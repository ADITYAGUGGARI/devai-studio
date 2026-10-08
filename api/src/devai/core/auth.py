"""Session authentication and workspace role authorization."""

import hashlib
import os
import secrets
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Header, HTTPException, Request

from devai.models import AuthSession, User


def password_hash(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex()
    return f"scrypt${salt}${digest}"


def password_matches(password: str, encoded: str) -> bool:
    try:
        algorithm, salt, expected = encoded.split("$")
        if algorithm != "scrypt":
            return False
        digest = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex()
        return secrets.compare_digest(digest, expected)
    except (ValueError, TypeError):
        return False


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def authorize(request: Request, principal: dict) -> dict:
    method, path, role = request.method, request.url.path, principal["role"]
    if method not in {"GET", "HEAD", "OPTIONS"}:
        if role == "viewer":
            raise HTTPException(403, "Viewer access is read-only")
        if path.startswith("/auth/users") or path == "/ops/settings":
            if role != "admin":
                raise HTTPException(403, "Administrator role required")
        elif path.endswith(
            ("/approve", "/reject", "/publish", "/reconcile", "/schedule")
        ) or path.startswith("/publishing/schedules/"):
            if role not in {"admin", "reviewer"}:
                raise HTTPException(403, "Reviewer role required")
    request.state.principal = principal
    return principal


def require_api_key(request: Request, x_api_key: Annotated[str | None, Header()] = None):
    # Compatibility for isolated tests/local scripts. Disabled in account deployments.
    expected = request.app.state.settings.admin_api_key
    if (
        os.getenv("ALLOW_DEV_API_KEY", "true").lower() == "true"
        and x_api_key
        and secrets.compare_digest(x_api_key.encode(), expected.encode())
    ):
        return authorize(request, {"id": "development", "email": "development", "role": "admin"})
    authorization = request.headers.get("authorization", "")
    bearer = authorization[7:] if authorization.startswith("Bearer ") else None
    token = bearer or request.cookies.get("devai_session")
    if not token:
        raise HTTPException(401, "Sign in required")
    if not bearer and request.method not in {"GET", "HEAD", "OPTIONS"}:
        if request.headers.get("origin") not in request.app.state.settings.cors_origins:
            raise HTTPException(403, "Invalid request origin")
    with request.app.state.session_factory() as db:
        session = db.get(AuthSession, token_hash(token))
        if not session:
            raise HTTPException(401, "Session expired; sign in again")
        expires = (
            session.expires_at.replace(tzinfo=UTC)
            if session.expires_at.tzinfo is None
            else session.expires_at
        )
        user = db.get(User, session.user_id)
        if expires <= datetime.now(UTC) or not user or not user.active:
            raise HTTPException(401, "Session expired; sign in again")
        return authorize(request, {"id": user.id, "email": user.email, "role": user.role})
