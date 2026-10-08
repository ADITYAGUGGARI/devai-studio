import uuid
from datetime import datetime
from difflib import SequenceMatcher
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request

from devai.core.auth import require_api_key
from devai.core.database import SessionFactory
from devai.models import ArticleEvidence, Audit, Job, Post, Slide, SourceCandidate
from devai.schemas.research import GenerateInput, ResearchDraftInput
from devai.services.daily import (
    ingest,
    latest_run,
    topic_for_date,
)
from devai.services.generation import generate
from devai.services.jobs import enqueue, enqueue_daily, serialise_job
from devai.services.research import create_editorial_draft, discover
from devai.services.source_urls import canonical_source_url

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.get("/research/discover")
def research_discover(session_factory: SessionFactory):
    return discover()


@router.post("/research/draft")
def research_draft(data: ResearchDraftInput, session_factory: SessionFactory):
    try:
        source_url = canonical_source_url(data.url)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    payload = create_editorial_draft({**data.model_dump(), "url": source_url})
    with session_factory.begin() as db:
        p = Post(id=str(uuid.uuid4()), title=payload["title"], caption=payload["caption"])
        db.add(p)
        db.flush()
        for i, s in enumerate(payload["slides"], 1):
            db.add(
                Slide(
                    id=str(uuid.uuid4()),
                    post_id=p.id,
                    position=f"{i:03d}",
                    headline=s["headline"],
                    body=s["body"],
                    visual_direction=s.get("visual_direction") or None,
                )
            )
        db.add(
            Audit(
                id=str(uuid.uuid4()),
                post_id=p.id,
                event=f"research draft from {data.url}; unverified scaffold",
            )
        )
        return {"id": p.id, "status": "draft", "verification_required": True}


@router.post("/research/generate")
def generate_post(data: GenerateInput, session_factory: SessionFactory):
    try:
        source_url = canonical_source_url(data.url)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    if len(data.excerpt.strip()) < 120:
        raise HTTPException(422, "Source excerpt of at least 120 characters required")
    with session_factory() as db:
        if db.query(SourceCandidate).filter_by(url=source_url).first():
            raise HTTPException(409, "This source was already used in a post")
        titles = [p.title for p in db.query(Post).all()]
        if any(
            SequenceMatcher(None, data.title.casefold(), title.casefold()).ratio() >= 0.86
            for title in titles
        ):
            raise HTTPException(
                409, "Similar post title already exists; review existing content first"
            )
    try:
        generated = generate(data.title, source_url, data.excerpt)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(422, str(exc))
    except Exception:
        raise HTTPException(502, "AI generation failed; no draft was saved")
    with session_factory.begin() as db:
        p = Post(id=str(uuid.uuid4()), title=generated["title"], caption=generated["caption"])
        db.add(p)
        db.flush()
        db.add(
            SourceCandidate(
                id=str(uuid.uuid4()),
                url=source_url,
                title=data.title,
                source="Manual source",
                post_id=p.id,
            )
        )
        db.add(
            ArticleEvidence(
                id=str(uuid.uuid4()),
                post_id=p.id,
                source_url=source_url,
                source_title=data.title,
                source_name="Manual source (review required)",
                excerpt=data.excerpt,
                topic="news",
                editorial_angle=generated.get("editorial_angle", generated["title"]),
            )
        )
        for i, s in enumerate(generated["slides"], 1):
            db.add(
                Slide(
                    id=str(uuid.uuid4()),
                    post_id=p.id,
                    position=f"{i:03d}",
                    headline=s["headline"],
                    body=s["body"],
                    visual_direction=s.get("visual_direction") or None,
                )
            )
        db.add(
            Audit(
                id=str(uuid.uuid4()),
                post_id=p.id,
                event=f"AI-generated draft from {source_url}; fact-check required",
            )
        )
        return {"id": p.id, "status": "draft", "fact_check_required": True}


@router.get("/research/daily/latest")
def daily_latest(session_factory: SessionFactory, request: Request):
    timezone_name = request.app.state.settings.daily_timezone
    timezone = ZoneInfo(timezone_name)
    with session_factory() as db:
        research_job = (
            db.query(Job)
            .filter(Job.kind.in_({"research", "daily_research"}))
            .order_by(Job.created_at.desc(), Job.id.desc())
            .first()
        )
        latest_research = serialise_job(research_job) if research_job else None
    return {
        "run": latest_run(session_factory, timezone_name),
        "latest_research": latest_research,
        "topic": topic_for_date(datetime.now(timezone).date()),
        "timezone": timezone_name,
        "mode": "carousel" if request.app.state.settings.daily_generate_carousel else "research",
    }


@router.post("/research/ingest")
def ingest_scaffolds(session_factory: SessionFactory):
    """Import the legacy unverified link scaffolds for manual curation."""
    return ingest(session_factory, SourceCandidate, Post, Slide, Audit)


@router.post("/research/daily/run", status_code=202)
def create_daily_package(session_factory: SessionFactory, request: Request):
    result = enqueue_daily(
        session_factory,
        request.app.state.settings.daily_timezone,
        generate_carousel=request.app.state.settings.daily_generate_carousel,
    )
    if result["status"] in {"failed", "retry_wait"}:
        from devai.routes.workflow import retry_job

        return retry_job(result["id"], session_factory)
    return result


@router.post("/research/daily/regenerate", status_code=202)
def regenerate_research(session_factory: SessionFactory):
    return enqueue(
        session_factory, "research_generate", {"slide_count": 8}, key="research_generate"
    )
