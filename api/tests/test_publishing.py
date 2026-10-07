"""Real route and worker, fake Meta transport, immutable managed JPEGs."""

import json

from devai.models import Job, MediaAsset, Post, PublishAttempt
from devai.services import managed_publishing
from devai.services.jobs import work_once

HEADERS = {"x-api-key": "test-secret"}


def approve(client, post_id):
    client.post(f"/posts/{post_id}/submit", headers=HEADERS)
    assert client.post(f"/posts/{post_id}/approve", headers=HEADERS).status_code == 200


def configure(monkeypatch, tmp_path, callback):
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "fake-token")
    monkeypatch.setenv("INSTAGRAM_ACCOUNT_ID", "fake-account")
    monkeypatch.setenv("PUBLIC_MEDIA_BASE_URL", "https://media.example.com")
    monkeypatch.setenv("PUBLISH_MEDIA_DIR", str(tmp_path / "published"))

    class FakePublisher:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def publish_carousel(self, urls, caption):
            return callback(urls, caption)

    monkeypatch.setattr(managed_publishing, "InstagramPublisher", FakePublisher)


def test_publish_reserves_version_and_serves_only_bound_media(
    client, ready_post, monkeypatch, tmp_path
):
    post_id = ready_post()
    approve(client, post_id)
    calls = []

    def publish(urls, caption):
        calls.append(urls)
        assert len(urls) == 6 and all(
            url.startswith("https://media.example.com/media/") for url in urls
        )
        assert (
            client.patch(
                f"/posts/{post_id}", headers=HEADERS, json={"title": "Late edit"}
            ).status_code
            == 409
        )
        assert client.post(f"/posts/{post_id}/publish", headers=HEADERS).status_code == 409
        for url in urls:
            response = client.get("/media/" + url.rsplit("/", 1)[1])
            assert response.status_code == 200 and response.headers["content-type"] == "image/jpeg"
            assert response.content.startswith(b"\xff\xd8")
        return "media-123"

    configure(monkeypatch, tmp_path, publish)
    queued = client.post(f"/posts/{post_id}/publish", headers=HEADERS)
    assert queued.status_code == 202
    assert client.post(f"/posts/{post_id}/publish", headers=HEADERS).status_code == 409
    assert work_once(client.app.state.session_factory)
    with client.app.state.session_factory() as db:
        assert db.get(Post, post_id).status == "published"
        assert db.get(Job, queued.json()["id"]).status == "completed"
        attempt = db.query(PublishAttempt).one()
        assert (attempt.version, attempt.status, attempt.external_id) == (
            "1",
            "published",
            "media-123",
        )
        assert db.query(MediaAsset).count() == 6
    assert len(calls) == 1


def test_uncertain_publish_never_retries_and_requires_human_reconciliation(
    client, ready_post, monkeypatch, tmp_path
):
    post_id = ready_post()
    approve(client, post_id)
    calls = []

    def fail(urls, caption):
        calls.append(urls)
        raise RuntimeError("contains fake-token")

    configure(monkeypatch, tmp_path, fail)
    job_id = client.post(f"/posts/{post_id}/publish", headers=HEADERS).json()["id"]
    work_once(client.app.state.session_factory)
    job = client.get(f"/jobs/{job_id}", headers=HEADERS).json()
    assert job["status"] == "needs_reconciliation" and "fake-token" not in json.dumps(job)
    assert client.post(f"/jobs/{job_id}/retry", headers=HEADERS).status_code == 409
    assert client.post(f"/posts/{post_id}/publish", headers=HEADERS).status_code == 409
    assert len(calls) == 1
    assert (
        client.post(
            f"/posts/{post_id}/reconcile",
            headers=HEADERS,
            json={"published": False, "note": "Checked Meta and account: no publication."},
        ).json()["status"]
        == "draft"
    )
    assert client.post(f"/posts/{post_id}/publish", headers=HEADERS).status_code == 409


def test_external_images_cannot_replace_approved_artwork(client, ready_post, monkeypatch, tmp_path):
    post_id = ready_post()
    approve(client, post_id)
    configure(monkeypatch, tmp_path, lambda *_: "never")
    response = client.post(
        f"/posts/{post_id}/publish",
        headers=HEADERS,
        json={"image_urls": ["https://example.com/unrelated.jpg"] * 6},
    )
    assert response.status_code == 422
    assert client.get(f"/posts/{post_id}", headers=HEADERS).json()["status"] == "approved"


def test_media_integrity_and_authentication(client):
    assert client.get("/media/no-token.jpg").status_code == 404
    assert client.post("/posts/any/publish").status_code == 401
