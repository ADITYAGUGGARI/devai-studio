"""Revisioned workspace research configuration; provider credentials never leave the server."""

import hashlib
import json
import uuid
from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

from devai.core.auth import require_api_key
from devai.core.database import SessionFactory
from devai.models.studio import ActionReceipt, Workspace
from devai.schemas.workflow import Category
from devai.services.operations import worker_health
from devai.services.research_schedule import schedule_values

router = APIRouter(prefix="/v1/workspaces", dependencies=[Depends(require_api_key)])


class AutoDraftOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = False


class ResearchSettingsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expectedRevision: int = Field(ge=1)
    researchEnabled: bool
    researchLocalTime: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    timeZone: str = Field(max_length=100)
    categories: list[Category] = Field(min_length=1, max_length=5)
    autoDraftOptions: AutoDraftOptions = Field(default_factory=AutoDraftOptions)

    @field_validator("timeZone")
    @classmethod
    def valid_zone(cls, value):
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("Use a valid IANA timezone") from exc
        return value

    @field_validator("categories")
    @classmethod
    def unique_categories(cls, values):
        if len(values) != len(set(values)):
            raise ValueError("Choose each category once")
        return values


def assert_workspace(request, identifier):
    if identifier != request.state.workspace_id:
        raise HTTPException(404, "Workspace not found")


@router.get("/{workspace_id}/settings")
def get_settings(workspace_id: str, request: Request, session_factory: SessionFactory):
    assert_workspace(request, workspace_id)
    with session_factory() as db:
        result = schedule_values(db.get(Workspace, workspace_id))
        result["canEdit"] = request.state.principal["workspace_role"] == "owner"
        result["autoDraftAvailable"] = False
        result["canRunResearch"] = request.state.principal["workspace_role"] in {"owner", "editor"}
        result["workerHealth"] = worker_health(request.app.state.session_factory)
        return result


@router.patch("/{workspace_id}/settings")
def save_settings(
    workspace_id: str,
    data: ResearchSettingsInput,
    request: Request,
    session_factory: SessionFactory,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=200),
):
    assert_workspace(request, workspace_id)
    if request.state.principal["workspace_role"] != "owner":
        raise HTTPException(403, "Only a studio owner can change the research schedule")
    if data.autoDraftOptions.enabled:
        raise HTTPException(
            409,
            "Automatic drafts require the revision 4 generation workflow; research can be scheduled independently",
        )
    actor = request.state.principal["id"]
    digest = hashlib.sha256(
        json.dumps([request.url.path, data.model_dump()], sort_keys=True).encode()
    ).hexdigest()
    with session_factory.begin() as db:
        workspace = db.query(Workspace).filter_by(id=workspace_id).with_for_update().one()
        receipt = (
            db.query(ActionReceipt).filter_by(actor_id=actor, action_key=idempotency_key).first()
        )
        if receipt:
            if receipt.request_hash != digest:
                raise HTTPException(409, {"code": "IDEMPOTENCY_MISMATCH"})
            return json.loads(receipt.response_json)
        if data.expectedRevision != workspace.revision:
            raise HTTPException(
                409, {"code": "REVISION_CONFLICT", "server": schedule_values(workspace)}
            )
        stored = json.loads(workspace.settings_json)
        stored["researchSchedule"] = {
            **data.model_dump(exclude={"expectedRevision"}),
            "effectiveAfterUTC": datetime.now(UTC).isoformat(),
        }
        workspace.settings_json = json.dumps(stored)
        workspace.revision += 1
        result = {
            **schedule_values(workspace),
            "canEdit": True,
            "autoDraftAvailable": False,
            "canRunResearch": True,
            "workerHealth": worker_health(request.app.state.session_factory),
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
