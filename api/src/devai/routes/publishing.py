"""Reserve an approved version before invoking the external publishing adapter."""

import os
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import update

from devai.core.auth import require_api_key
from devai.core.database import SessionFactory
from devai.integrations.instagram import InstagramPublisher
from devai.models import Audit, Post, PublishAttempt, Slide
from devai.schemas.posts import PublishInput

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.post("/posts/{id}/publish")
def publish_approved(id: str, session_factory: SessionFactory, data: PublishInput | None = None):
    with session_factory.begin() as db:
        post = db.get(Post, id)
        if post is None:
            raise HTTPException(404, "Post not found")
        if post.status != "approved":
            raise HTTPException(409, "Only approved content can be published")
        if not os.getenv("INSTAGRAM_ACCESS_TOKEN") or not os.getenv("INSTAGRAM_ACCOUNT_ID"):
            raise HTTPException(503, "Instagram credentials not configured")
        if data is None or not 2 <= len(data.image_urls) <= 10:
            raise HTTPException(422, "Provide 2–10 publicly accessible HTTPS JPEG image URLs")
        if any(not url.startswith("https://") for url in data.image_urls):
            raise HTTPException(422, "Public HTTPS image URLs required")
        if db.query(Slide).filter_by(post_id=id).count() != len(data.image_urls):
            raise HTTPException(422, "Image count must match approved slide count")

        attempt_id = str(uuid.uuid4())
        version, caption = post.version, post.caption
        reserved = db.execute(
            update(Post)
            .where(Post.id == id, Post.status == "approved", Post.version == version)
            .values(status="publishing")
        )
        if reserved.rowcount != 1:
            raise HTTPException(409, "This version is no longer available for publishing")
        db.add(PublishAttempt(id=attempt_id, post_id=id, version=version, status="started"))
        db.add(
            Audit(id=str(uuid.uuid4()), post_id=id, event=f"publishing reserved version {version}")
        )

    try:
        with InstagramPublisher() as publisher:
            external_id = publisher.publish_carousel(data.image_urls, caption)
    except Exception as exc:
        with session_factory.begin() as db:
            attempt = db.get(PublishAttempt, attempt_id)
            attempt.status = "needs_reconciliation"
            # Provider exception messages can contain request URLs and credentials.
            attempt.error = type(exc).__name__
            db.add(
                Audit(
                    id=str(uuid.uuid4()),
                    post_id=id,
                    event="publish failed or uncertain; manual reconciliation required",
                )
            )
        raise HTTPException(
            502,
            "Instagram publish failed or outcome uncertain. Reconcile manually; automatic retry disabled",
        ) from exc

    with session_factory.begin() as db:
        post = db.get(Post, id)
        post.status = "published"
        attempt = db.get(PublishAttempt, attempt_id)
        attempt.status, attempt.external_id = "published", external_id
        db.add(
            Audit(
                id=str(uuid.uuid4()),
                post_id=id,
                event=f"published version {version}, media {external_id}",
            )
        )
    return {"status": "published", "instagram_media_id": external_id}
