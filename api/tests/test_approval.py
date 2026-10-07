import os
import sys
from pathlib import Path

os.environ['DATABASE_URL'] = 'sqlite:///' + str(Path(__file__).resolve().parent / 'test_devai.sqlite')
os.environ['ADMIN_API_KEY'] = 'test-secret'
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from main import app, Base, engine
import pytest

client = TestClient(app)
HEADERS = {'x-api-key': 'test-secret'}

@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield

def create_post():
    response = client.post('/posts', headers=HEADERS, json={'title': 'AI review', 'caption': 'First draft', 'slides': [{'headline': 'Slide one', 'body': 'Test'}]})
    assert response.status_code == 200
    return response.json()['id']

def test_authentication_required():
    assert client.get('/posts').status_code == 401
    assert client.post('/posts', json={'title': 'Unprotected'}).status_code == 401

def test_full_approval_and_invalidation():
    post_id = create_post()
    assert client.post(f'/posts/{post_id}/approve', headers=HEADERS).status_code == 409
    assert client.post(f'/posts/{post_id}/submit', headers=HEADERS).json()['status'] == 'pending_review'
    assert client.post(f'/posts/{post_id}/approve', headers=HEADERS).json()['status'] == 'approved'
    assert client.post(f'/posts/{post_id}/approve', headers=HEADERS).status_code == 409
    updated = client.patch(f'/posts/{post_id}', headers=HEADERS, json={'caption': 'Changed'}).json()
    assert updated == {'status': 'draft', 'version': '2'}
    assert client.post(f'/posts/{post_id}/approve', headers=HEADERS).status_code == 409
    assert len(client.get(f'/posts/{post_id}/audit', headers=HEADERS).json()) == 4

def test_reject_resubmit_and_missing_post():
    post_id = create_post()
    assert client.post(f'/posts/{post_id}/submit', headers=HEADERS).status_code == 200
    assert client.post(f'/posts/{post_id}/reject', headers=HEADERS).json()['status'] == 'rejected'
    assert client.post(f'/posts/{post_id}/submit', headers=HEADERS).json()['status'] == 'pending_review'
    assert client.patch('/posts/nonexistent', headers=HEADERS, json={'title':'x'}).status_code == 404
    assert client.post(f'/posts/{post_id}/publish', headers=HEADERS).status_code == 409

def test_slides_are_persisted_in_order():
    post_id = create_post()
    posts = client.get('/posts', headers=HEADERS).json()
    assert len(posts) == 1
    assert posts[0]['id'] == post_id
    assert posts[0]['slides'][0]['headline'] == 'Slide one'
    assert posts[0]['slides'][0]['position'] == 1

def test_edit_slide_invalidates_approval_and_export():
    import io,zipfile
    post_id=create_post()
    slide_id=client.get('/posts',headers=HEADERS).json()[0]['slides'][0]['id']
    assert client.post(f'/posts/{post_id}/submit',headers=HEADERS).status_code==200
    assert client.post(f'/posts/{post_id}/approve',headers=HEADERS).status_code==200
    r=client.patch(f'/posts/{post_id}/slides/{slide_id}',headers=HEADERS,json={'headline':'Edited slide'})
    assert r.json()=={'status':'draft','version':'2'}
    assert client.post(f'/posts/{post_id}/publish',headers=HEADERS).status_code==409
    r=client.get(f'/posts/{post_id}/export',headers=HEADERS)
    assert r.status_code==200
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        assert z.namelist()==['slide_01.png','caption.txt']
        from PIL import Image
        image=Image.open(io.BytesIO(z.read('slide_01.png')))
        assert image.size==(1080,1350)
    assert client.get(f'/posts/{post_id}/slides/{slide_id}/image',headers=HEADERS).status_code==200

def test_publishing_is_never_simulated_as_success():
    post_id=create_post()
    assert client.post(f'/posts/{post_id}/publish',headers=HEADERS).status_code==409
    client.post(f'/posts/{post_id}/submit',headers=HEADERS)
    client.post(f'/posts/{post_id}/approve',headers=HEADERS)
    assert client.post(f'/posts/{post_id}/publish',headers=HEADERS).status_code==503
