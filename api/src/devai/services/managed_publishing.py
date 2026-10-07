"""Version-bound JPEG snapshots and approval-gated, non-retrying publication."""

import hashlib
import json
import os
import secrets
import uuid
from pathlib import Path
from urllib.parse import urlsplit

from sqlalchemy import update

from devai.integrations.instagram import InstagramPublisher
from devai.models import ArticleEvidence, Audit, MediaAsset, Post, PublishAttempt, Slide
from devai.services.artwork import normalize_image, slide_hash


def validate_ready(db, post: Post) -> list[Slide]:
    evidence = db.query(ArticleEvidence).filter_by(post_id=post.id).first()
    if (
        not evidence
        or len(evidence.excerpt) < 120
        or evidence.source_url not in (post.caption or "")
    ):
        raise ValueError(
            "Saved source evidence and its exact citation are required before approval or publishing"
        )
    if len(post.caption or "") > 2200:
        raise ValueError("Caption exceeds Instagram's 2,200-character limit")
    slides = db.query(Slide).filter_by(post_id=post.id).order_by(Slide.position).all()
    if not 6 <= len(slides) <= 8:
        raise ValueError("Approval requires six to eight slides")
    for index, slide in enumerate(slides, 1):
        if (
            not slide.artwork_path
            or not Path(slide.artwork_path).is_file()
            or slide.composition_mode != "ai_native"
        ):
            raise ValueError(f"Slide {index} needs a complete AI-native image")
        packet = {
            "headline": slide.headline or "",
            "body": slide.body or "",
            "visual_direction": slide.visual_direction,
        }
        if slide.content_hash != slide_hash(post.title, packet):
            raise ValueError(f"Slide {index} image is stale; regenerate after editing")
        report = json.loads(slide.validation_json or "{}")
        raw = Path(slide.artwork_path).read_bytes()
        if (
            not report.get("passed")
            or report.get("image_sha256") != hashlib.sha256(raw).hexdigest()
        ):
            raise ValueError(f"Slide {index} image must pass validation before approval")
        normalize_image(raw)
    return slides


def public_base() -> str:
    base = os.getenv("PUBLIC_MEDIA_BASE_URL", "").rstrip("/")
    parts = urlsplit(base)
    if (
        parts.scheme != "https"
        or not parts.hostname
        or parts.username
        or parts.query
        or parts.fragment
        or parts.hostname in {"localhost", "127.0.0.1", "::1"}
    ):
        raise ValueError(
            "Set PUBLIC_MEDIA_BASE_URL to the public HTTPS address of this API so Instagram can fetch its JPEGs"
        )
    return base


def publish_managed(
    session_factory, post_id: str, version: str, *, progress=lambda *_: None
) -> dict:
    base = public_base()
    attempt_id = str(uuid.uuid4())
    root = Path(os.getenv("PUBLISH_MEDIA_DIR", ".local-data/publishing-media")).resolve()
    root.mkdir(parents=True, exist_ok=True)
    created = []
    try:
        with session_factory.begin() as db:
            post = db.query(Post).filter_by(id=post_id).with_for_update().first()
            if not post or post.version != version or post.status != "approved":
                raise ValueError("Only the current approved version can be published")
            slides = validate_ready(db, post)
            reserved = db.execute(
                update(Post)
                .where(Post.id == post_id, Post.version == version, Post.status == "approved")
                .values(status="publishing")
            )
            if reserved.rowcount != 1:
                raise ValueError("This version is already reserved for publication")
            urls = []
            for slide in slides:
                token = secrets.token_hex(32)
                data = normalize_image(Path(slide.artwork_path).read_bytes(), output_format="JPEG")
                path = root / f"{token}.jpg"
                path.write_bytes(data)
                created.append(path)
                db.add(
                    MediaAsset(
                        token=token,
                        post_id=post_id,
                        version=version,
                        slide_id=slide.id,
                        path=str(path),
                        sha256=hashlib.sha256(data).hexdigest(),
                    )
                )
                urls.append(f"{base}/media/{token}.jpg")
            caption = post.caption or ""
            db.add(
                PublishAttempt(id=attempt_id, post_id=post_id, version=version, status="started")
            )
            db.add(
                Audit(
                    id=str(uuid.uuid4()),
                    post_id=post_id,
                    event=f"Publishing reserved version {version}; immutable JPEG snapshot",
                )
            )
    except Exception:
        for path in created:
            path.unlink(missing_ok=True)
        raise
    progress(0, 1, "Publishing approved JPEG carousel to Instagram")
    try:
        with InstagramPublisher() as publisher:
            media_id = publisher.publish_carousel(urls, caption)
    except Exception as exc:
        with session_factory.begin() as db:
            attempt = db.get(PublishAttempt, attempt_id)
            attempt.status, attempt.error = "needs_reconciliation", type(exc).__name__
            db.add(
                Audit(
                    id=str(uuid.uuid4()),
                    post_id=post_id,
                    event="Instagram outcome uncertain; reconcile before any further publishing",
                )
            )
        raise ValueError(
            "Instagram outcome uncertain; reconcile this attempt, automatic retries are disabled"
        ) from exc
    with session_factory.begin() as db:
        post = db.query(Post).filter_by(id=post_id).with_for_update().first()
        post.status = "published"
        attempt = db.get(PublishAttempt, attempt_id)
        attempt.status, attempt.external_id = "published", media_id
        db.add(
            Audit(
                id=str(uuid.uuid4()),
                post_id=post_id,
                event=f"Published approved version {version}, media {media_id}",
            )
        )
    progress(1, 1, "Published")
    return {"status": "published", "post_id": post_id, "instagram_media_id": media_id}
