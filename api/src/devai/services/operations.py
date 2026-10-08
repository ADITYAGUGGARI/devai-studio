"""Version capture and durable publication scheduling."""

import json
import uuid
from datetime import UTC, datetime

from devai.core.auth import token_hash
from devai.models import Post, PostRevision, PublishSchedule, Slide, TopicApproval, WorkspaceSetting
from devai.services.posts import serialize


def topic_fingerprint(topic) -> str:
    return token_hash(
        json.dumps([topic.title, topic.url, topic.excerpt, topic.category], ensure_ascii=False)
    )


def approved_topic(db, topic) -> bool:
    approval = db.get(TopicApproval, topic.id)
    return bool(approval and approval.fingerprint == topic_fingerprint(topic))


def capture_revision(db, post, reason: str):
    db.flush()
    if db.query(PostRevision).filter_by(post_id=post.id, version=post.version).first():
        return
    data = serialize(db, post)
    data["artwork"] = {
        s.id: {
            "path": s.artwork_path,
            "content_hash": s.content_hash,
            "validation_json": s.validation_json,
        }
        for s in db.query(Slide).filter_by(post_id=post.id)
    }
    db.add(
        PostRevision(
            id=str(uuid.uuid4()),
            post_id=post.id,
            version=post.version,
            snapshot_json=json.dumps(data),
            reason=reason,
        )
    )


def settings_values(factory, config) -> dict:
    data = {
        "daily_enabled": config.daily_enabled,
        "daily_hour": config.daily_hour,
        "timezone": config.daily_timezone,
        "daily_generate_carousel": config.daily_generate_carousel,
    }
    with factory() as db:
        row = db.get(WorkspaceSetting, "research_schedule")
        if row:
            data.update(json.loads(row.value_json))
    return data


def dispatch_schedules(factory, now=None):
    from devai.services.jobs import insert_job
    from devai.services.managed_publishing import validate_ready

    now = now or datetime.now(UTC)
    with factory.begin() as db:
        rows = (
            db.query(PublishSchedule)
            .filter(PublishSchedule.status == "scheduled", PublishSchedule.due_at <= now)
            .with_for_update(skip_locked=True)
            .all()
        )
        for row in rows:
            post = db.query(Post).filter_by(id=row.post_id).with_for_update().first()
            if not post or post.status != "approved" or post.version != row.version:
                row.status, row.error, row.active_key = (
                    "cancelled",
                    "Approval or content version changed; review and schedule again",
                    None,
                )
                continue
            try:
                validate_ready(db, post)
            except ValueError as exc:
                row.status, row.error, row.active_key = "failed", str(exc), None
                continue
            job = insert_job(
                db,
                "publish",
                {"post_id": row.post_id, "version": row.version},
                key=f"post:{row.post_id}",
            )
            row.job_id, row.status, row.active_key = job.id, "queued", None


def record_worker_heartbeat(factory):
    with factory.begin() as db:
        row = db.query(WorkspaceSetting).filter_by(key="worker_heartbeat").with_for_update().first()
        value = json.dumps({"at": datetime.now(UTC).isoformat()})
        if row:
            row.value_json = value
        else:
            db.add(WorkspaceSetting(key="worker_heartbeat", value_json=value))


def worker_health(factory):
    with factory() as db:
        row = db.get(WorkspaceSetting, "worker_heartbeat")
        at = json.loads(row.value_json)["at"] if row else None
    return {
        "last_seen": at,
        "healthy": bool(
            at and (datetime.now(UTC) - datetime.fromisoformat(at)).total_seconds() < 90
        ),
    }
