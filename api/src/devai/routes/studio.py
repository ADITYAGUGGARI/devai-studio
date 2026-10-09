"""Revision 4 workspace-scoped API; legacy contracts remain available."""

import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel

from devai.core.auth import require_api_key
from devai.core.database import SessionFactory
from devai.models import Job
from devai.models.studio import ActionReceipt, Finding, ResearchRun, Workspace
from devai.services.jobs import insert_job, serialise_job

router = APIRouter(prefix="/v1", dependencies=[Depends(require_api_key)])


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
    window: Literal["last_24_hours"] = "last_24_hours"
    rankingPolicyRevision: Literal["developer-24h-v1"] = "developer-24h-v1"
    sourceCatalogRevision: Literal["official-feeds-v1"] = "official-feeds-v1"


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
    digest = hashlib.sha256(json.dumps(data.model_dump(), sort_keys=True).encode()).hexdigest()
    with session_factory.begin() as db:
        # Serialize paid/action reservations per studio; unrelated studios remain independent.
        db.query(Workspace).filter_by(id=request.state.workspace_id).with_for_update().one()
        receipt = (
            db.query(ActionReceipt).filter_by(actor_id=actor, action_key=idempotency_key).first()
        )
        if receipt:
            if receipt.request_hash != digest:
                raise HTTPException(409, {"code": "IDEMPOTENCY_MISMATCH"})
            return json.loads(receipt.response_json)
        end = datetime.now(UTC)
        identifier = str(uuid.uuid4())
        job = insert_job(
            db,
            "research_v4",
            {"run_id": identifier},
            key=f"{request.state.workspace_id}:research-v4",
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
        result = {
            "runId": run.id,
            "jobId": job.id,
            "windowStartUTC": run.window_start.isoformat(),
            "windowEndUTC": run.window_end.isoformat(),
        }
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
def list_runs(session_factory: SessionFactory):
    with session_factory() as db:
        return {
            "items": [
                run_snapshot(db, run)
                for run in db.query(ResearchRun).order_by(ResearchRun.created_at.desc()).limit(24)
            ]
        }


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
    cursor: int = 0,
):
    if cursor < 0 or not 0 <= priorityMin <= 100:
        raise HTTPException(422, "Invalid cursor or priority")
    with session_factory() as db:
        if not db.get(ResearchRun, run_id):
            raise HTTPException(404, "Research run not found")
        query = db.query(Finding).filter(Finding.run_id == run_id, Finding.score >= priorityMin)
        if q:
            query = query.filter(Finding.title.ilike(f"%{q}%"))
        if disposition:
            query = query.filter_by(disposition=disposition)
        if category:
            query = query.filter_by(category=category)
        total = query.count()
        rows = (
            query.order_by(Finding.score.desc(), Finding.published_at.desc(), Finding.id)
            .offset(cursor)
            .limit(24)
            .all()
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
                for row in rows
            ],
            "total": total,
            "nextCursor": cursor + 24 if cursor + 24 < total else None,
        }
