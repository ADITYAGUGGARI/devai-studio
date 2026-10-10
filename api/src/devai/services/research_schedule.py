"""Workspace research schedules with frozen windows and durable daily deduplication."""

import json
import uuid
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from devai.core.workspaces import scoped_factory
from devai.models.studio import ActionReceipt, ResearchRun, Workspace
from devai.services.jobs import insert_job
from devai.services.research_runs import aware

CATEGORIES = ["news", "tutorial", "architecture", "tools", "insight"]
DEFAULTS = {
    "researchEnabled": False,
    "researchLocalTime": "08:00",
    "timeZone": "America/Chicago",
    "categories": CATEGORIES,
    "autoDraftOptions": {"enabled": False},
}


def scheduled_instant(day, local_time, zone_name):
    """First occurrence on a fold; next valid wall time through a spring gap."""
    hour, minute = map(int, local_time.split(":"))
    zone = ZoneInfo(zone_name)
    naive = datetime.combine(day, datetime.min.time()).replace(hour=hour, minute=minute)
    for _ in range(181):
        candidate = naive.replace(tzinfo=zone, fold=0).astimezone(UTC)
        if candidate.astimezone(zone).replace(tzinfo=None) == naive:
            return candidate
        naive += timedelta(minutes=1)
    raise ValueError("Could not resolve this timezone's daily research time")


def schedule_values(workspace, now=None):
    now = aware(now or datetime.now(UTC))
    stored = json.loads(workspace.settings_json)
    values = {**DEFAULTS, **stored.get("researchSchedule", {})}
    zone = ZoneInfo(values["timeZone"])
    day = now.astimezone(zone).date()
    instant = scheduled_instant(day, values["researchLocalTime"], values["timeZone"])
    if instant <= now:
        instant = scheduled_instant(
            day + timedelta(days=1), values["researchLocalTime"], values["timeZone"]
        )
    return {
        **{key: values[key] for key in DEFAULTS},
        "workspaceId": workspace.id,
        "revision": workspace.revision,
        "nextRunAt": instant.isoformat() if values["researchEnabled"] else None,
    }


def create_research_run(db, workspace_id, actor, *, now=None, categories=None, schedule_key=None):
    end = aware(now or datetime.now(UTC))
    identifier = str(uuid.uuid4())
    job = insert_job(
        db,
        "research_v4",
        {"run_id": identifier, "categories": categories or CATEGORIES},
        key=f"{workspace_id}:research-v4",
        schedule_key=schedule_key,
    )
    run = db.query(ResearchRun).filter_by(job_id=job.id).first()
    if not run:
        run = ResearchRun(
            id=identifier,
            job_id=job.id,
            window_start=end - timedelta(hours=24),
            window_end=end,
            created_by=actor,
        )
        db.add(run)
        db.flush()
    return {
        "runId": run.id,
        "jobId": job.id,
        "windowStartUTC": aware(run.window_start).isoformat(),
        "windowEndUTC": aware(run.window_end).isoformat(),
    }


def enqueue_workspace_schedule(factory, workspace_id, *, now=None):
    now = aware(now or datetime.now(UTC))
    workspace_factory = scoped_factory(factory, workspace_id)
    with workspace_factory.begin() as db:
        workspace = db.query(Workspace).filter_by(id=workspace_id).with_for_update().first()
        if not workspace:
            return None
        stored = json.loads(workspace.settings_json).get("researchSchedule", {})
        values = {**DEFAULTS, **stored}
        if not values["researchEnabled"]:
            return None
        day = now.astimezone(ZoneInfo(values["timeZone"])).date()
        due = scheduled_instant(day, values["researchLocalTime"], values["timeZone"])
        effective = datetime.fromisoformat(
            stored.get("effectiveAfterUTC", workspace.created_at.isoformat())
        )
        if now < due or due <= aware(effective):
            return None
        key = f"research-daily:{values['timeZone']}:{day.isoformat()}"
        receipt = db.query(ActionReceipt).filter_by(actor_id="scheduler", action_key=key).first()
        if receipt:
            return json.loads(receipt.response_json)
        result = create_research_run(
            db,
            workspace_id,
            "scheduler",
            now=now,
            categories=values["categories"],
            schedule_key=key,
        )
        db.add(
            ActionReceipt(
                id=str(uuid.uuid4()),
                actor_id="scheduler",
                action_key=key,
                request_hash="scheduled-research-v1",
                response_json=json.dumps(result),
            )
        )
        return result
