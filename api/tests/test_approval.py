import io
import zipfile

from PIL import Image

HEADERS = {"x-api-key": "test-secret"}


def test_authentication_required(client):
    assert client.get("/posts").status_code == 401
    assert client.post("/posts", json={"title": "Unprotected"}).status_code == 401


def test_full_approval_and_invalidation(client, ready_post):
    post_id = ready_post()
    assert client.post(f"/posts/{post_id}/approve", headers=HEADERS).status_code == 409
    assert (
        client.post(f"/posts/{post_id}/submit", headers=HEADERS).json()["status"]
        == "pending_review"
    )
    assert client.post(f"/posts/{post_id}/approve", headers=HEADERS).json()["status"] == "approved"
    assert client.post(f"/posts/{post_id}/approve", headers=HEADERS).status_code == 409
    updated = client.patch(f"/posts/{post_id}", headers=HEADERS, json={"caption": "Changed"}).json()
    assert updated == {"status": "draft", "version": "2"}
    assert client.post(f"/posts/{post_id}/approve", headers=HEADERS).status_code == 409
    assert len(client.get(f"/posts/{post_id}/audit", headers=HEADERS).json()) == 4


def test_missing_images_or_citations_block_approval(client, ready_post):
    post_id = ready_post()
    client.patch(f"/posts/{post_id}", headers=HEADERS, json={"caption": "No citation"})
    client.post(f"/posts/{post_id}/submit", headers=HEADERS)
    assert client.post(f"/posts/{post_id}/approve", headers=HEADERS).status_code == 409
    bare = client.post(
        "/posts", headers=HEADERS, json={"title": "Bare scaffold", "slides": [{"headline": "One"}]}
    ).json()["id"]
    client.post(f"/posts/{bare}/submit", headers=HEADERS)
    assert client.post(f"/posts/{bare}/approve", headers=HEADERS).status_code == 409


def test_reject_resubmit_and_missing_post(client, ready_post):
    post_id = ready_post()
    assert client.post(f"/posts/{post_id}/submit", headers=HEADERS).status_code == 200
    assert client.post(f"/posts/{post_id}/reject", headers=HEADERS).json()["status"] == "rejected"
    assert (
        client.post(f"/posts/{post_id}/submit", headers=HEADERS).json()["status"]
        == "pending_review"
    )
    assert (
        client.patch("/posts/nonexistent", headers=HEADERS, json={"title": "x"}).status_code == 404
    )
    assert client.post(f"/posts/{post_id}/publish", headers=HEADERS).status_code == 409


def test_edit_slide_invalidates_artwork_and_export(client, ready_post):
    post_id = ready_post()
    slide = client.get(f"/posts/{post_id}", headers=HEADERS).json()["slides"][0]
    client.post(f"/posts/{post_id}/submit", headers=HEADERS)
    client.post(f"/posts/{post_id}/approve", headers=HEADERS)
    response = client.patch(
        f"/posts/{post_id}/slides/{slide['id']}", headers=HEADERS, json={"headline": "Edited slide"}
    )
    assert response.json() == {"status": "draft", "version": "2"}
    assert client.get(f"/posts/{post_id}/export", headers=HEADERS).status_code == 409
    assert client.post(f"/posts/{post_id}/publish", headers=HEADERS).status_code == 409
    assert (
        client.get(f"/posts/{post_id}", headers=HEADERS).json()["slides"][0]["artwork_current"]
        is False
    )


def test_export_preserves_complete_images_and_sources(client, ready_post):
    post_id = ready_post()
    response = client.get(f"/posts/{post_id}/export", headers=HEADERS)
    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert {"caption.txt", "sources.json", "review.json", "slide_06.png"} <= set(
            archive.namelist()
        )
        assert Image.open(io.BytesIO(archive.read("slide_01.png"))).size == (1080, 1350)
    assert (
        client.get(
            f"/posts/{post_id}/slides/{client.get(f'/posts/{post_id}', headers=HEADERS).json()['slides'][0]['id']}/image",
            headers=HEADERS,
        ).status_code
        == 200
    )


def test_publishing_is_never_simulated_as_success(client, ready_post):
    post_id = ready_post()
    assert client.post(f"/posts/{post_id}/publish", headers=HEADERS).status_code == 409
    client.post(f"/posts/{post_id}/submit", headers=HEADERS)
    client.post(f"/posts/{post_id}/approve", headers=HEADERS)
    assert client.post(f"/posts/{post_id}/publish", headers=HEADERS).status_code == 503
