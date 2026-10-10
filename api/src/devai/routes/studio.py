"""Revision 4 workspace-scoped API; legacy contracts remain available."""

import base64
import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Literal
from zoneinfo import available_timezones

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import and_, func, or_

from devai.core.auth import require_api_key
from devai.core.database import SessionFactory
from devai.models import Job
from devai.models.studio import ActionReceipt, Finding, ResearchRun, Workspace
from devai.schemas.workflow import Category
from devai.services.jobs import serialise_job
from devai.services.research_schedule import create_research_run

router = APIRouter(prefix="/v1", dependencies=[Depends(require_api_key)])


@router.get("/time-zones")
def time_zones(q: str = ""):
    if len(q) > 100:
        raise HTTPException(422, "Timezone search is too long")
    matches = sorted(zone for zone in available_timezones() if q.casefold() in zone.casefold())
    return {"items": matches[:50], "total": len(matches)}


@router.get("/jobs/{job_id}")
def get_job(job_id: str, session_factory: SessionFactory):
    with session_factory() as db:
        job = db.get(Job, job_id)
        if not job:
            raise HTTPException(404, "Job not found")
        result = serialise_job(job)
        result["serverTime"] = datetime.now(UTC)
        result["canCancel"] = job.kind != "publish" and job.status in {
            "queued",
            "running",
            "retry_wait",
        }
        if job.cancel_requested and job.status == "running":
            result["status"] = "cancelling"
        return result


@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str, request: Request, session_factory: SessionFactory):
    require_editor(request)
    with session_factory.begin() as db:
        job = db.query(Job).filter_by(id=job_id).with_for_update().first()
        if not job:
            raise HTTPException(404, "Job not found")
        if job.kind == "publish":
            raise HTTPException(
                409, "Publishing must be cancelled through its publication reservation"
            )
        if job.status in {"queued", "retry_wait"}:
            job.cancel_requested = True
            job.status, job.active_key, job.finished_at = "cancelled", None, datetime.now(UTC)
            job.step = "Cancelled before starting"
        elif job.status == "running":
            job.cancel_requested = True
        return serialise_job(job)


class ResearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    window: Literal["last_24_hours"] = "last_24_hours"
    rankingPolicyRevision: Literal["developer-24h-v1"] = "developer-24h-v1"
    sourceCatalogRevision: Literal["official-feeds-v1"] = "official-feeds-v1"
    categoryIds: list[Category] | None = Field(default=None, min_length=1, max_length=5)


def require_editor(request):
    if request.state.principal["workspace_role"] not in {"owner", "editor"}:
        raise HTTPException(403, "An owner or editor must start research")


def run_snapshot(db, run):
    job = db.get(Job, run.job_id)
    return {
        "id": run.id,
        "jobId": run.job_id,
        "windowStartUTC": run.window_start,
        "windowEndUTC": run.window_end,
        "rankingPolicy": run.policy,
        "coverage": json.loads(run.coverage_json),
        "status": job.status,
        "job": serialise_job(job),
    }


@router.post("/research/runs", status_code=202)
def start_research(
    data: ResearchInput,
    request: Request,
    session_factory: SessionFactory,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=200),
):
    require_editor(request)
    actor = request.state.principal["id"]
    digest = hashlib.sha256(
        json.dumps([request.method, request.url.path, data.model_dump()], sort_keys=True).encode()
    ).hexdigest()
    with session_factory.begin() as db:
        # Serialize paid/action reservations per studio; unrelated studios remain independent.
        workspace = (
            db.query(Workspace).filter_by(id=request.state.workspace_id).with_for_update().one()
        )
        receipt = (
            db.query(ActionReceipt).filter_by(actor_id=actor, action_key=idempotency_key).first()
        )
        if receipt:
            if receipt.request_hash != digest:
                raise HTTPException(409, {"code": "IDEMPOTENCY_MISMATCH"})
            return json.loads(receipt.response_json)
        configured_categories = (
            json.loads(workspace.settings_json).get("researchSchedule", {}).get("categories")
        )
        result = create_research_run(
            db,
            request.state.workspace_id,
            actor,
            categories=data.categoryIds or configured_categories,
        )
        db.add(
            ActionReceipt(
                id=str(uuid.uuid4()),
                actor_id=actor,
                action_key=idempotency_key,
                request_hash=digest,
                response_json=json.dumps(result),
            )
        )
        return result


@router.get("/research/runs")
def list_runs(session_factory: SessionFactory, cursor: str = ""):
    with session_factory() as db:
        query = db.query(ResearchRun)
        if cursor:
            try:
                if len(cursor) > 1000:
                    raise ValueError()
                payload = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
                created = datetime.fromisoformat(payload["created"])
                identifier = payload["id"]
                if not isinstance(identifier, str):
                    raise ValueError()
            except (ValueError, TypeError, KeyError):
                raise HTTPException(422, "Invalid research history cursor") from None
            query = query.filter(
                or_(
                    ResearchRun.created_at < created,
                    and_(ResearchRun.created_at == created, ResearchRun.id < identifier),
                )
            )
        rows = query.order_by(ResearchRun.created_at.desc(), ResearchRun.id.desc()).limit(25).all()
        next_cursor = None
        if len(rows) > 24:
            last = rows[23]
            next_cursor = (
                base64.urlsafe_b64encode(
                    json.dumps(
                        {
                            "created": last.created_at.isoformat(),
                            "id": last.id,
                        }
                    ).encode()
                )
                .decode()
                .rstrip("=")
            )
        return {"items": [run_snapshot(db, run) for run in rows[:24]], "nextCursor": next_cursor}


@router.get("/research/runs/{run_id}")
def get_run(run_id: str, session_factory: SessionFactory):
    with session_factory() as db:
        run = db.get(ResearchRun, run_id)
        if not run:
            raise HTTPException(404, "Research run not found")
        return run_snapshot(db, run)


@router.get("/research/runs/{run_id}/findings")
def findings(
    run_id: str,
    session_factory: SessionFactory,
    q: str = "",
    disposition: str | None = None,
    category: str | None = None,
    priorityMin: int = 0,
    cursor: str = "",
):
    if len(cursor) > 2000 or not 0 <= priorityMin <= 100:
        raise HTTPException(422, "Invalid cursor or priority")
    with session_factory() as db:
        if not db.get(ResearchRun, run_id):
            raise HTTPException(404, "Research run not found")
        query = db.query(Finding).filter(Finding.run_id == run_id, Finding.score >= priorityMin)
        if q:
            query = query.filter(Finding.title.icontains(q, autoescape=True))
        if disposition:
            query = query.filter_by(disposition=disposition)
        if category:
            query = query.filter_by(category=category)
        total = query.count()
        date = func.coalesce(Finding.published_at, datetime(1970, 1, 1, tzinfo=UTC))
        scope = hashlib.sha256(
            json.dumps([run_id, q, disposition, category, priorityMin]).encode()
        ).hexdigest()
        if cursor:
            try:
                payload = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
                if payload["scope"] != scope:
                    raise ValueError()
                score, published, identifier = (
                    int(payload["score"]),
                    datetime.fromisoformat(payload["date"]),
                    payload["id"],
                )
                if not isinstance(identifier, str) or not 0 <= score <= 100:
                    raise ValueError()
            except (ValueError, TypeError, KeyError):
                raise HTTPException(422, "Invalid cursor for these filters") from None
            query = query.filter(
                or_(
                    Finding.score < score,
                    and_(Finding.score == score, date < published),
                    and_(Finding.score == score, date == published, Finding.id > identifier),
                )
            )
        rows = query.order_by(Finding.score.desc(), date.desc(), Finding.id).limit(25).all()
        next_cursor = None
        if len(rows) > 24:
            last = rows[23]
            published = last.published_at or datetime(1970, 1, 1, tzinfo=UTC)
            next_cursor = (
                base64.urlsafe_b64encode(
                    json.dumps(
                        {
                            "scope": scope,
                            "score": last.score,
                            "date": published.isoformat(),
                            "id": last.id,
                        }
                    ).encode()
                )
                .decode()
                .rstrip("=")
            )
        return {
            "items": [
                {
                    "id": row.id,
                    "title": row.title,
                    "url": row.canonical_url,
                    "topicId": row.topic_id,
                    "source": row.source,
                    "category": row.category,
                    "publishedAt": row.published_at,
                    "capturedAt": row.captured_at,
                    "disposition": row.disposition,
                    "score": row.score,
                    "dimensions": json.loads(row.dimensions_json),
                    "evidence": json.loads(row.evidence_json),
                }
                for row in rows[:24]
            ],
            "total": total,
            "nextCursor": next_cursor,
        }
