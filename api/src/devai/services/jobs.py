"""Database-backed jobs with atomic claims, leases, retry policy and resumable steps."""

import json
import logging
import os
import threading
import uuid
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy import and_, or_, update
from sqlalchemy.exc import IntegrityError

from devai.models import DailyRun, Job, Post, Topic
from devai.services.provider import ProviderError
from devai.services.verification import GroundingError

logger = logging.getLogger(__name__)
ACTIVE = {"queued", "running", "retry_wait"}


def serialise_job(job: Job) -> dict:
    data = {
        key: getattr(job, key)
        for key in (
            "id",
            "kind",
            "status",
            "error",
            "step",
            "progress",
            "total",
            "attempts",
            "max_attempts",
            "available_at",
            "created_at",
            "finished_at",
        )
    }
    for key in ("available_at", "created_at", "finished_at"):
        value = data[key]
        if value and value.tzinfo is None:
            data[key] = value.replace(tzinfo=UTC)
    data["payload"] = json.loads(job.payload_json)
    data["result"] = json.loads(job.result_json) if job.result_json else None
    return data


def insert_job(
    db, kind: str, payload: dict, *, key: str | None = None, schedule_key: str | None = None
) -> Job:
    existing = db.query(Job).filter(Job.active_key == key).first() if key else None
    if schedule_key and not existing:
        existing = db.query(Job).filter_by(schedule_key=schedule_key).first()
    if existing:
        return existing
    job = Job(
        id=str(uuid.uuid4()),
        kind=kind,
        payload_json=json.dumps(payload),
        active_key=key,
        schedule_key=schedule_key,
        max_attempts=1 if kind == "publish" else 3,
    )
    db.add(job)
    db.flush()
    return job


def enqueue(session_factory, kind: str, payload: dict, *, key=None, schedule_key=None) -> dict:
    try:
        with session_factory.begin() as db:
            return serialise_job(insert_job(db, kind, payload, key=key, schedule_key=schedule_key))
    except IntegrityError:
        with session_factory() as db:
            job = (
                db.query(Job)
                .filter(
                    or_(
                        *([Job.active_key == key] if key else [])
                        + ([Job.schedule_key == schedule_key] if schedule_key else [])
                    )
                )
                .first()
            )
            if not job:
                raise
            return serialise_job(job)


def enqueue_daily(session_factory, timezone: str, *, now=None, generate_carousel=False) -> dict:
    zone = ZoneInfo(timezone)
    current = now or datetime.now(zone)
    current = current.replace(tzinfo=zone) if current.tzinfo is None else current.astimezone(zone)
    date = current.date().isoformat()
    key = f"daily:{timezone}:{date}"
    return enqueue(
        session_factory,
        "daily" if generate_carousel else "daily_research",
        {"timezone": timezone, "local_date": date, "slide_count": 8},
        key=key,
        schedule_key=key,
    )


def assert_idle(db, post_id: str):
    if db.query(Job).filter_by(active_key=f"post:{post_id}").first():
        raise ValueError("Wait for this post's active job to finish before editing or approving")


def _claim(session_factory, *, now=None) -> dict | None:
    now = now or datetime.now(UTC)
    eligible = or_(
        and_(Job.status.in_(["queued", "retry_wait"]), Job.available_at <= now),
        and_(Job.status == "running", Job.lease_until < now),
    )
    with session_factory.begin() as db:
        job = (
            db.query(Job)
            .filter(eligible)
            .order_by(Job.created_at)
            .with_for_update(skip_locked=True)
            .first()
        )
        if not job:
            return None
        if job.kind == "publish" and job.status == "running":
            job.status, job.error, job.active_key = (
                "needs_reconciliation"
                if db.get(Post, json.loads(job.payload_json)["post_id"]).status == "publishing"
                else "failed",
                "Publishing worker stopped; check Instagram before retrying",
                None,
            )
            job.finished_at = now
            return None
        if job.attempts >= job.max_attempts:
            job.status, job.active_key, job.error = (
                "failed",
                None,
                "Retry limit reached after worker interruption",
            )
            job.finished_at = now
            return None
        token = str(uuid.uuid4())
        changed = db.execute(
            update(Job)
            .execution_options(synchronize_session=False)
            .where(Job.id == job.id, eligible)
            .values(
                status="running",
                attempts=Job.attempts + 1,
                lease_token=token,
                lease_until=now + timedelta(seconds=120),
                error=None,
            )
        )
        if changed.rowcount != 1:
            return None
        db.refresh(job)
        return {
            "id": job.id,
            "kind": job.kind,
            "payload": json.loads(job.payload_json),
            "token": token,
        }


def _update(session_factory, claim: dict, **values):
    with session_factory.begin() as db:
        result = db.execute(
            update(Job)
            .where(
                Job.id == claim["id"], Job.status == "running", Job.lease_token == claim["token"]
            )
            .values(**values)
        )
        if result.rowcount != 1:
            raise RuntimeError("Worker lost its job lease")


def dispatch(session_factory, claim: dict, progress) -> dict:
    from devai.services.artwork import generate_post_artwork
    from devai.services.daily import topic_for_date
    from devai.services.managed_publishing import publish_managed
    from devai.services.topics import create_from_topic, research_queue

    kind, payload = claim["kind"], claim["payload"]
    if kind == "verify":
        from devai.models import ArticleEvidence, Slide
        from devai.services.verification import verify_copy

        with session_factory() as db:
            post = db.get(Post, payload["post_id"])
            evidence = db.query(ArticleEvidence).filter_by(post_id=post.id).first()
            if not evidence:
                raise ValueError("Saved source evidence is required")
            content = {
                "title": post.title,
                "caption": post.caption,
                "slides": [
                    {"headline": s.headline, "body": s.body}
                    for s in db.query(Slide).filter_by(post_id=post.id).order_by(Slide.position)
                ],
            }
            excerpt, source_url = evidence.excerpt, evidence.source_url
        report = verify_copy(excerpt, content, source_url)
        if not report["supported"]:
            raise GroundingError(report)
        with session_factory.begin() as db:
            post = db.query(Post).filter_by(id=payload["post_id"]).with_for_update().first()
            if post.version != payload["version"] or post.status in {"published", "publishing"}:
                raise ValueError("Post changed during copy verification")
            lease = db.get(Job, claim["id"])
            if lease.status != "running" or lease.lease_token != claim["token"]:
                raise RuntimeError("Worker lost its job lease")
            post.verification_json = json.dumps(report)
        return {"post_id": post.id, "grounding": report}
    if kind in {"research", "daily_research"}:
        discover_fn = None
        query = payload.get("query")
        if kind == "daily_research" and os.getenv("DAILY_WEB_SEARCH", "false").lower() == "true":
            query = "AI coding agents, developer tools, models and production AI engineering announcements"
        if query:
            from devai.services.search import search_web

            def discover_fn(**kwargs):
                return search_web(query, **kwargs)

        result = research_queue(session_factory, progress=progress, discover_fn=discover_fn)
        if kind == "daily_research":
            with session_factory.begin() as db:
                run = (
                    db.query(DailyRun)
                    .filter_by(local_date=payload["local_date"], timezone=payload["timezone"])
                    .first()
                )
                if not run:
                    run = DailyRun(
                        id=str(uuid.uuid4()),
                        local_date=payload["local_date"],
                        timezone=payload["timezone"],
                        started_at=datetime.now(UTC),
                    )
                    db.add(run)
                run.status = "completed_with_warnings" if result["warnings"] else "completed"
                result = {**json.loads(run.result_json or "{}"), **result}
                run.result_json, run.finished_at = json.dumps(result), datetime.now(UTC)
                run.attempt_count = db.get(Job, claim["id"]).attempts
        return result
    if kind == "artwork":
        return generate_post_artwork(
            session_factory,
            payload["post_id"],
            slide_id=payload.get("slide_id"),
            expected_version=payload["version"],
            force=False,
            progress=progress,
            owner_job=(claim["id"], claim["token"]),
        )
    if kind == "publish":
        return publish_managed(
            session_factory, payload["post_id"], payload["version"], progress=progress
        )
    warnings = []
    if kind in {"daily", "research_generate"}:
        progress(0, 10, "Discovering and verifying recent primary sources")
        research = research_queue(session_factory, progress=lambda *_: None)
        warnings = research["warnings"]
    if kind == "daily":
        with session_factory.begin() as db:
            run = (
                db.query(DailyRun)
                .filter_by(local_date=payload["local_date"], timezone=payload["timezone"])
                .first()
            )
            if run and run.status in {"completed", "completed_with_warnings"}:
                return json.loads(run.result_json or "{}")
            if not run:
                run = DailyRun(
                    id=str(uuid.uuid4()),
                    local_date=payload["local_date"],
                    timezone=payload["timezone"],
                    status="running",
                    started_at=datetime.now(UTC),
                )
                db.add(run)
            run.status, run.error = "running", None
            run.attempt_count = db.get(Job, claim["id"]).attempts
    if not payload.get("topic_id"):
        with session_factory.begin() as db:
            candidates = (
                db.query(Topic)
                .filter(
                    Topic.status == "queued",
                    Topic.verification.in_(["primary_source", "human_verified"]),
                )
                .order_by(Topic.priority.desc(), Topic.published_at.desc())
                .with_for_update(skip_locked=True)
            )
            desired = (
                topic_for_date(datetime.fromisoformat(payload["local_date"]).date())
                if kind == "daily"
                else None
            )
            from devai.services.operations import approved_topic

            approved = [t for t in candidates.all() if approved_topic(db, t)]
            topic = next((t for t in approved if t.category == desired), None)
            topic = topic or (approved[0] if approved else None)
            if not topic:
                raise ValueError(
                    "No approved unused topic is available; review and approve a verified topic"
                )
            payload["topic_id"] = topic.id
            topic.status, topic.job_id = "generating", claim["id"]
        _update(session_factory, claim, payload_json=json.dumps(payload))
    progress(1, 10, "Writing original carousel and checking every factual claim")
    result = create_from_topic(
        session_factory,
        payload["topic_id"],
        slide_count=payload.get("slide_count", 8),
        job_id=claim["id"],
    )
    result["warnings"] = warnings
    _update(
        session_factory,
        claim,
        result_json=json.dumps(result),
        active_key=f"post:{result['post_id']}",
    )
    with session_factory() as db:
        payload["post_id"] = result["post_id"]
        payload["version"] = db.get(Post, result["post_id"]).version
    _update(session_factory, claim, payload_json=json.dumps(payload))
    if payload.get("artwork", True):
        with session_factory() as db:
            version = db.get(Post, result["post_id"]).version
        generate_post_artwork(
            session_factory,
            result["post_id"],
            expected_version=version,
            force=False,
            progress=lambda done, total, step: progress(2 + done, 2 + total, step),
            owner_job=(claim["id"], claim["token"]),
        )
    progress(10, 10, "Draft ready for human review")
    if kind == "daily":
        with session_factory.begin() as db:
            run = (
                db.query(DailyRun)
                .filter_by(local_date=payload["local_date"], timezone=payload["timezone"])
                .one()
            )
            run.status = "completed_with_warnings" if warnings else "completed"
            run.result_json, run.finished_at = json.dumps(result), datetime.now(UTC)
    return result


def safe_error(exc: Exception) -> str:
    if isinstance(exc, (ProviderError, ValueError, LookupError)):
        return str(exc)[:1200]
    if isinstance(exc, httpx.HTTPStatusError):
        return (
            f"Provider HTTP {exc.response.status_code}; check credits, model access and rate limits"
        )
    return f"{type(exc).__name__}: provider or workflow operation failed"


def work_once(session_factory, *, handler=None) -> bool:
    claim = _claim(session_factory)
    if not claim:
        return False
    stop_heartbeat = threading.Event()

    def heartbeat():
        while not stop_heartbeat.wait(20):
            try:
                from devai.services.operations import record_worker_heartbeat

                record_worker_heartbeat(session_factory)
                _update(
                    session_factory, claim, lease_until=datetime.now(UTC) + timedelta(seconds=120)
                )
            except Exception:
                logger.exception("Job lease renewal failed")
                break

    heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
    heartbeat_thread.start()

    def progress(done, total, step):
        _update(session_factory, claim, progress=done, total=max(1, total), step=step)

    try:
        from devai.services.usage import usage_scope

        with usage_scope(session_factory, claim["id"]):
            result = (handler or dispatch)(session_factory, claim, progress)
        _update(
            session_factory,
            claim,
            status="completed_with_warnings" if result.get("warnings") else "completed",
            result_json=json.dumps(result),
            step="Completed with source warnings" if result.get("warnings") else "Completed",
            active_key=None,
            finished_at=datetime.now(UTC),
        )
    except Exception as exc:
        from devai.services.topics import ResearchEvidenceError

        message = safe_error(exc)
        with session_factory.begin() as db:
            job = db.get(Job, claim["id"])
            if job.lease_token != claim["token"]:
                return True
            if isinstance(exc, ResearchEvidenceError):
                job.result_json = json.dumps(exc.report)
            retryable = (
                (isinstance(exc, ProviderError) and exc.retryable)
                or isinstance(exc, httpx.RequestError)
                or (
                    isinstance(exc, httpx.HTTPStatusError)
                    and (exc.response.status_code == 429 or exc.response.status_code >= 500)
                )
            )
            retry = retryable and job.attempts < job.max_attempts and job.kind != "publish"
            job.status = (
                "retry_wait"
                if retry
                else "needs_reconciliation"
                if job.kind == "publish"
                and db.get(Post, json.loads(job.payload_json).get("post_id")).status == "publishing"
                else "failed"
            )
            job.error, job.step = message, "Waiting to retry" if retry else "Failed; review error"
            if isinstance(exc, GroundingError):
                job.result_json = json.dumps({"grounding": exc.report})
            job.available_at = datetime.now(UTC) + timedelta(seconds=30 * 2 ** (job.attempts - 1))
            if not retry:
                job.active_key, job.finished_at = None, datetime.now(UTC)
            payload = json.loads(job.payload_json)
            if payload.get("topic_id"):
                topic = db.get(Topic, payload["topic_id"])
                if topic and not topic.post_id and topic.job_id == job.id:
                    topic.error = message
                    if not retry:
                        topic.status, topic.job_id = "queued", None
            if job.kind in {"daily", "daily_research"}:
                run = (
                    db.query(DailyRun)
                    .filter_by(local_date=payload["local_date"], timezone=payload["timezone"])
                    .first()
                )
                if run:
                    run.status, run.error, run.finished_at = "failed", message, datetime.now(UTC)
    finally:
        stop_heartbeat.set()
        heartbeat_thread.join(2)
    return True


def run_worker(session_factory, stop: threading.Event, settings=None):
    while not stop.is_set():
        try:
            from devai.services.operations import (
                dispatch_schedules,
                record_worker_heartbeat,
                settings_values,
            )

            record_worker_heartbeat(session_factory)
            dispatch_schedules(session_factory)
            schedule = settings_values(session_factory, settings) if settings else {}
            if schedule.get("daily_enabled"):
                now = datetime.now(ZoneInfo(schedule["timezone"]))
                if now.hour >= schedule["daily_hour"]:
                    enqueue_daily(
                        session_factory,
                        schedule["timezone"],
                        now=now,
                        generate_carousel=schedule["daily_generate_carousel"],
                    )
            if not work_once(session_factory):
                stop.wait(1)
        except Exception:
            logger.exception("Background job loop failed")
            stop.wait(3)
