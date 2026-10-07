"""Publication uses managed media bound to the approved version, never arbitrary URLs."""

import hashlib
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from devai.core.auth import require_api_key
from devai.core.database import SessionFactory
from devai.models import Audit, Job, MediaAsset, Post, PublishAttempt
from devai.schemas.posts import PublishInput
from devai.services.jobs import assert_idle, insert_job, serialise_job
from devai.services.managed_publishing import public_base, validate_ready

router = APIRouter()


@router.get("/media/{token}.jpg")
def public_media(token: str, session_factory: SessionFactory):
    with session_factory() as db:
        asset = db.get(MediaAsset, token)
        if not asset or not Path(asset.path).is_file():
            raise HTTPException(404)
        raw = Path(asset.path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != asset.sha256:
            raise HTTPException(409, "Media integrity check failed")
        return Response(
            raw,
            media_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=31536000, immutable"},
        )


@router.post("/posts/{id}/publish", dependencies=[Depends(require_api_key)], status_code=202)
def publish_approved(id: str, session_factory: SessionFactory, data: PublishInput | None = None):
    with session_factory.begin() as db:
        post = db.query(Post).filter_by(id=id).with_for_update().first()
        if not post:
            raise HTTPException(404, "Post not found")
        if post.status != "approved":
            raise HTTPException(409, "Only approved content can be published")
        if not os.getenv("INSTAGRAM_ACCESS_TOKEN") or not os.getenv("INSTAGRAM_ACCOUNT_ID"):
            raise HTTPException(503, "Instagram credentials not configured")
        if data and data.image_urls:
            raise HTTPException(
                422,
                "Publishing uses the approved slide images automatically; external URLs are not accepted",
            )
        try:
            assert_idle(db, id)
            public_base()
            validate_ready(db, post)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        job = insert_job(db, "publish", {"post_id": id, "version": post.version}, key=f"post:{id}")
        return serialise_job(job)


class ReconcileInput(BaseModel):
    published: bool
    external_id: str | None = Field(default=None, max_length=200)
    note: str = Field(min_length=10, max_length=1000)


@router.get("/posts/{id}/publishing", dependencies=[Depends(require_api_key)])
def publishing_history(id: str, session_factory: SessionFactory):
    with session_factory() as db:
        return [
            {
                "id": a.id,
                "version": a.version,
                "status": a.status,
                "external_id": a.external_id,
                "error": a.error,
            }
            for a in db.query(PublishAttempt).filter_by(post_id=id).all()
        ]


@router.post("/posts/{id}/reconcile", dependencies=[Depends(require_api_key)])
def reconcile(id: str, data: ReconcileInput, session_factory: SessionFactory):
    with session_factory.begin() as db:
        post = db.query(Post).filter_by(id=id).with_for_update().first()
        if not post or post.status != "publishing":
            raise HTTPException(409, "No uncertain publishing outcome to reconcile")
        if data.published and not data.external_id:
            raise HTTPException(422, "Instagram media ID is required for a confirmed publication")
        try:
            assert_idle(db, id)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        attempt = (
            db.query(PublishAttempt)
            .filter_by(post_id=id)
            .order_by(PublishAttempt.created.desc())
            .first()
        )
        if attempt:
            attempt.status = "published" if data.published else "confirmed_not_published"
            attempt.external_id = data.external_id if data.published else None
        post.status = "published" if data.published else "draft"
        db.add(
            Audit(
                id=str(uuid.uuid4()),
                post_id=id,
                event=f"Human reconciliation: {'published' if data.published else 'confirmed not published'}; {data.note}",
            )
        )
        for job in db.query(Job).filter_by(kind="publish", status="needs_reconciliation").all():
            import json

            if json.loads(job.payload_json).get("post_id") == id:
                job.step = "Reconciled by reviewer"
        return {"status": post.status}
