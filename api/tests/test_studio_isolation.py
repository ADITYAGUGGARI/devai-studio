"""Exercise persisted isolation and competing edits against the migrated database."""

import pytest
from fastapi import HTTPException

from devai.core.workspaces import scoped_factory
from devai.models import Slide
from devai.models.studio import StudioDocument, StudioVersion, Workspace
from devai.services.studio_documents import create_document, restore_version, save_document


def studios(client):
    factory = client.app.state.session_factory
    with factory.begin() as db:
        for identifier in ("studio-a", "studio-b"):
            db.add(Workspace(id=identifier, name=identifier))
    return scoped_factory(factory, "studio-a"), scoped_factory(factory, "studio-b")


def test_scoped_reads_and_writes(client):
    first, second = studios(client)
    with first.begin() as db:
        document = create_document(db, kind="content", data={"title": "Private"}, actor="a")
        identifier = document.id
        db.add(Slide(id="private-slide", headline="Private pixels"))
    with second.begin() as db:
        assert db.get(StudioDocument, identifier) is None
        assert db.get(Slide, "private-slide") is None
        assert db.query(StudioVersion).count() == 0
    with pytest.raises(HTTPException) as failure:
        with second.begin() as db:
            db.add(Slide(id="foreign-slide", workspace_id="studio-a"))
    assert failure.value.status_code == 404


def test_conflict_and_restore_preserve_history(client):
    first, _ = studios(client)
    with first.begin() as db:
        document = create_document(db, kind="content", data={"title": "Original"}, actor="a")
        identifier = document.id
    with first.begin() as db:
        save_document(db, identifier, revision=1, data={"title": "Saved"}, actor="a")
    with pytest.raises(HTTPException) as failure:
        with first.begin() as db:
            save_document(db, identifier, revision=1, data={"title": "Losing edit"}, actor="b")
    assert failure.value.status_code == 409
    assert failure.value.detail["server"]["data"]["title"] == "Saved"
    with first.begin() as db:
        restored = restore_version(db, identifier, revision=2, target_revision=1, actor="a")
        assert restored.revision == 3
        assert restored.data_json == '{"title": "Original"}'
        assert db.query(StudioVersion).filter_by(document_id=identifier).count() == 3
