import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from httpx import HTTPError

from devai.core.auth import require_api_key
from devai.core.database import SessionFactory
from devai.models import Audit, Post, Slide
from devai.schemas.posts import PostInput, SlideUpdate, UpdateInput
from devai.services.artwork import generate_post_artwork
from devai.services.posts import serialize

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.post("/posts/{id}/artwork")
def generate_artwork(id: str, session_factory: SessionFactory):
    try:
        return generate_post_artwork(session_factory, id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(502, str(exc)) from exc
    except HTTPError as exc:
        raise HTTPException(502, f"AI artwork request failed ({type(exc).__name__})") from exc


@router.get("/posts")
def posts(session_factory: SessionFactory):
    with session_factory() as db:
        return [serialize(db, p) for p in db.query(Post).order_by(Post.created.desc()).all()]


@router.post("/posts")
def create(data: PostInput, session_factory: SessionFactory):
    with session_factory.begin() as db:
        p = Post(id=str(uuid.uuid4()), title=data.title, caption=data.caption)
        db.add(p)
        for i, s in enumerate(data.slides):
            db.add(
                Slide(
                    id=str(uuid.uuid4()),
                    post_id=p.id,
                    position=str(i + 1).zfill(3),
                    headline=s.headline,
                    body=s.body,
                )
            )
        db.add(Audit(id=str(uuid.uuid4()), post_id=p.id, event="created"))
        return {"id": p.id}


@router.patch("/posts/{id}")
def update(id: str, data: UpdateInput, session_factory: SessionFactory):
    with session_factory.begin() as db:
        p = db.get(Post, id)
        if not p:
            raise HTTPException(404)
        if p.status in ("publishing", "published"):
            raise HTTPException(409, "Cannot edit publishing/published content")
        if data.title is not None:
            p.title = data.title
        if data.caption is not None:
            p.caption = data.caption
        p.version = str(int(p.version) + 1)
        p.status = "draft"
        db.add(Audit(id=str(uuid.uuid4()), post_id=id, event="edited; approval invalidated"))
        return {"status": p.status, "version": p.version}


@router.post("/posts/{id}/{action}")
def transition(
    id: str, action: Literal["submit", "approve", "reject"], session_factory: SessionFactory
):
    allowed = {
        "submit": ({"draft", "rejected"}, "pending_review"),
        "approve": ({"pending_review"}, "approved"),
        "reject": ({"pending_review"}, "rejected"),
    }
    if action not in allowed:
        raise HTTPException(400, "Unknown transition")
    with session_factory.begin() as db:
        p = db.get(Post, id)
        if not p:
            raise HTTPException(404)
        from_states, target = allowed[action]
        if p.status not in from_states:
            raise HTTPException(409, "Invalid status transition")
        p.status = target
        db.add(Audit(id=str(uuid.uuid4()), post_id=id, event=f"{action} version {p.version}"))
        return {"status": p.status}


@router.get("/posts/{id}/audit")
def audit(id: str, session_factory: SessionFactory):
    with session_factory() as db:
        return [
            {"event": a.event, "created": a.created.isoformat()}
            for a in db.query(Audit).filter_by(post_id=id).order_by(Audit.created).all()
        ]


@router.patch("/posts/{id}/slides/{slide_id}")
def update_slide(id: str, slide_id: str, data: SlideUpdate, session_factory: SessionFactory):
    with session_factory.begin() as db:
        p = db.get(Post, id)
        if not p:
            raise HTTPException(404, "Post not found")
        if p.status in ("publishing", "published"):
            raise HTTPException(409, "Post cannot be edited")
        s = db.get(Slide, slide_id)
        if not s or s.post_id != id:
            raise HTTPException(404, "Slide not found")
        if data.headline is not None:
            s.headline = data.headline
        if data.body is not None:
            s.body = data.body
        p.version = str(int(p.version) + 1)
        p.status = "draft"
        db.add(
            Audit(
                id=str(uuid.uuid4()),
                post_id=id,
                event=f"slide edited; approval invalidated; version {p.version}",
            )
        )
        return {"status": p.status, "version": p.version}
