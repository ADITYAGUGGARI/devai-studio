"""Local workspace accounts; only administrators create accounts."""

import os
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from devai.core.auth import password_hash, password_matches, require_api_key, token_hash
from devai.core.database import SessionFactory
from devai.models import AuthSession, LoginAttempt, User

router = APIRouter(prefix="/auth")


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)


class NewUser(Credentials):
    password: str = Field(min_length=12, max_length=256)
    role: Literal["admin", "reviewer", "editor", "viewer"] = "editor"


def bootstrap_admin(factory):
    email, password = os.getenv("ADMIN_EMAIL"), os.getenv("ADMIN_PASSWORD")
    if not email or not password:
        return
    if len(password) < 12:
        raise ValueError("ADMIN_PASSWORD must contain at least 12 characters")
    with factory.begin() as db:
        if not db.query(User).first():
            db.add(
                User(
                    id=str(uuid.uuid4()),
                    email=email.strip().lower(),
                    password_hash=password_hash(password),
                    role="admin",
                )
            )


@router.post("/login")
def login(data: Credentials, request: Request, response: Response, session_factory: SessionFactory):
    email = data.email.strip().lower()
    now = datetime.now(UTC)
    identity = token_hash(email)
    address = token_hash("ip:" + (request.client.host if request.client else "unknown"))
    with session_factory.begin() as db:
        db.query(LoginAttempt).filter(
            LoginAttempt.created_at < now - timedelta(minutes=15)
        ).delete()
        for key, limit in [(identity, 5), (address, 30)]:
            if db.query(func.count(LoginAttempt.id)).filter_by(identity=key).scalar() >= limit:
                raise HTTPException(429, "Too many login attempts; retry in 15 minutes")
        user = db.query(User).filter_by(email=email, active=True).first()
        # Always perform password work, including unknown accounts.
        encoded = user.password_hash if user else "scrypt$dummy$" + "0" * 128
        valid = password_matches(data.password, encoded)
        if not user or not valid:
            for key in (identity, address):
                db.add(LoginAttempt(id=str(uuid.uuid4()), identity=key))
            principal = None
        else:
            token = secrets.token_urlsafe(32)
            db.add(
                AuthSession(
                    token_hash=token_hash(token),
                    user_id=user.id,
                    expires_at=now + timedelta(hours=12),
                )
            )
            principal = {"id": user.id, "email": user.email, "role": user.role}
    if principal is None:
        raise HTTPException(401, "Invalid email or password")
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
        "expires_at": (now + timedelta(hours=12)).isoformat(),
    }


@router.get("/me")
def me(principal=Depends(require_api_key)):
    return principal


@router.post("/logout", dependencies=[Depends(require_api_key)])
def logout(request: Request, response: Response, session_factory: SessionFactory):
    token = request.headers.get("authorization", "").removeprefix("Bearer ") or request.cookies.get(
        "devai_session", ""
    )
    with session_factory.begin() as db:
        db.query(AuthSession).filter_by(token_hash=token_hash(token)).delete()
    response.delete_cookie("devai_session", path="/")
    return {"signed_out": True}


@router.post("/users", dependencies=[Depends(require_api_key)], status_code=201)
def add_user(data: NewUser, session_factory: SessionFactory):
    try:
        with session_factory.begin() as db:
            user = User(
                id=str(uuid.uuid4()),
                email=data.email.strip().lower(),
                password_hash=password_hash(data.password),
                role=data.role,
            )
            db.add(user)
            return {"id": user.id, "email": user.email, "role": user.role}
    except IntegrityError as exc:
        raise HTTPException(409, "Account already exists") from exc
