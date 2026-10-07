import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException

from devai.core.auth import require_api_key
from devai.core.database import SessionFactory
from devai.models import Audit, Job, Post, Slide
from devai.schemas.posts import PostInput, SlideUpdate, UpdateInput
from devai.services.jobs import assert_idle, insert_job, serialise_job
from devai.services.managed_publishing import validate_ready
from devai.services.posts import serialize

router = APIRouter(dependencies=[Depends(require_api_key)])


def queue_artwork(id: str, session_factory, slide_id: str | None = None):
    with session_factory.begin() as db:
        post = db.query(Post).filter_by(id=id).with_for_update().first()
        if not post:
            raise HTTPException(404, "Post not found")
        if post.status in {"publishing", "published"}:
            raise HTTPException(409, "Post cannot be changed")
        existing = db.query(Job).filter_by(active_key=f"post:{id}").first()
        if existing:
            return serialise_job(existing)
        slides = db.query(Slide).filter_by(post_id=id).all()
        selected = [s for s in slides if not slide_id or s.id == slide_id]
        if not selected:
            raise HTTPException(404, "No matching slides")
        post.version, post.status = str(int(post.version) + 1), "draft"
        for slide in selected:
            slide.content_hash, slide.validation_json = None, None
        job = insert_job(
            db,
            "artwork",
            {"post_id": id, "version": post.version, "slide_id": slide_id},
            key=f"post:{id}",
        )
        db.add(
            Audit(id=str(uuid.uuid4()), post_id=id, event="Artwork queued; approval invalidated")
        )
        return serialise_job(job)


@router.post("/posts/{id}/artwork", status_code=202)
def generate_artwork(id: str, session_factory: SessionFactory):
    return queue_artwork(id, session_factory)


@router.post("/posts/{id}/slides/{slide_id}/regenerate", status_code=202)
def regenerate_slide(id: str, slide_id: str, session_factory: SessionFactory):
    return queue_artwork(id, session_factory, slide_id)


@router.get("/posts/{id}")
def get_post(id: str, session_factory: SessionFactory):
    with session_factory() as db:
        post = db.query(Post).filter_by(id=id).with_for_update().first()
        if not post:
            raise HTTPException(404)
        return serialize(db, post)


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
        p = db.query(Post).filter_by(id=id).with_for_update().first()
        if not p:
            raise HTTPException(404)
        if p.status in ("publishing", "published"):
            raise HTTPException(409, "Cannot edit publishing/published content")
        try:
            assert_idle(db, id)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        p.verification_json = None
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
        p = db.query(Post).filter_by(id=id).with_for_update().first()
        if not p:
            raise HTTPException(404)
        try:
            assert_idle(db, id)
            if action == "approve":
                validate_ready(db, p)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
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
        p = db.query(Post).filter_by(id=id).with_for_update().first()
        if not p:
            raise HTTPException(404, "Post not found")
        if p.status in ("publishing", "published"):
            raise HTTPException(409, "Post cannot be edited")
        s = db.get(Slide, slide_id)
        if not s or s.post_id != id:
            raise HTTPException(404, "Slide not found")
        try:
            assert_idle(db, id)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        s.content_hash, s.validation_json = None, None
        p.verification_json = None
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
