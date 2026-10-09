import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest

from devai.core.auth import password_hash
from devai.models import AuthSession, User
from devai.services import operations
from devai.services.usage import usage_scope

HEADERS = {"X-API-Key": "test-secret"}
PASSWORD = "Testing-password-12345"


def account(client, role="admin", email="owner@example.test"):
    with client.app.state.session_factory.begin() as db:
        db.add(
            User(
                id=str(uuid.uuid4()), email=email, password_hash=password_hash(PASSWORD), role=role
            )
        )
    return client.post("/auth/login", json={"email": email, "password": PASSWORD})


def test_login_logout_and_cookie_origin_enforcement(client, monkeypatch):
    monkeypatch.setenv("ALLOW_DEV_API_KEY", "false")
    response = account(client)
    assert response.status_code == 200
    assert "HttpOnly" in response.headers["set-cookie"]
    assert client.get("/auth/me").json()["role"] == "admin"
    assert client.post("/research/refresh").status_code == 403
    token = response.json()["token"]
    assert client.get("/posts", headers={"Authorization": "Bearer " + token}).status_code == 200
    assert (
        client.post("/auth/logout", headers={"Origin": "http://localhost:5173"}).status_code == 200
    )
    assert client.get("/posts", headers={"Authorization": "Bearer " + token}).status_code == 401


@pytest.mark.parametrize(
    "role,path",
    [
        ("viewer", "/research/refresh"),
        ("editor", "/posts/missing/approve"),
        ("editor", "/auth/users"),
        ("reviewer", "/auth/users"),
    ],
)
def test_roles_prevent_unauthorized_mutations(client, role, path):
    response = account(client, role)
    assert (
        client.post(
            path, headers={"Authorization": "Bearer " + response.json()["token"]}, json={}
        ).status_code
        == 403
    )


def test_password_bruteforce_is_durably_limited(client):
    for _ in range(5):
        assert (
            client.post(
                "/auth/login", json={"email": "unknown@example.test", "password": "bad"}
            ).status_code
            == 401
        )
    assert (
        client.post(
            "/auth/login", json={"email": "unknown@example.test", "password": "bad"}
        ).status_code
        == 429
    )


def test_session_expiration_and_disabled_account(client):
    response = account(client)
    token = response.json()["token"]
    with client.app.state.session_factory.begin() as db:
        for row in db.query(AuthSession):
            row.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    assert client.get("/posts", headers={"Authorization": "Bearer " + token}).status_code == 401


def test_topic_approval_is_bound_to_evidence_and_category(client):
    topic = client.post(
        "/topics",
        headers=HEADERS,
        json={
            "title": "A real developer source",
            "url": "https://example.com/topic",
            "excerpt": "Source evidence. " * 30,
        },
    ).json()
    assert client.post(f"/topics/{topic['id']}/approve", headers=HEADERS).status_code == 409
    client.post(f"/topics/{topic['id']}/verify", headers=HEADERS)
    assert (
        client.post(f"/topics/{topic['id']}/generate", headers=HEADERS, json={}).status_code == 409
    )
    assert client.post(f"/topics/{topic['id']}/approve", headers=HEADERS).status_code == 200
    assert client.get("/topics", headers=HEADERS).json()[0]["approved"]
    client.patch(f"/topics/{topic['id']}", headers=HEADERS, json={"category": "architecture"})
    assert not client.get("/topics", headers=HEADERS).json()[0]["approved"]


def test_version_restore_preserves_history_and_invalidates_approval(client):
    post = client.post(
        "/posts",
        headers=HEADERS,
        json={
            "title": "Original title",
            "caption": "Original copy",
            "slides": [{"headline": "Original slide", "body": "Original explanation."}],
        },
    ).json()["id"]
    client.patch(f"/posts/{post}", headers=HEADERS, json={"title": "Edited title"})
    history = client.get(f"/posts/{post}/versions", headers=HEADERS).json()
    old = next(r for r in history if r["version"] == "1")
    assert old["snapshot"]["title"] == "Original title"
    assert (
        client.post(f"/posts/{post}/versions/{old['id']}/restore", headers=HEADERS).status_code
        == 200
    )
    restored = client.get(f"/posts/{post}", headers=HEADERS).json()
    assert (
        restored["title"] == "Original title"
        and restored["status"] == "draft"
        and restored["version"] == "3"
    )


def test_schedule_is_approval_gated_and_dispatch_deduplicated(client, ready_post, monkeypatch):
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "test-token")
    monkeypatch.setenv("INSTAGRAM_ACCOUNT_ID", "test-account")
    monkeypatch.setenv("PUBLIC_MEDIA_BASE_URL", "https://example.com")
    post = ready_post()
    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    assert (
        client.post(f"/posts/{post}/schedule", headers=HEADERS, json={"due_at": future}).status_code
        == 409
    )
    client.post(f"/posts/{post}/submit", headers=HEADERS)
    client.post(f"/posts/{post}/approve", headers=HEADERS)
    row = client.post(f"/posts/{post}/schedule", headers=HEADERS, json={"due_at": future})
    assert row.status_code == 201
    assert (
        client.post(f"/posts/{post}/schedule", headers=HEADERS, json={"due_at": future}).status_code
        == 409
    )
    operations.dispatch_schedules(
        client.app.state.session_factory, datetime.now(UTC) + timedelta(hours=2)
    )
    operations.dispatch_schedules(
        client.app.state.session_factory, datetime.now(UTC) + timedelta(hours=2)
    )
    assert (
        len([j for j in client.get("/jobs", headers=HEADERS).json() if j["kind"] == "publish"]) == 1
    )


def test_scheduled_version_is_cancelled_when_copy_changes(client, ready_post, monkeypatch):
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "test-token")
    monkeypatch.setenv("INSTAGRAM_ACCOUNT_ID", "test-account")
    monkeypatch.setenv("PUBLIC_MEDIA_BASE_URL", "https://example.com")
    post = ready_post()
    client.post(f"/posts/{post}/submit", headers=HEADERS)
    client.post(f"/posts/{post}/approve", headers=HEADERS)
    client.post(
        f"/posts/{post}/schedule",
        headers=HEADERS,
        json={"due_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat()},
    )
    client.patch(f"/posts/{post}", headers=HEADERS, json={"caption": "Changed copy"})
    operations.dispatch_schedules(
        client.app.state.session_factory, datetime.now(UTC) + timedelta(hours=2)
    )
    assert client.get("/publishing/schedules", headers=HEADERS).json()[0]["status"] == "cancelled"
    assert not client.get("/jobs", headers=HEADERS).json()


def test_cost_tracking_records_usage_without_inventing_unconfigured_prices(client, monkeypatch):
    from devai.services.usage import record_usage

    monkeypatch.setenv(
        "PROVIDER_PRICE_RATES_JSON",
        json.dumps({"test-model": {"input_per_million": 2, "output_per_million": 4}}),
    )
    with usage_scope(client.app.state.session_factory, "test-job"):
        record_usage(
            "chat/completions",
            "test-model",
            {"usage": {"prompt_tokens": 1000, "completion_tokens": 500}},
            100,
        )
        record_usage("images/generations", "unknown", {"data": [{}]}, 200)
    data = client.get("/ops/summary", headers=HEADERS).json()
    assert data["estimated_cost_usd"] == pytest.approx(0.004)
    assert data["unpriced_calls"] == 1
    assert data["usage"][0]["images"] == 1


def test_daily_settings_validate_and_persist(client):
    settings = {
        "daily_enabled": True,
        "daily_hour": 8,
        "timezone": "America/Chicago",
        "daily_generate_carousel": False,
    }
    assert client.patch("/ops/settings", headers=HEADERS, json=settings).status_code == 200
    assert client.get("/ops/summary", headers=HEADERS).json()["settings"] == settings
    assert (
        client.patch(
            "/ops/settings", headers=HEADERS, json={**settings, "timezone": "invalid-zone"}
        ).status_code
        == 422
    )


def test_edited_caption_requires_new_grounding_even_when_images_are_current(client, ready_post):
    post = ready_post()
    client.patch(
        f"/posts/{post}",
        headers=HEADERS,
        json={"caption": "Unverified claim. Source: https://example.com"},
    )
    client.post(f"/posts/{post}/submit", headers=HEADERS)
    response = client.post(f"/posts/{post}/approve", headers=HEADERS)
    assert response.status_code == 409 and "grounding" in response.json()["detail"]
