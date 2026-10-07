"""Exercise the real publish route with a fake adapter; never contact Meta."""

from devai.models import PublishAttempt
from devai.routes import publishing

HEADERS = {"x-api-key": "test-secret"}
IMAGES = ["https://example.com/one.jpg", "https://example.com/two.jpg"]


def approved_post(client):
    response = client.post(
        "/posts",
        headers=HEADERS,
        json={
            "title": "Review this carousel",
            "slides": [{"headline": "One"}, {"headline": "Two"}],
        },
    )
    post_id = response.json()["id"]
    client.post(f"/posts/{post_id}/submit", headers=HEADERS)
    client.post(f"/posts/{post_id}/approve", headers=HEADERS)
    return post_id


def configure_publisher(monkeypatch, callback):
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "fake-token")
    monkeypatch.setenv("INSTAGRAM_ACCOUNT_ID", "fake-account")

    class FakePublisher:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def publish_carousel(self, urls, caption):
            return callback(urls, caption)

    monkeypatch.setattr(publishing, "InstagramPublisher", FakePublisher)


def test_publish_route_is_reachable_and_reserves_before_network(client, monkeypatch):
    post_id = approved_post(client)
    calls = []

    def publish(urls, caption):
        calls.append(urls)
        # Simulate a second request arriving during the external operation.
        assert (
            client.post(
                f"/posts/{post_id}/publish", headers=HEADERS, json={"image_urls": IMAGES}
            ).status_code
            == 409
        )
        assert (
            client.patch(
                f"/posts/{post_id}", headers=HEADERS, json={"title": "Late edit"}
            ).status_code
            == 409
        )
        return "media-123"

    configure_publisher(monkeypatch, publish)
    response = client.post(
        f"/posts/{post_id}/publish", headers=HEADERS, json={"image_urls": IMAGES}
    )
    assert response.json() == {"status": "published", "instagram_media_id": "media-123"}
    assert calls == [IMAGES]
    with client.app.state.session_factory() as db:
        attempt = db.query(PublishAttempt).one()
        assert attempt.status == "published"
        assert attempt.version == "1"
        assert attempt.external_id == "media-123"


def test_uncertain_publish_requires_reconciliation_and_does_not_retry(client, monkeypatch):
    post_id = approved_post(client)
    calls = []

    def fail(urls, caption):
        calls.append(urls)
        raise RuntimeError("Failure containing fake-token")

    configure_publisher(monkeypatch, fail)
    response = client.post(
        f"/posts/{post_id}/publish", headers=HEADERS, json={"image_urls": IMAGES}
    )
    assert response.status_code == 502
    assert "fake-token" not in response.text
    assert (
        client.post(
            f"/posts/{post_id}/publish", headers=HEADERS, json={"image_urls": IMAGES}
        ).status_code
        == 409
    )
    assert len(calls) == 1
    with client.app.state.session_factory() as db:
        attempt = db.query(PublishAttempt).one()
        assert attempt.status == "needs_reconciliation"
        assert attempt.error == "RuntimeError"


def test_image_count_must_match_approved_slides(client, monkeypatch):
    post_id = approved_post(client)

    def unexpected_network(*args):
        raise AssertionError("Invalid input must not reach the publisher")

    configure_publisher(monkeypatch, unexpected_network)
    response = client.post(
        f"/posts/{post_id}/publish", headers=HEADERS, json={"image_urls": IMAGES + [IMAGES[0]]}
    )
    assert response.status_code == 422
    assert client.get("/posts", headers=HEADERS).json()[0]["status"] == "approved"


def test_publish_requires_authentication(client):
    assert client.post("/posts/any/publish", json={"image_urls": IMAGES}).status_code == 401
