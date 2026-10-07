import uuid
from difflib import SequenceMatcher

from fastapi import APIRouter, Depends, HTTPException

from devai.core.auth import require_api_key
from devai.core.database import SessionFactory
from devai.models import Audit, Post, Slide, SourceCandidate
from devai.schemas.research import GenerateInput, ResearchDraftInput
from devai.services.daily import ingest
from devai.services.generation import generate
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
        for i, s in enumerate(payload["slides"], 1):
            db.add(
                Slide(
                    id=str(uuid.uuid4()),
                    post_id=p.id,
                    position=f"{i:03d}",
                    headline=s["headline"],
                    body=s["body"],
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
        for i, s in enumerate(generated["slides"], 1):
            db.add(
                Slide(
                    id=str(uuid.uuid4()),
                    post_id=p.id,
                    position=f"{i:03d}",
                    headline=s["headline"],
                    body=s["body"],
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


@router.post("/research/ingest")
def ingest_daily(session_factory: SessionFactory):
    return ingest(session_factory, SourceCandidate, Post, Slide, Audit)
