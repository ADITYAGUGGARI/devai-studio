"""Revisioned personal preferences; publication timestamps remain immutable."""

import hashlib
import json
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

from devai.core.auth import require_api_key
from devai.core.database import SessionFactory
from devai.models import User
from devai.models.authentication import UserProfile
from devai.models.content import utc_now
from devai.models.studio import ActionReceipt, Membership, Workspace

router = APIRouter(prefix="/v1", dependencies=[Depends(require_api_key)])


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expectedRevision: int = Field(ge=1)
    displayName: str = Field(min_length=1, max_length=80)
    locale: Literal["en"] = "en"
    timeZone: str = Field(min_length=1, max_length=100)

    @field_validator("displayName")
    @classmethod
    def trimmed_name(cls, value):
        value = value.strip()
        if not value or any(ord(character) < 32 for character in value):
            raise ValueError("Enter a display name without control characters")
        return value

    @field_validator("timeZone")
    @classmethod
    def valid_timezone(cls, value):
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError("Choose a valid IANA timezone") from None
        return value


def profile_snapshot(user, profile):
    return {
        "id": user.id,
        "email": user.email,
        "displayName": profile.display_name if profile else "",
        "locale": profile.locale if profile else "en",
        "timeZone": profile.time_zone if profile else "America/Chicago",
        "revision": profile.revision if profile else 1,
        "updatedAt": profile.updated_at.isoformat() if profile else None,
    }


def actor_user(db, request, *, lock=False):
    query = db.query(User).filter_by(id=request.state.principal["id"], active=True)
    user = (query.with_for_update() if lock else query).first()
    if not user:
        raise HTTPException(401, "Sign in with a personal account to manage your profile")
    return user


@router.get("/me")
def me(request: Request, session_factory: SessionFactory):
    with request.app.state.session_factory() as db:
        user = actor_user(db, request)
        result = profile_snapshot(user, db.get(UserProfile, user.id))
        # Memberships belong to the authenticated identity, not a client supplied user ID.
        result["workspaces"] = [
            {
                "id": member.workspace_id,
                "name": db.get(Workspace, member.workspace_id).name,
                "role": member.role,
                "publishPermission": bool(member.publish_permission),
            }
            for member in db.query(Membership).filter_by(user_id=user.id)
        ]
        return result


@router.patch("/me")
def update_me(
    data: ProfileUpdate,
    request: Request,
    session_factory: SessionFactory,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=200),
):
    digest = hashlib.sha256(
        json.dumps(["PATCH", "/v1/me", data.model_dump()], sort_keys=True).encode()
    ).hexdigest()
    with session_factory.begin() as db:
        user = actor_user(db, request, lock=True)
        receipt = (
            db.query(ActionReceipt).filter_by(actor_id=user.id, action_key=idempotency_key).first()
        )
        if receipt:
            if receipt.request_hash != digest:
                raise HTTPException(
                    409,
                    {
                        "code": "IDEMPOTENCY_MISMATCH",
                        "message": "This action key was used for a different request",
                    },
                )
            return json.loads(receipt.response_json)
        profile = db.get(UserProfile, user.id)
        current = profile.revision if profile else 1
        if current != data.expectedRevision:
            raise HTTPException(
                409,
                {
                    "code": "revision_conflict",
                    "message": "Your profile changed on another device. Your input has not been saved.",
                    "server": profile_snapshot(user, profile),
                },
            )
        if not profile:
            profile = UserProfile(user_id=user.id)
            db.add(profile)
        profile.display_name = data.displayName
        profile.locale = data.locale
        profile.time_zone = data.timeZone
        profile.revision = current + 1
        profile.updated_at = utc_now()
        result = profile_snapshot(user, profile)
        import uuid

        db.add(
            ActionReceipt(
                id=str(uuid.uuid4()),
                actor_id=user.id,
                action_key=idempotency_key,
                request_hash=digest,
                response_json=json.dumps(result),
            )
        )
        return result
