"""Transactional document revisions; losing writers never overwrite saved state."""

import json
import uuid

from fastapi import HTTPException
from sqlalchemy import update

from devai.models.content import utc_now
from devai.models.studio import StudioDocument, StudioVersion


def snapshot(document):
    return {
        "id": document.id,
        "kind": document.kind,
        "parent_id": document.parent_id,
        "revision": document.revision,
        "state": document.state,
        "data": json.loads(document.data_json),
        "updated_at": document.updated_at.isoformat(),
    }


def record_version(db, document, actor, reason):
    db.add(
        StudioVersion(
            id=str(uuid.uuid4()),
            workspace_id=document.workspace_id,
            document_id=document.id,
            revision=document.revision,
            data_json=document.data_json,
            state=document.state,
            actor_id=actor,
            reason=reason,
        )
    )


def create_document(db, *, kind, data, actor, parent_id=None, state="draft"):
    document = StudioDocument(
        id=str(uuid.uuid4()),
        kind=kind,
        data_json=json.dumps(data),
        created_by=actor,
        parent_id=parent_id,
        state=state,
    )
    db.add(document)
    db.flush()
    record_version(db, document, actor, "Created")
    return document


def save_document(db, document_id, *, revision, data, actor, reason="Edited", state=None):
    document = db.get(StudioDocument, document_id)
    if document is None or document.deleted_at is not None:
        raise HTTPException(404, "Content not found")
    values = {
        "revision": revision + 1,
        "data_json": json.dumps(data),
        "updated_at": utc_now(),
        "state": state or document.state,
    }
    result = db.execute(
        update(StudioDocument)
        .where(
            StudioDocument.id == document_id,
            StudioDocument.revision == revision,
            StudioDocument.deleted_at.is_(None),
        )
        .values(**values)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        db.refresh(document)
        raise HTTPException(
            409,
            {
                "code": "revision_conflict",
                "message": "This content changed on another device. Compare your changes with the saved version.",
                "server": snapshot(document),
            },
        )
    db.refresh(document)
    record_version(db, document, actor, reason)
    return document


def restore_version(db, document_id, *, revision, target_revision, actor):
    version = (
        db.query(StudioVersion)
        .filter_by(
            document_id=document_id,
            revision=target_revision,
        )
        .first()
    )
    if version is None:
        raise HTTPException(404, "Version not found")
    # A restore is a new edit, never a rewind of the optimistic concurrency token.
    return save_document(
        db,
        document_id,
        revision=revision,
        data=json.loads(version.data_json),
        actor=actor,
        reason=f"Restored revision {target_revision}",
        state="draft",
    )
