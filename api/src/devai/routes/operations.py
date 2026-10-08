"""Topic approval, version history, scheduling and operational visibility."""

import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, text

from devai.core.auth import require_api_key
from devai.core.database import SessionFactory
from devai.models import (
    Job,
    Post,
    PostRevision,
    PublishSchedule,
    Slide,
    Topic,
    TopicApproval,
    UsageEvent,
    User,
    WorkspaceSetting,
)
from devai.services.jobs import assert_idle, insert_job, serialise_job
from devai.services.managed_publishing import public_base, validate_ready
from devai.services.operations import capture_revision, settings_values, topic_fingerprint
from devai.services.posts import serialize

router = APIRouter(dependencies=[Depends(require_api_key)])


class ScheduleInput(BaseModel):
    due_at: datetime


class ResearchSettings(BaseModel):
    daily_enabled: bool
    daily_hour: int = Field(ge=0, le=23)
    timezone: str = Field(max_length=100)
    daily_generate_carousel: bool = False


@router.post("/topics/{id}/approve")
def approve_topic(id: str, request: Request, session_factory: SessionFactory):
    with session_factory.begin() as db:
        topic = db.query(Topic).filter_by(id=id).with_for_update().first()
        if not topic or topic.status != "queued" or topic.verification == "unverified":
            raise HTTPException(
                409, "Review and verify queued source evidence before topic approval"
            )
        db.merge(
            TopicApproval(
                topic_id=id,
                fingerprint=topic_fingerprint(topic),
                approved_by=request.state.principal["id"],
            )
        )
        return {"approved": True}


@router.get("/posts/{id}/versions")
def versions(id: str, session_factory: SessionFactory):
    with session_factory() as db:
        post = db.get(Post, id)
        if not post:
            raise HTTPException(404)
        rows = (
            db.query(PostRevision)
            .filter_by(post_id=id)
            .order_by(PostRevision.created_at.desc())
            .all()
        )
        history = [
            {
                "id": row.id,
                "version": row.version,
                "reason": row.reason,
                "created_at": row.created_at,
                "snapshot": {
                    k: v for k, v in json.loads(row.snapshot_json).items() if k != "artwork"
                },
            }
            for row in rows
        ]
        if not any(row.version == post.version for row in rows):
            history.insert(
                0,
                {
                    "id": None,
                    "version": post.version,
                    "reason": "Current version",
                    "created_at": post.created,
                    "snapshot": serialize(db, post),
                },
            )
        return history


@router.get("/posts/{id}/versions/{revision_id}/slides/{slide_id}/image")
def revision_image(id: str, revision_id: str, slide_id: str, session_factory: SessionFactory):
    with session_factory() as db:
        row = db.get(PostRevision, revision_id)
        if not row or row.post_id != id:
            raise HTTPException(404)
        path = json.loads(row.snapshot_json).get("artwork", {}).get(slide_id, {}).get("path")
        if not path or not Path(path).is_file():
            raise HTTPException(404, "No image saved for this historical version")
        return FileResponse(path, media_type="image/png")


@router.post("/posts/{id}/versions/{revision_id}/restore")
def restore(id: str, revision_id: str, session_factory: SessionFactory):
    with session_factory.begin() as db:
        post = db.query(Post).filter_by(id=id).with_for_update().first()
        row = db.get(PostRevision, revision_id)
        if not post or not row or row.post_id != id:
            raise HTTPException(404)
        if post.status in {"publishing", "published"}:
            raise HTTPException(409, "Published content cannot be restored")
        try:
            assert_idle(db, id)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        capture_revision(db, post, "Before historical restoration")
        data = json.loads(row.snapshot_json)
        post.title, post.caption = data["title"], data["caption"]
        post.version, post.status = str(int(post.version) + 1), "draft"
        post.verification_json = (
            json.dumps(data.get("verification")) if data.get("verification") else None
        )
        for packet in data["slides"]:
            slide = db.get(Slide, packet["id"])
            if not slide or slide.post_id != id:
                raise HTTPException(409, "Historical slide set is unavailable")
            slide.headline, slide.body, slide.visual_direction = (
                packet["headline"],
                packet["body"],
                packet.get("visual_direction"),
            )
            old = data.get("artwork", {}).get(slide.id, {})
            slide.artwork_path, slide.content_hash, slide.validation_json = (
                old.get("path"),
                old.get("content_hash"),
                old.get("validation_json"),
            )
        return {"version": post.version, "status": "draft"}


@router.post("/posts/{id}/verify", status_code=202)
def verify_post(id: str, session_factory: SessionFactory):
    with session_factory.begin() as db:
        post = db.query(Post).filter_by(id=id).with_for_update().first()
        if not post or post.status in {"publishing", "published"}:
            raise HTTPException(409, "Editable draft required")
        try:
            assert_idle(db, id)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        return serialise_job(
            insert_job(db, "verify", {"post_id": id, "version": post.version}, key=f"post:{id}")
        )


@router.post("/posts/{id}/schedule", status_code=201)
def schedule(id: str, data: ScheduleInput, request: Request, session_factory: SessionFactory):
    if data.due_at.tzinfo is None or data.due_at <= datetime.now(UTC):
        raise HTTPException(422, "Schedule a timezone-aware future time")
    if not os.getenv("INSTAGRAM_ACCESS_TOKEN") or not os.getenv("INSTAGRAM_ACCOUNT_ID"):
        raise HTTPException(503, "Instagram credentials not configured")
    with session_factory.begin() as db:
        post = db.query(Post).filter_by(id=id).with_for_update().first()
        if not post or post.status != "approved":
            raise HTTPException(409, "Approve the exact post version before scheduling")
        try:
            assert_idle(db, id)
            public_base()
            validate_ready(db, post)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        if db.query(PublishSchedule).filter_by(active_key=f"post:{id}").first():
            raise HTTPException(409, "This post already has a scheduled publication")
        row = PublishSchedule(
            id=str(uuid.uuid4()),
            post_id=id,
            version=post.version,
            due_at=data.due_at,
            active_key=f"post:{id}",
            created_by=request.state.principal["id"],
        )
        db.add(row)
        return {"id": row.id, "status": "scheduled", "due_at": row.due_at}


@router.get("/publishing/schedules")
def schedules(session_factory: SessionFactory):
    with session_factory() as db:
        result = []
        for row in db.query(PublishSchedule).order_by(PublishSchedule.due_at.desc()):
            job = db.get(Job, row.job_id) if row.job_id else None
            result.append(
                {
                    "id": row.id,
                    "post_id": row.post_id,
                    "version": row.version,
                    "due_at": row.due_at.replace(tzinfo=UTC)
                    if row.due_at.tzinfo is None
                    else row.due_at,
                    "status": job.status if job else row.status,
                    "error": job.error if job else row.error,
                }
            )
        return result


@router.post("/publishing/schedules/{id}/cancel")
def cancel(id: str, session_factory: SessionFactory):
    with session_factory.begin() as db:
        row = db.query(PublishSchedule).filter_by(id=id).with_for_update().first()
        if not row or row.status != "scheduled":
            raise HTTPException(409, "Only future scheduled publications can be cancelled")
        row.status, row.active_key = "cancelled", None
        return {"status": "cancelled"}


@router.get("/ops/summary")
def summary(request: Request, session_factory: SessionFactory):
    with session_factory() as db:
        db.execute(text("SELECT 1"))
        usage = db.query(UsageEvent).order_by(UsageEvent.created_at.desc()).limit(100).all()
        from devai.services.operations import worker_health

        return {
            "worker": worker_health(session_factory),
            "database": "postgresql"
            if db.bind.dialect.name == "postgresql"
            else db.bind.dialect.name,
            "jobs": dict(db.query(Job.status, func.count(Job.id)).group_by(Job.status).all()),
            "accounts": db.query(func.count(User.id)).scalar(),
            "usage": [
                {
                    "id": u.id,
                    "job_id": u.job_id,
                    "model": u.model,
                    "operation": u.operation,
                    "status": u.status,
                    "input_tokens": u.input_tokens,
                    "output_tokens": u.output_tokens,
                    "images": u.images,
                    "estimated_cost_usd": u.estimated_cost_usd,
                    "created_at": u.created_at,
                    "duration_ms": u.duration_ms,
                }
                for u in usage
            ],
            "estimated_cost_usd": sum(
                u.estimated_cost_usd or 0 for u in db.query(UsageEvent).all()
            ),
            "unpriced_calls": db.query(func.count(UsageEvent.id))
            .filter(UsageEvent.estimated_cost_usd.is_(None))
            .scalar(),
            "settings": settings_values(session_factory, request.app.state.settings),
        }


@router.patch("/ops/settings")
def update_settings(data: ResearchSettings, session_factory: SessionFactory):
    try:
        ZoneInfo(data.timezone)
    except (KeyError, ValueError) as exc:
        raise HTTPException(422, "Use a valid IANA timezone") from exc
    with session_factory.begin() as db:
        db.merge(
            WorkspaceSetting(key="research_schedule", value_json=json.dumps(data.model_dump()))
        )
    return data.model_dump()
