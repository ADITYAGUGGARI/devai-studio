"""Isolated mail fixture verifies real persistence and challenge security behavior."""

from datetime import UTC, datetime, timedelta

from devai.models import EmailChallenge, User
from devai.models.studio import Membership
from devai.services import email_delivery


def test_idempotent_code_delivery_is_not_repeated(client, monkeypatch):
    delivered = configured(monkeypatch)
    headers = {"Idempotency-Key": "isolated-mail-action"}
    data = {"email": "retry@example.test"}
    first = client.post("/v1/auth/email/challenges", headers=headers, json=data)
    second = client.post("/v1/auth/email/challenges", headers=headers, json=data)
    assert first.status_code == second.status_code == 202
    assert first.json() == second.json()
    assert len(delivered) == 1
    assert (
        client.post(
            "/v1/auth/email/challenges", headers=headers, json={"email": "different@example.test"}
        ).status_code
        == 409
    )


def configured(monkeypatch):
    delivered = []
    monkeypatch.setenv("APP_SECRET", "isolated-email-test-secret-with-more-than-32-characters")
    monkeypatch.setattr(email_delivery, "mail_configured", lambda: True)
    monkeypatch.setattr(
        email_delivery, "deliver_code", lambda email, code: delivered.append((email, code))
    )
    return delivered


def test_signup_one_use_code_and_private_workspace(client, monkeypatch):
    delivered = configured(monkeypatch)
    challenge = client.post("/v1/auth/email/challenges", json={"email": "new@example.test"})
    assert challenge.status_code == 202
    identifier = challenge.json()["challengeId"]
    code = delivered[0][1]
    assert code not in challenge.text
    with client.app.state.session_factory() as db:
        saved = db.get(EmailChallenge, identifier)
        assert saved.code_hash != code
    result = client.post("/v1/auth/email/verify", json={"challengeId": identifier, "code": code})
    assert result.status_code == 200
    token = result.json()["token"]
    workspace = result.json()["workspaceIds"][0]
    with client.app.state.session_factory() as db:
        member = db.query(Membership).filter_by(workspace_id=workspace).one()
        assert member.role == "owner"
        assert member.publish_permission == 1
        assert db.query(User).filter_by(email="new@example.test").one().role == "editor"
    headers = {"Authorization": f"Bearer {token}", "X-Workspace-ID": workspace}
    assert client.get("/auth/me", headers=headers).status_code == 200
    assert client.get("/topics", headers=headers).json() == []
    assert (
        client.get("/topics", headers={**headers, "X-Workspace-ID": "another-studio"}).status_code
        == 404
    )
    assert (
        client.post(
            "/v1/auth/email/verify", json={"challengeId": identifier, "code": code}
        ).status_code
        == 401
    )


def test_failed_attempts_commit_and_resend_is_limited(client, monkeypatch):
    delivered = configured(monkeypatch)
    challenge = client.post("/v1/auth/email/challenges", json={"email": "test@example.test"}).json()
    identifier = challenge["challengeId"]
    assert (
        client.post("/v1/auth/email/challenges", json={"email": "test@example.test"}).status_code
        == 429
    )
    wrong = "999999" if delivered[0][1] != "999999" else "000000"
    for _ in range(5):
        assert (
            client.post(
                "/v1/auth/email/verify", json={"challengeId": identifier, "code": wrong}
            ).status_code
            == 401
        )
    with client.app.state.session_factory() as db:
        assert db.get(EmailChallenge, identifier).attempts == 5
    assert (
        client.post(
            "/v1/auth/email/verify", json={"challengeId": identifier, "code": delivered[0][1]}
        ).status_code
        == 401
    )


def test_expired_and_failed_delivery_never_authenticate(client, monkeypatch):
    delivered = configured(monkeypatch)
    challenge = client.post("/v1/auth/email/challenges", json={"email": "old@example.test"}).json()
    with client.app.state.session_factory.begin() as db:
        db.get(EmailChallenge, challenge["challengeId"]).expires_at = datetime.now(UTC) - timedelta(
            seconds=1
        )
    assert (
        client.post(
            "/v1/auth/email/verify",
            json={"challengeId": challenge["challengeId"], "code": delivered[0][1]},
        ).status_code
        == 401
    )

    def unavailable(*args):
        raise RuntimeError("test SMTP unavailable")

    monkeypatch.setattr(email_delivery, "deliver_code", unavailable)
    assert (
        client.post("/v1/auth/email/challenges", json={"email": "failed@example.test"}).status_code
        == 503
    )
    with client.app.state.session_factory() as db:
        assert db.query(EmailChallenge).filter_by(email="failed@example.test").one().consumed
