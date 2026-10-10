"""Account preferences use real persisted revisions, never overwrite concurrent changes."""

from datetime import UTC, datetime, timedelta

from devai.core.auth import token_hash
from devai.models import AuthSession, User


def account(client, identifier="profile-user"):
    with client.app.state.session_factory.begin() as db:
        db.add(
            User(
                id=identifier,
                email=f"{identifier}@example.test",
                password_hash="unused",
                role="viewer",
            )
        )
        db.flush()
        db.add(
            AuthSession(
                token_hash=token_hash(identifier),
                user_id=identifier,
                expires_at=datetime.now(UTC) + timedelta(hours=1),
            )
        )
    return {"Authorization": f"Bearer {identifier}", "Idempotency-Key": "profile-action"}


def test_profile_idempotency_conflicts_and_identity_isolation(client):
    headers = account(client)
    other = account(client, "other-profile")
    assert client.get("/v1/me", headers=headers).json()["revision"] == 1
    data = {"displayName": "  Engineer  ", "timeZone": "Asia/Kolkata", "expectedRevision": 1}
    first = client.patch("/v1/me", headers=headers, json=data)
    assert first.status_code == 200, first.text
    assert first.json()["displayName"] == "Engineer"
    assert first.json()["revision"] == 2
    assert client.patch("/v1/me", headers=headers, json=data).json() == first.json()
    assert (
        client.patch("/v1/me", headers=headers, json={**data, "displayName": "Changed"}).status_code
        == 409
    )
    conflict = client.patch(
        "/v1/me",
        headers={**headers, "Idempotency-Key": "new-action"},
        json={**data, "displayName": "Mine"},
    )
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["server"]["displayName"] == "Engineer"
    assert client.get("/v1/me", headers=headers).json()["displayName"] == "Engineer"
    assert client.get("/v1/me", headers=other).json()["displayName"] == ""
    for changes in [
        {"timeZone": "invalid-zone"},
        {"locale": "fr"},
        {"displayName": "  "},
        {"userId": "other-profile"},
    ]:
        assert client.patch("/v1/me", headers=headers, json={**data, **changes}).status_code == 422
