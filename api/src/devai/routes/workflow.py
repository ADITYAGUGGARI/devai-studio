"""Queue and job controls used by the existing dashboard."""

import json
import os
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError

from devai.core.auth import require_api_key
from devai.core.database import SessionFactory
from devai.models import Audit, Job, Post, SourceCandidate, Topic
from devai.schemas.workflow import GenerateTopicInput, TopicInput, TopicUpdate
from devai.services.jobs import ACTIVE, enqueue, insert_job, scoped_key, serialise_job
from devai.services.operations import approved_topic, settings_values
from devai.services.source_urls import canonical_source_url
from devai.services.topics import serialise_topic

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.get("/workflow/config")
def workflow_config(request: Request):
    config = request.app.state.settings
    return {
        "worker_enabled": config.background_worker_enabled,
        "daily_enabled": config.daily_enabled,
        "daily_generate_carousel": config.daily_generate_carousel,
        "daily_hour": config.daily_hour,
        "timezone": config.daily_timezone,
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "instagram_configured": bool(
            os.getenv("INSTAGRAM_ACCESS_TOKEN") and os.getenv("INSTAGRAM_ACCOUNT_ID")
        ),
        "public_media_configured": bool(os.getenv("PUBLIC_MEDIA_BASE_URL")),
        **settings_values(request.app.state.session_factory, config),
    }


@router.get("/topics")
def topics(session_factory: SessionFactory):
    with session_factory() as db:
        return [
            {**serialise_topic(t), "approved": approved_topic(db, t)}
            for t in db.query(Topic)
            .order_by(Topic.priority.desc(), Topic.published_at.desc())
            .all()
        ]


@router.post("/topics", status_code=201)
def add_topic(data: TopicInput, session_factory: SessionFactory):
    try:
        url = canonical_source_url(data.url)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    try:
        with session_factory.begin() as db:
            if db.query(SourceCandidate).filter_by(url=url).first():
                raise HTTPException(409, "Source already used in a draft")
            topic = Topic(
                id=str(uuid.uuid4()),
                url=url,
                title=data.title,
                source=data.source,
                excerpt=data.excerpt,
                category=data.category,
                priority=data.priority,
                published_at=data.published_at,
                verification="unverified",
            )
            db.add(topic)
            db.flush()
            return serialise_topic(topic)
    except IntegrityError as exc:
        raise HTTPException(409, "Source already exists in the topic queue") from exc


@router.patch("/topics/{id}")
def update_topic(id: str, data: TopicUpdate, session_factory: SessionFactory):
    with session_factory.begin() as db:
        topic = db.query(Topic).filter_by(id=id).with_for_update().first()
        if not topic:
            raise HTTPException(404)
        if topic.status in {"generating", "used"}:
            raise HTTPException(409, "Cannot change a generating or used topic")
        if data.excerpt is not None:
            topic.verification = "unverified"
        if data.status == "archived":
            topic.selected = False
        for key, value in data.model_dump(exclude_none=True).items():
            setattr(topic, key, value)
        return serialise_topic(topic)


@router.post("/topics/{id}/select")
def select_topic(id: str, session_factory: SessionFactory):
    with session_factory.begin() as db:
        topic = db.query(Topic).filter_by(id=id).with_for_update().first()
        if not topic or topic.status != "queued":
            raise HTTPException(409, "Only a queued topic can be selected")
        db.query(Topic).filter(Topic.selected.is_(True)).update({"selected": False})
        topic.selected = True
        return serialise_topic(topic)


@router.post("/topics/{id}/verify")
def verify_topic(id: str, session_factory: SessionFactory):
    with session_factory.begin() as db:
        topic = db.query(Topic).filter_by(id=id).with_for_update().first()
        if not topic or topic.status != "queued":
            raise HTTPException(409, "Only queued topics can be verified")
        if len(topic.excerpt.strip()) < 240:
            raise HTTPException(
                422, "Provide at least 240 characters of readable source evidence first"
            )
        topic.verification = "human_verified"
        db.add(
            Audit(
                id=str(uuid.uuid4()),
                post_id=None,
                event=f"Reviewer verified source evidence for topic {id}",
            )
        )
        return serialise_topic(topic)


@router.post("/topics/{id}/generate", status_code=202)
def generate_topic(id: str, data: GenerateTopicInput, session_factory: SessionFactory):
    with session_factory.begin() as db:
        topic = db.query(Topic).filter_by(id=id).with_for_update().first()
        if not topic:
            raise HTTPException(404)
        if topic.post_id:
            return {"post_id": topic.post_id, "status": "already_generated"}
        if topic.verification == "unverified" or topic.status == "archived":
            raise HTTPException(409, "Verify the evidence and queue the topic before generation")
        if not approved_topic(db, topic):
            raise HTTPException(409, "Approve the topic after reviewing its source evidence")
        job = insert_job(db, "generate", {"topic_id": id, **data.model_dump()}, key=f"topic:{id}")
        topic.job_id, topic.status = job.id, "generating"
        return serialise_job(job)


@router.post("/research/refresh", status_code=202)
def refresh(session_factory: SessionFactory):
    return enqueue(session_factory, "research", {}, key="research")


class SearchInput(BaseModel):
    query: str = Field(min_length=5, max_length=300)


@router.post("/research/search", status_code=202)
def search(data: SearchInput, session_factory: SessionFactory):
    return enqueue(session_factory, "research", {"query": data.query}, key="research")


@router.get("/jobs")
def jobs(session_factory: SessionFactory):
    with session_factory() as db:
        return [
            serialise_job(job)
            for job in db.query(Job).order_by(Job.created_at.desc()).limit(100).all()
        ]


@router.get("/jobs/{id}")
def job_status(id: str, session_factory: SessionFactory):
    with session_factory() as db:
        job = db.query(Job).filter_by(id=id).with_for_update().first()
        if not job:
            raise HTTPException(404)
        return serialise_job(job)


@router.post("/jobs/{id}/retry", status_code=202)
def retry_job(id: str, session_factory: SessionFactory):
    with session_factory.begin() as db:
        job = db.query(Job).filter_by(id=id).with_for_update().first()
        if not job or job.status not in {"failed", "retry_wait"} or job.kind == "publish":
            raise HTTPException(
                409, "This job cannot be retried; publishing outcomes require reconciliation"
            )
        payload = json.loads(job.payload_json)
        key = (
            f"output:{payload['output_id']}"
            if job.kind == "studio_output" and payload.get("output_id")
            else f"post:{payload['post_id']}"
            if payload.get("post_id")
            else f"topic:{payload['topic_id']}"
            if payload.get("topic_id")
            else f"{job.workspace_id}:research-v4"
            if job.kind == "research_v4"
            else job.schedule_key or "research"
        )
        key = scoped_key(db, key)
        if (
            db.query(Job)
            .filter(Job.active_key == key, Job.id != id, Job.status.in_(ACTIVE))
            .first()
        ):
            raise HTTPException(409, "Another job is using this content")
        if payload.get("post_id"):
            post = db.get(Post, payload["post_id"])
            if (
                not post
                or post.version != payload.get("version", post.version)
                or post.status in {"publishing", "published"}
            ):
                raise HTTPException(409, "Content changed; create a new job instead")
        if payload.get("topic_id"):
            topic = db.get(Topic, payload["topic_id"])
            if topic and topic.job_id not in {None, id}:
                raise HTTPException(409, "Topic has a newer generation job")
            if topic and not topic.post_id:
                topic.status, topic.job_id = "generating", id
        job.status, job.active_key, job.attempts = "queued", key, 0
        job.cancel_requested = False
        job.error, job.finished_at, job.available_at = None, None, datetime.now(UTC)
        return serialise_job(job)
