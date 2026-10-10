"""Persisted creation, independent outputs, review and private media routes."""

import json
import uuid
import zipfile
from datetime import UTC, datetime
from io import BytesIO

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import FileResponse, Response

from devai.core.auth import require_api_key
from devai.core.database import SessionFactory
from devai.models import Job, Post, Topic
from devai.models.studio import StudioDocument, StudioVersion
from devai.schemas.studio_content import (
    ChangesInput,
    GenerateInput,
    OutputAction,
    RestoreInput,
    ReviewInput,
    SetupEdit,
    SetupInput,
    TimelineInput,
)
from devai.services.studio_content import (
    asset_bytes,
    capabilities,
    current_assets,
    digest,
    document,
    idle,
    mutation,
    public,
    queue_output,
    require_role,
    revision,
    scene_visual_hash,
    timeline_hash,
    topic_packet,
    view,
)
from devai.services.studio_documents import create_document, save_document

router = APIRouter(prefix="/v1", dependencies=[Depends(require_api_key)])
ActionKey = Header(alias="Idempotency-Key", min_length=1, max_length=200)


@router.get("/providers/capabilities")
def provider_capabilities():
    return capabilities()


@router.post("/setups", status_code=201)
def create_setup(
    data: SetupInput,
    request: Request,
    session_factory: SessionFactory,
    idempotency_key: str = ActionKey,
):
    require_role(request, {"owner", "editor"})
    with session_factory.begin() as db:

        def create(actor):
            topic_packet(db, data.topicId)
            row = create_document(db, kind="setup", data=data.model_dump(), actor=actor)
            return view(row)

        return mutation(db, request, idempotency_key, data.model_dump(), create)


@router.get("/setups/{setup_id}")
def get_setup(setup_id: str, session_factory: SessionFactory):
    with session_factory() as db:
        return view(document(db, setup_id, "setup"))


@router.patch("/setups/{setup_id}")
def edit_setup(
    setup_id: str,
    data: SetupEdit,
    request: Request,
    session_factory: SessionFactory,
    idempotency_key: str = ActionKey,
):
    require_role(request, {"owner", "editor"})
    with session_factory.begin() as db:

        def edit(actor):
            row = document(db, setup_id, "setup", lock=True)
            revision(row, data.expectedRevision)
            if json.loads(row.data_json).get("contentId"):
                raise HTTPException(
                    409, "This setup has generated outputs; create a new setup to change formats"
                )
            topic_packet(db, data.topicId)
            return view(
                save_document(
                    db,
                    row.id,
                    revision=row.revision,
                    actor=actor,
                    data=data.model_dump(exclude={"expectedRevision"}),
                )
            )

        return mutation(db, request, idempotency_key, data.model_dump(), edit)


@router.post("/setups/{setup_id}/generate", status_code=202)
def generate_setup(
    setup_id: str,
    data: GenerateInput,
    request: Request,
    session_factory: SessionFactory,
    idempotency_key: str = ActionKey,
):
    require_role(request, {"owner", "editor"})
    with session_factory.begin() as db:

        def generate(actor):
            setup = document(db, setup_id, "setup", lock=True)
            revision(setup, data.expectedRevision)
            saved = json.loads(setup.data_json)
            if saved.get("contentId"):
                raise HTTPException(
                    409, "Outputs already exist; continue or retry the existing jobs"
                )
            if sorted(data.confirmedFormats) != sorted(saved["formats"]):
                raise HTTPException(422, "Confirm the saved output formats")
            caps = capabilities()
            if data.capabilityRevision != caps["revision"]:
                raise HTTPException(
                    409, "Provider configuration changed; refresh the generation review"
                )
            if (
                "reel" in saved["formats"]
                and saved["options"]["subtitles"]
                and not caps["subtitlesSupported"]
            ):
                raise HTTPException(
                    409,
                    "The worker needs FFmpeg libass subtitle support for this Reel; use the documented worker image",
                )
            for format in saved["formats"]:
                if not caps["formats"][format]["configured"]:
                    raise HTTPException(
                        409,
                        {
                            "message": "Generation is unavailable",
                            "issues": caps["formats"][format]["issues"],
                        },
                    )
            source = topic_packet(db, saved["topicId"])
            topic = db.get(Topic, saved["topicId"])
            if "carousel" in saved["formats"] and (topic.post_id or topic.job_id):
                raise HTTPException(
                    409,
                    "This source already has a carousel or an active topic job; continue that draft",
                )
            content = create_document(
                db,
                kind="content",
                actor=actor,
                data={
                    "title": source["title"],
                    "topicId": source["id"],
                    "source": source,
                    "setupId": setup.id,
                },
            )
            outputs, jobs = [], []
            for format in saved["formats"]:
                output = create_document(
                    db,
                    kind="output",
                    parent_id=content.id,
                    actor=actor,
                    data={
                        "format": format,
                        "source": source,
                        "options": saved["options"],
                        "scenes": [],
                        "caption": "",
                        "voiceId": saved["options"]["voiceId"],
                        "subtitles": saved["options"]["subtitles"],
                        "stage": "queued",
                        "budgetRemaining": 0,
                    },
                )
                queued = queue_output(db, output, actor, budget=data.confirmedBudget)
                outputs.append(output.id)
                jobs.append(queued["jobId"])
                if format == "carousel":
                    topic.status, topic.job_id = "generating", queued["jobId"]
            saved["contentId"] = content.id
            save_document(
                db,
                setup.id,
                revision=setup.revision,
                data=saved,
                actor=actor,
                reason="Generation authorized",
            )
            return {"contentId": content.id, "outputIds": outputs, "jobIds": jobs}

        return mutation(db, request, idempotency_key, data.model_dump(), generate)


def content_view(db, row):
    result = view(row)
    result["outputs"] = [
        output_view(db, output)
        for output in db.query(StudioDocument)
        .filter_by(parent_id=row.id, kind="output", deleted_at=None)
        .all()
    ]
    return result


def output_view(db, row):
    result = view(row)
    data = result["data"]
    jobs = db.query(Job).filter(Job.kind == "studio_output").order_by(Job.created_at.desc()).all()
    job = next(
        (item for item in jobs if json.loads(item.payload_json).get("output_id") == row.id), None
    )
    if job:
        from devai.services.jobs import serialise_job

        result["job"] = serialise_job(job)
    if data.get("format") == "reel":
        for scene in data.get("scenes", []):
            scene["imageCurrent"] = bool(
                scene.get("imageAssetId") and scene.get("imageHash") == scene_visual_hash(scene)
            )
            scene["audioCurrent"] = bool(
                scene.get("audioAssetId")
                and scene.get("audioHash") == digest([scene["script"], data["voiceId"]])
            )
        data["renderCurrent"] = bool(
            data.get("renderId")
            and data.get("renderHash") == timeline_hash(json.loads(row.data_json))
        )
    if data.get("format") == "carousel" and data.get("postId"):
        post = db.get(Post, data["postId"])
        data["approvalCurrent"] = bool(
            post and data.get("approval", {}).get("postVersion") == post.version
        )
    return result


@router.get("/content")
def list_content(session_factory: SessionFactory, q: str = "", status: str = "", before: str = ""):
    with session_factory() as db:
        query = db.query(StudioDocument).filter_by(kind="content", deleted_at=None)
        if q:
            query = query.filter(StudioDocument.data_json.ilike(f"%{q[:100]}%"))
        if status:
            query = query.filter_by(state=status)
        if before:
            previous = document(db, before, "content")
            query = query.filter(StudioDocument.created_at < previous.created_at)
        rows = query.order_by(StudioDocument.created_at.desc()).limit(25).all()
        return {
            "items": [content_view(db, row) for row in rows[:24]],
            "nextCursor": rows[23].id if len(rows) > 24 else None,
        }


@router.get("/content/{content_id}")
def get_content(content_id: str, session_factory: SessionFactory):
    with session_factory() as db:
        return content_view(db, document(db, content_id, "content"))


@router.get("/outputs/{output_id}")
@router.get("/outputs/{output_id}/timeline")
def get_output(output_id: str, session_factory: SessionFactory):
    with session_factory() as db:
        return output_view(db, document(db, output_id, "output"))


@router.patch("/outputs/{output_id}/timeline")
def edit_timeline(
    output_id: str,
    data: TimelineInput,
    request: Request,
    session_factory: SessionFactory,
    idempotency_key: str = ActionKey,
):
    require_role(request, {"owner", "editor"})
    with session_factory.begin() as db:

        def edit(actor):
            row = document(db, output_id, "output", lock=True)
            revision(row, data.expectedRevision)
            idle(db, row)
            saved = json.loads(row.data_json)
            if saved["format"] != "reel":
                raise HTTPException(422, "Only Reels have a timeline")
            if saved["source"]["url"] not in data.caption:
                raise HTTPException(422, "Retain the exact source citation in the caption")
            caption = data.caption
            if data.voiceId and "AI-generated" not in caption:
                caption += "\nVoice: AI-generated narration."
                if len(caption) > 2200:
                    raise HTTPException(
                        422, "Shorten the caption to retain the AI narration disclosure"
                    )
            if data.musicAssetId:
                _, music, _ = asset_bytes(db, data.musicAssetId, output_id=output_id)
                if not (
                    music.get("uploadedMusic")
                    and music.get("license", {}).get("acknowledged")
                    and music.get("validation", {}).get("passed")
                ):
                    raise HTTPException(422, "Choose decoded audio with recorded usage rights")
            old = {scene["id"]: scene for scene in saved["scenes"]}
            saved["scenes"] = [
                {**old.get(scene.id, {}), **scene.model_dump()} for scene in data.scenes
            ]
            saved.update(
                caption=caption,
                voiceId=data.voiceId,
                subtitles=data.subtitles,
                subtitleStyle=data.subtitleStyle.model_dump() if data.subtitleStyle else None,
                subtitleCues=(
                    [
                        {**cue.model_dump(), "id": cue.id or uuid.uuid4().hex}
                        for cue in data.subtitleCues
                    ]
                    if data.subtitleCues is not None
                    else None
                ),
                stage="needs_render",
                musicAssetId=data.musicAssetId,
                voiceGainDb=data.voiceGainDb,
                musicGainDb=data.musicGainDb,
                ducking=data.ducking,
            )
            saved.pop("approval", None)
            saved.pop("grounding", None)
            return output_view(
                db,
                save_document(
                    db, row.id, revision=row.revision, data=saved, actor=actor, state="draft"
                ),
            )

        return mutation(db, request, idempotency_key, data.model_dump(), edit)


@router.post("/outputs/{output_id}/scenes/{scene_id}/generate", status_code=202)
def scene_action(
    output_id: str,
    scene_id: str,
    data: OutputAction,
    request: Request,
    session_factory: SessionFactory,
    idempotency_key: str = ActionKey,
):
    require_role(request, {"owner", "editor"})
    with session_factory.begin() as db:

        def queue(actor):
            row = document(db, output_id, "output", lock=True)
            revision(row, data.expectedRevision)
            if not any(
                scene["id"] == scene_id for scene in json.loads(row.data_json).get("scenes", [])
            ):
                raise HTTPException(404, "Scene not found")
            if not data.confirmedBudget:
                raise HTTPException(422, "Confirm a provider-request budget")
            return queue_output(
                db, row, actor, action="scene", budget=data.confirmedBudget, unit_id=scene_id
            )

        return mutation(db, request, idempotency_key, data.model_dump(), queue)


@router.post("/outputs/{output_id}/review/{action}")
def review_output(
    output_id: str,
    action: str,
    data: ReviewInput,
    request: Request,
    session_factory: SessionFactory,
    idempotency_key: str = ActionKey,
):
    require_role(request, {"owner", "reviewer"} if action == "approve" else {"owner", "editor"})
    if action not in {"submit", "approve"}:
        raise HTTPException(404, "Unknown review action")
    with session_factory.begin() as db:

        def review(actor):
            row = document(db, output_id, "output", lock=True)
            revision(row, data.expectedRevision)
            idle(db, row)
            saved = json.loads(row.data_json)
            topic = topic_packet(db, saved["source"]["id"])
            if topic["fingerprint"] != saved["source"]["fingerprint"]:
                raise HTTPException(
                    409, "Source evidence changed; regenerate and review this output"
                )
            hashes = current_assets(db, row)
            if set(data.reviewedAssetIds) != set(hashes):
                raise HTTPException(422, "Inspect every current asset before review")
            if action == "approve" and row.state != "pending_review":
                raise HTTPException(409, "Submit the current output for review first")
            approval = {
                "id": uuid.uuid4().hex,
                "actorId": actor,
                "approvedAt": datetime.now(UTC).isoformat(),
                "revision": row.revision + 1,
                "assetHashes": hashes,
                "captionHash": digest(saved.get("caption")),
                "evidenceHash": topic["fingerprint"],
                "contentHash": timeline_hash(saved),
            }
            if saved.get("postId"):
                post = db.get(Post, saved["postId"])
                approval["postVersion"] = post.version
                if action == "approve":
                    post.status = "approved"
            saved["approval" if action == "approve" else "submission"] = approval
            return output_view(
                db,
                save_document(
                    db,
                    row.id,
                    revision=row.revision,
                    data=saved,
                    actor=actor,
                    reason=f"Review {action}",
                    state="approved" if action == "approve" else "pending_review",
                ),
            )

        return mutation(db, request, idempotency_key, data.model_dump(), review)


@router.post("/outputs/{output_id}/changes")
def request_changes(
    output_id: str,
    data: ChangesInput,
    request: Request,
    session_factory: SessionFactory,
    idempotency_key: str = ActionKey,
):
    require_role(request, {"owner", "reviewer"})
    with session_factory.begin() as db:

        def change(actor):
            row = document(db, output_id, "output", lock=True)
            revision(row, data.expectedRevision)
            idle(db, row)
            saved = json.loads(row.data_json)
            saved.pop("approval", None)
            saved.setdefault("revisionRequests", []).append(
                {"actorId": actor, "notes": data.notes, "revision": row.revision}
            )
            return output_view(
                db,
                save_document(
                    db,
                    row.id,
                    revision=row.revision,
                    data=saved,
                    actor=actor,
                    reason="Revision requested",
                    state="changes_requested",
                ),
            )

        return mutation(db, request, idempotency_key, data.model_dump(), change)


@router.get("/outputs/{output_id}/versions")
def output_versions(output_id: str, session_factory: SessionFactory):
    with session_factory() as db:
        document(db, output_id, "output")
        rows = (
            db.query(StudioVersion)
            .filter_by(document_id=output_id)
            .order_by(StudioVersion.revision.desc())
            .limit(100)
            .all()
        )
        return {
            "items": [
                {
                    "revision": row.revision,
                    "state": row.state,
                    "reason": row.reason,
                    "createdAt": row.created_at,
                    "data": public(json.loads(row.data_json)),
                }
                for row in rows
            ]
        }


@router.post("/outputs/{output_id}/versions/restore")
def restore_output(
    output_id: str,
    data: RestoreInput,
    request: Request,
    session_factory: SessionFactory,
    idempotency_key: str = ActionKey,
):
    require_role(request, {"owner", "editor"})
    with session_factory.begin() as db:

        def restore(actor):
            row = document(db, output_id, "output", lock=True)
            revision(row, data.expectedRevision)
            idle(db, row)
            current = json.loads(row.data_json)
            if current["format"] != "reel":
                raise HTTPException(422, "Restore carousel versions in the carousel editor")
            target = (
                db.query(StudioVersion)
                .filter_by(document_id=output_id, revision=data.targetRevision)
                .first()
            )
            if not target:
                raise HTTPException(404, "Version not found")
            saved = json.loads(target.data_json)
            source = topic_packet(db, current["source"]["id"])
            if saved["source"]["fingerprint"] != source["fingerprint"]:
                raise HTTPException(409, "Source evidence changed; review the current source first")
            # Restoring creative work never restores paid authorization or an old approval.
            for name in ("budgetRemaining", "providerRequests", "revisionRequests"):
                if name in current:
                    saved[name] = current[name]
            saved.pop("approval", None)
            return output_view(
                db,
                save_document(
                    db,
                    row.id,
                    revision=row.revision,
                    data=saved,
                    actor=actor,
                    state="draft",
                    reason=f"Restored revision {data.targetRevision}",
                ),
            )

        return mutation(db, request, idempotency_key, data.model_dump(), restore)


@router.get("/assets/{asset_id}")
def private_asset(asset_id: str, session_factory: SessionFactory):
    with session_factory() as db:
        _, data, _ = asset_bytes(db, asset_id)
        return FileResponse(
            data["privatePath"],
            media_type={"image": "image/png", "audio": "audio/wav", "video": "video/mp4"}[
                data["kind"]
            ],
            headers={"Cache-Control": "private, no-store"},
        )


@router.get("/outputs/{output_id}/export")
def export_output(output_id: str, session_factory: SessionFactory):
    with session_factory() as db:
        output = document(db, output_id, "output")
        saved = json.loads(output.data_json)
        current_assets(db, output)
        if saved["format"] == "carousel":
            from devai.routes.exports import export_post

            return export_post(saved["postId"], session_factory)
        _, _, raw = asset_bytes(db, saved["renderId"], output_id=output.id)
        stream = BytesIO()
        with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("reel.mp4", raw)
            archive.writestr("caption.txt", saved["caption"])
            archive.writestr("editorial.json", json.dumps(public(saved), indent=2))
        return Response(
            stream.getvalue(),
            media_type="application/zip",
            headers={
                "Content-Disposition": 'attachment; filename="devai-reel.zip"',
                "Cache-Control": "no-store",
            },
        )


@router.post("/outputs/{output_id}/{action}", status_code=202)
def output_action(
    output_id: str,
    action: str,
    data: OutputAction,
    request: Request,
    session_factory: SessionFactory,
    idempotency_key: str = ActionKey,
):
    if action not in {"render", "voiceover", "generate", "grounding", "sync"}:
        raise HTTPException(404, "Unknown output action")
    require_role(request, {"owner", "editor"})
    with session_factory.begin() as db:

        def queue(actor):
            row = document(db, output_id, "output", lock=True)
            revision(row, data.expectedRevision)
            if action == "sync":
                idle(db, row)
                saved = json.loads(row.data_json)
                post = db.get(Post, saved.get("postId"))
                if not post:
                    raise HTTPException(409, "Generate the carousel first")
                saved.update(caption=post.caption, postVersion=post.version)
                saved.pop("approval", None)
                return output_view(
                    db,
                    save_document(
                        db,
                        row.id,
                        revision=row.revision,
                        data=saved,
                        actor=actor,
                        state="draft",
                        reason="Carousel synchronized",
                    ),
                )
            if action in {"generate", "voiceover", "grounding"} and not data.confirmedBudget:
                raise HTTPException(422, "Confirm an additional provider-request budget")
            return queue_output(db, row, actor, action=action, budget=data.confirmedBudget)

        return mutation(db, request, idempotency_key, data.model_dump(), queue)
