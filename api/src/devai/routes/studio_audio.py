"""Workspace-authorized expiring uploads; audio is not available until decoded."""

import hashlib
import hmac
import json
import os
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator

from devai.core.auth import require_api_key
from devai.core.database import SessionFactory
from devai.models import Job
from devai.services.jobs import ACTIVE, insert_job, serialise_job
from devai.services.studio_content import document, mutation, require_role, view
from devai.services.studio_documents import create_document, save_document

router = APIRouter(prefix="/v1", dependencies=[Depends(require_api_key)])
ActionKey = Header(alias="Idempotency-Key", min_length=1, max_length=200)
MAX_BYTES = 50 * 1024 * 1024


class AudioLicense(BaseModel):
    model_config = ConfigDict(extra="forbid")
    acknowledged: Literal[True]
    basis: Literal["owned", "licensed"]
    reference: str = Field(min_length=3, max_length=1000)


class AudioUpload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fileName: str = Field(min_length=1, max_length=160)
    mimeType: Literal["audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp4", "audio/x-m4a"]
    sizeBytes: int = Field(gt=0, le=MAX_BYTES)
    license: AudioLicense

    @model_validator(mode="after")
    def safe_name(self):
        if (
            Path(self.fileName).name != self.fileName
            or "\\" in self.fileName
            or any(ord(c) < 32 for c in self.fileName)
            or Path(self.fileName).suffix.lower() not in {".wav", ".mp3", ".m4a"}
        ):
            raise ValueError("Choose a WAV, MP3 or M4A file with a plain file name")
        return self


class CompleteUpload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


@router.post("/outputs/{output_id}/audio/uploads", status_code=201)
def prepare(
    output_id: str,
    data: AudioUpload,
    request: Request,
    session_factory: SessionFactory,
    idempotency_key: str = ActionKey,
):
    require_role(request, {"owner", "editor"})
    with session_factory.begin() as db:

        def create(actor):
            output = document(db, output_id, "output")
            if json.loads(output.data_json)["format"] != "reel":
                raise HTTPException(422, "Audio uploads belong to a Reel")
            token = secrets.token_urlsafe(32)
            row = create_document(
                db,
                kind="audio_upload",
                parent_id=output_id,
                actor=actor,
                data={
                    **data.model_dump(),
                    "privateTokenHash": hashlib.sha256(token.encode()).hexdigest(),
                    "expiresAt": (datetime.now(UTC) + timedelta(minutes=15)).isoformat(),
                },
                state="awaiting_bytes",
            )
            return {
                "upload": view(row),
                "uploadPath": f"/v1/uploads/{row.id}/bytes",
                "completePath": f"/v1/uploads/{row.id}/complete",
                "token": token,
            }

        return mutation(db, request, idempotency_key, data.model_dump(), create)


@router.get("/uploads/{upload_id}")
def get_upload(upload_id: str, session_factory: SessionFactory):
    with session_factory() as db:
        row = document(db, upload_id, "audio_upload")
        data = view(row)
        job_id = data["data"].get("jobId")
        job = db.get(Job, job_id) if job_id else None
        return {**data, "job": serialise_job(job) if job else None}


@router.put("/uploads/{upload_id}/bytes")
async def put_bytes(
    upload_id: str,
    request: Request,
    session_factory: SessionFactory,
    upload_token: str = Header(alias="X-Upload-Token"),
):
    require_role(request, {"owner", "editor"})
    with session_factory() as db:
        row = document(db, upload_id, "audio_upload")
        saved = json.loads(row.data_json)
        parent = row.parent_id
        if not hmac.compare_digest(
            hashlib.sha256(upload_token.encode()).hexdigest(), saved["privateTokenHash"]
        ):
            raise HTTPException(403, "The upload authorization is invalid")
        if datetime.fromisoformat(saved["expiresAt"]) < datetime.now(UTC):
            raise HTTPException(410, "Upload expired; prepare a new upload")
        if request.headers.get("content-type", "").split(";")[0] != saved["mimeType"]:
            raise HTTPException(422, "The upload content type must match the selected audio file")
        if request.headers.get("content-encoding"):
            raise HTTPException(422, "Upload the original audio bytes without content encoding")
    root = Path(os.getenv("STUDIO_MEDIA_DIR", ".local-data/studio-media")).resolve() / parent
    root.mkdir(parents=True, exist_ok=True)
    temporary = root / f"{uuid.uuid4().hex}.part"
    count, checksum = 0, hashlib.sha256()
    try:
        with temporary.open("wb") as target:
            async for chunk in request.stream():
                count += len(chunk)
                if count > min(MAX_BYTES, saved["sizeBytes"]):
                    raise HTTPException(413, "Uploaded bytes exceed the declared file size")
                target.write(chunk)
                checksum.update(chunk)
        if count != saved["sizeBytes"]:
            raise HTTPException(422, "Upload was incomplete; resend the original file")
        sha = checksum.hexdigest()
        with session_factory.begin() as db:
            row = document(db, upload_id, "audio_upload", lock=True)
            saved = json.loads(row.data_json)
            if saved.get("sha256"):
                if sha != saved["sha256"]:
                    raise HTTPException(409, "This upload already contains different bytes")
                return {"sha256": sha, "sizeBytes": count}
            path = root / f"{upload_id}.uploaded"
            temporary.replace(path)
            saved.update(privatePath=str(path), sha256=sha)
            save_document(
                db,
                row.id,
                revision=row.revision,
                data=saved,
                actor=request.state.principal["id"],
                state="bytes_received",
            )
        return {"sha256": sha, "sizeBytes": count}
    finally:
        temporary.unlink(missing_ok=True)


@router.post("/uploads/{upload_id}/complete", status_code=202)
def complete(
    upload_id: str,
    data: CompleteUpload,
    request: Request,
    session_factory: SessionFactory,
    idempotency_key: str = ActionKey,
):
    require_role(request, {"owner", "editor"})
    with session_factory.begin() as db:

        def finish(actor):
            row = document(db, upload_id, "audio_upload", lock=True)
            saved = json.loads(row.data_json)
            if saved.get("sha256") != data.sha256:
                raise HTTPException(409, "Upload all original bytes before validation")
            existing = db.get(Job, saved.get("jobId")) if saved.get("jobId") else None
            if saved.get("assetId") or (existing and existing.status in ACTIVE):
                return {
                    "uploadId": row.id,
                    "jobId": saved.get("jobId"),
                    "assetId": saved.get("assetId"),
                }
            job = insert_job(
                db, "studio_audio_upload", {"upload_id": row.id}, key=f"audio-upload:{row.id}"
            )
            saved["jobId"] = job.id
            save_document(
                db, row.id, revision=row.revision, data=saved, actor=actor, state="validating"
            )
            return {"uploadId": row.id, "jobId": job.id}

        return mutation(db, request, idempotency_key, data.model_dump(), finish)
