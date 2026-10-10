"""Real email-code authentication with persistent abuse controls and personal studios."""

import hashlib
import hmac
import json
import os
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Header, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import func, text

from devai.core.auth import password_hash, token_hash
from devai.models import AuthSession, EmailChallenge, User
from devai.models.studio import Membership, Workspace
from devai.services import email_delivery
from devai.services.research_runs import aware

router = APIRouter(prefix="/v1/auth")


class ChallengeInput(BaseModel):
    email: str = Field(min_length=3, max_length=254, pattern=r"^[^\s@<>:]+@[^\s@<>:]+\.[^\s@<>:]+$")
    replaceChallengeId: str | None = None


class VerifyInput(BaseModel):
    challengeId: str = Field(max_length=64)
    code: str = Field(pattern=r"^\d{6}$")


def code_hash(identifier, code):
    secret = os.getenv("APP_SECRET", "")
    if len(secret) < 32:
        raise HTTPException(
            503, "Email sign-in is unavailable; configure APP_SECRET and SMTP on the server"
        )
    return hmac.new(secret.encode(), f"{identifier}:{code}".encode(), hashlib.sha256).hexdigest()


def check_origin(request):
    origin = request.headers.get("origin")
    if origin and origin not in request.app.state.settings.cors_origins:
        raise HTTPException(403, "Invalid request origin")


@router.get("/capabilities")
def capabilities():
    return {
        "emailConfigured": email_delivery.mail_configured(),
        "passwordLoginAvailable": bool(os.getenv("ADMIN_EMAIL")),
        "appleConfigured": False,
    }


@router.post("/email/challenges", status_code=202)
def challenge(
    data: ChallengeInput,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key", max_length=200),
):
    check_origin(request)
    if not email_delivery.mail_configured():
        raise HTTPException(
            503,
            "Email sign-in is unavailable; configure SMTP and APP_SECRET on the server. Existing local accounts can still use password sign-in.",
        )
    email = data.email.lower().strip()
    address = token_hash(request.client.host if request.client else "unknown")
    now = datetime.now(UTC)
    identifier, code = str(uuid.uuid4()), f"{secrets.randbelow(1_000_000):06}"
    factory = request.app.state.session_factory
    action = token_hash(idempotency_key) if idempotency_key else None
    digest = token_hash(json.dumps({**data.model_dump(), "email": email}, sort_keys=True))
    with factory.begin() as db:
        if db.bind.dialect.name == "postgresql":
            for identity in sorted({email, address, action or email}):
                lock = int.from_bytes(
                    hashlib.sha256(identity.encode()).digest()[:8], "big", signed=True
                )
                db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock})
        replay = db.query(EmailChallenge).filter_by(action_hash=action).first() if action else None
        if replay:
            if replay.request_hash != digest:
                raise HTTPException(409, {"code": "IDEMPOTENCY_MISMATCH"})
            if replay.delivery_status == "failed":
                raise HTTPException(
                    503,
                    "The email could not be delivered. Request a new code after the resend interval.",
                )
            return {
                "challengeId": replay.id,
                "expiresAt": aware(replay.expires_at),
                "resendAfter": aware(replay.created_at) + timedelta(seconds=30),
                "deliveryStatus": replay.delivery_status,
                "message": "Check your email for a sign-in code",
            }
        recent = (
            db.query(EmailChallenge)
            .filter_by(email=email)
            .order_by(EmailChallenge.created_at.desc())
            .first()
        )
        if recent and aware(recent.created_at) > now - timedelta(seconds=30):
            wait = max(1, 30 - int((now - aware(recent.created_at)).total_seconds()))
            raise HTTPException(
                429,
                {"message": "Wait before requesting another code", "retryAfter": wait},
                headers={"Retry-After": str(wait)},
            )
        for condition, limit in [
            (EmailChallenge.email == email, 5),
            (EmailChallenge.address_hash == address, 30),
        ]:
            count = (
                db.query(func.count(EmailChallenge.id))
                .filter(condition, EmailChallenge.created_at > now - timedelta(minutes=15))
                .scalar()
            )
            if count >= limit:
                raise HTTPException(
                    429,
                    "Too many code requests; retry in 15 minutes",
                    headers={"Retry-After": "900"},
                )
        db.query(EmailChallenge).filter_by(email=email, consumed=False).update({"consumed": True})
        db.add(
            EmailChallenge(
                id=identifier,
                email=email,
                address_hash=address,
                code_hash=code_hash(identifier, code),
                action_hash=action,
                request_hash=digest,
                expires_at=now + timedelta(minutes=10),
                created_at=now,
            )
        )
    try:
        email_delivery.deliver_code(email, code)
    except Exception:
        with factory.begin() as db:
            saved = db.get(EmailChallenge, identifier)
            saved.consumed, saved.delivery_status = True, "failed"
        raise HTTPException(
            503,
            "The email could not be delivered. Retry later or contact your studio administrator.",
        ) from None
    with factory.begin() as db:
        db.get(EmailChallenge, identifier).delivery_status = "sent"
    return {
        "challengeId": identifier,
        "expiresAt": now + timedelta(minutes=10),
        "resendAfter": now + timedelta(seconds=30),
        "message": "Check your email for a sign-in code",
        "deliveryStatus": "sent",
    }


@router.post("/email/verify")
def verify(data: VerifyInput, request: Request, response: Response):
    check_origin(request)
    now = datetime.now(UTC)
    principal, failure, token, workspace_ids = None, None, None, []
    with request.app.state.session_factory.begin() as db:
        challenge = (
            db.query(EmailChallenge).filter_by(id=data.challengeId).with_for_update().first()
        )
        if (
            not challenge
            or challenge.consumed
            or aware(challenge.expires_at) <= now
            or challenge.attempts >= 5
        ):
            failure = "This code expired or is unavailable. Request a new code."
        elif not secrets.compare_digest(challenge.code_hash, code_hash(challenge.id, data.code)):
            challenge.attempts += 1
            failure = "The code is incorrect. Check your email and try again."
        else:
            challenge.consumed = True
            user = db.query(User).filter_by(email=challenge.email).first()
            if user and not user.active:
                failure = "Sign-in is unavailable for this account. Contact your administrator."
            else:
                if not user:
                    user = User(
                        id=str(uuid.uuid4()),
                        email=challenge.email,
                        password_hash=password_hash(secrets.token_urlsafe(48)),
                        role="editor",
                    )
                    db.add(user)
                    db.flush()
                memberships = db.query(Membership).filter_by(user_id=user.id).all()
                if not memberships:
                    workspace = Workspace(
                        id=str(uuid.uuid4()),
                        name="Personal studio",
                        settings_json=json.dumps(
                            {
                                "timezone": "America/Chicago",
                                "daily_hour": 8,
                                "daily_enabled": False,
                                "auto_draft": False,
                                "onboarding_complete": False,
                            }
                        ),
                    )
                    db.add(workspace)
                    db.flush()
                    membership = Membership(
                        workspace_id=workspace.id,
                        user_id=user.id,
                        role="owner",
                        publish_permission=1,
                    )
                    db.add(membership)
                    memberships = [membership]
                token = secrets.token_urlsafe(32)
                db.add(
                    AuthSession(
                        token_hash=token_hash(token),
                        user_id=user.id,
                        expires_at=now + timedelta(hours=12),
                    )
                )
                principal = {"id": user.id, "email": user.email, "role": user.role}
                workspace_ids = [item.workspace_id for item in memberships]
    # Raise after commit: failed-code attempts and one-use consumption must persist.
    if failure:
        raise HTTPException(401, failure)
    response.set_cookie(
        "devai_session",
        token,
        httponly=True,
        secure=os.getenv("COOKIE_SECURE", "false") == "true",
        samesite="strict",
        max_age=43200,
        path="/",
    )
    response.headers["Cache-Control"] = "no-store"
    return {
        "user": principal,
        "token": token,
        "workspaceIds": workspace_ids,
        "expires_at": (now + timedelta(hours=12)).isoformat(),
    }
