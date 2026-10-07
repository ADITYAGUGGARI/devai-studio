"""Persistent editorial backlog and explicit topic selection."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from devai.core.auth import require_api_key
from devai.core.database import SessionFactory
from devai.services.editorial_queue import collect_topics, list_topics, set_topic_status

router = APIRouter(prefix="/editorial", dependencies=[Depends(require_api_key)])


class StatusChange(BaseModel):
    status: str


@router.get("/topics")
def topics(session_factory: SessionFactory):
    return {"topics": list_topics(session_factory)}


@router.post("/discover")
def discover_topics(session_factory: SessionFactory):
    try:
        return collect_topics(session_factory)
    except Exception as exc:
        raise HTTPException(502, f"Source discovery failed: {type(exc).__name__}") from exc


@router.patch("/topics/{topic_id}")
def update_topic(topic_id: str, data: StatusChange, session_factory: SessionFactory):
    try:
        updated = set_topic_status(session_factory, topic_id, data.status)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if not updated:
        raise HTTPException(404, "Topic not found")
    return {"id": topic_id, "status": data.status}
