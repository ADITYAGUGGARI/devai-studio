"""Workspace-scoped content documents, asset integrity and version-bound reviews."""

import hashlib
import json
import os
import uuid
from pathlib import Path

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder

from devai.models import Job, Topic
from devai.models.studio import ActionReceipt, StudioDocument, Workspace
from devai.services.jobs import ACTIVE, insert_job
from devai.services.operations import approved_topic
from devai.services.studio_documents import create_document, save_document, snapshot


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def scene_visual_hash(scene):
    return digest({key: scene.get(key) for key in ("headline", "body", "visualDirection")})


def document(db, identifier, kind=None, *, lock=False):
    query = db.query(StudioDocument).filter_by(id=identifier, deleted_at=None)
    if kind:
        query = query.filter_by(kind=kind)
    row = (query.with_for_update() if lock else query).first()
    if not row:
        raise HTTPException(404, "Content not found in this studio")
    return row


def public(value):
    if isinstance(value, dict):
        return {
            key: public(item)
            for key, item in value.items()
            if key not in {"privatePath", "privateTokenHash"}
        }
    if isinstance(value, list):
        return [public(item) for item in value]
    return value


def view(row):
    return public(snapshot(row))


def mutation(db, request, key, payload, operation):
    actor = request.state.principal["id"]
    db.query(Workspace).filter_by(id=request.state.workspace_id).with_for_update().one()
    fingerprint = digest([request.url.path, payload])
    receipt = db.query(ActionReceipt).filter_by(actor_id=actor, action_key=key).first()
    if receipt:
        if receipt.request_hash != fingerprint:
            raise HTTPException(
                409,
                {
                    "code": "IDEMPOTENCY_MISMATCH",
                    "message": "Use a new action key for changed input",
                },
            )
        return json.loads(receipt.response_json)
    result = jsonable_encoder(operation(actor))
    db.add(
        ActionReceipt(
            id=uuid.uuid4().hex,
            actor_id=actor,
            action_key=key,
            request_hash=fingerprint,
            response_json=json.dumps(result),
        )
    )
    return result


def require_role(request, roles):
    if request.state.principal["workspace_role"] not in roles:
        raise HTTPException(403, "Your studio role does not permit this action")


def topic_packet(db, identifier):
    topic = db.get(Topic, identifier)
    if not topic:
        raise HTTPException(404, "Topic not found")
    if (
        topic.status == "archived"
        or not approved_topic(db, topic)
        or topic.verification not in {"primary_source", "human_verified"}
        or len(topic.excerpt.strip()) < 240
    ):
        raise HTTPException(
            409, "Verify the source and explicitly approve this topic before generation"
        )
    return {
        "id": topic.id,
        "title": topic.title,
        "url": topic.url,
        "source": topic.source,
        "excerpt": topic.excerpt,
        "category": topic.category,
        "publishedAt": topic.published_at.isoformat() if topic.published_at else None,
        "capturedAt": topic.retrieved_at.isoformat(),
        "fingerprint": digest([topic.url, topic.excerpt]),
    }


def capabilities():
    from devai.services.video import binary, execute

    media_issues = []
    for name in ("ffmpeg", "ffprobe"):
        try:
            binary(name)
        except ValueError as exc:
            media_issues.append(str(exc))
    subtitle_supported = False
    if not media_issues:
        try:
            subtitle_supported = (
                " subtitles " in execute([binary("ffmpeg"), "-hide_banner", "-filters"]).decode()
            )
        except ValueError as exc:
            media_issues.append(str(exc))
    configured = bool(os.getenv("OPENAI_API_KEY", "").strip())
    data = {
        "providerConfigured": configured,
        "providerLiveVerified": False,
        "formats": {
            "carousel": {
                "configured": configured,
                "issues": [] if configured else ["Configure a valid server-side OpenAI key"],
            },
            "reel": {
                "configured": configured and not media_issues,
                "issues": media_issues
                + ([] if configured else ["Configure a valid server-side OpenAI key"]),
            },
        },
        "budgetUnit": "provider requests",
        "defaultBudgetPerOutput": 64,
        "imageModel": os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2"),
        "speechModel": os.getenv("OPENAI_SPEECH_MODEL", "gpt-4o-mini-tts"),
        "subtitlesSupported": subtitle_supported,
    }
    return {**data, "revision": digest(data)}


def idle(db, output):
    jobs = db.query(Job).filter(Job.status.in_(ACTIVE), Job.kind == "studio_output").all()
    if any(json.loads(job.payload_json).get("output_id") == output.id for job in jobs):
        raise HTTPException(409, "This output has background work; wait or cancel before editing")


def revision(row, expected):
    if row.revision != expected:
        raise HTTPException(
            409,
            {
                "code": "revision_conflict",
                "message": "This output changed on another device; your edits are retained",
                "server": view(row),
            },
        )


def queue_output(db, output, actor, *, action="generate", budget=0, unit_id=None):
    idle(db, output)
    data = json.loads(output.data_json)
    data["budgetRemaining"] = data.get("budgetRemaining", 0) + budget
    data.pop("approval", None)
    output = save_document(
        db,
        output.id,
        revision=output.revision,
        data=data,
        actor=actor,
        reason=f"Authorized {action}",
        state="queued",
    )
    job = insert_job(
        db,
        "studio_output",
        {"output_id": output.id, "action": action, "unit_id": unit_id, "actor": actor},
        key=f"output:{output.id}",
    )
    return {"outputId": output.id, "jobId": job.id, "revision": output.revision}


def asset(db, output_id, raw, *, kind, validation, content_hash):
    identity = uuid.uuid4().hex
    extension = {"image": "png", "audio": "wav", "video": "mp4"}[kind]
    root = Path(os.getenv("STUDIO_MEDIA_DIR", ".local-data/studio-media")).resolve() / output_id
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{identity}.{extension}"
    path.write_bytes(raw)
    row = create_document(
        db,
        kind="asset",
        parent_id=output_id,
        actor="worker",
        data={
            "kind": kind,
            "privatePath": str(path),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "contentHash": content_hash,
            "validation": validation,
            "bytes": len(raw),
        },
        state="validated",
    )
    return row.id


def asset_bytes(db, identifier, *, output_id=None):
    row = document(db, identifier, "asset")
    if output_id and row.parent_id != output_id:
        raise HTTPException(404, "Asset not found")
    data = json.loads(row.data_json)
    path = Path(data["privatePath"]).resolve()
    root = Path(os.getenv("STUDIO_MEDIA_DIR", ".local-data/studio-media")).resolve()
    if not path.is_relative_to(root):
        raise HTTPException(409, "Saved asset has an invalid storage location")
    if not path.is_file():
        raise HTTPException(409, "Saved asset is unavailable; regenerate this unit")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != data["sha256"]:
        raise HTTPException(409, "Saved asset failed integrity validation; regenerate this unit")
    return row, data, raw


def current_assets(db, output):
    data = json.loads(output.data_json)
    if data.get("format") == "carousel":
        from devai.models import Post, Slide
        from devai.services.managed_publishing import validate_ready

        post = db.get(Post, data.get("postId"))
        if not post:
            raise HTTPException(409, "Generate this carousel first")
        if post.version != data.get("postVersion") or post.caption != data.get("caption"):
            raise HTTPException(
                409, "Carousel copy changed; synchronize this output before reviewing it"
            )
        try:
            validate_ready(db, post)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        return {
            slide.id: json.loads(slide.validation_json)["image_sha256"]
            for slide in db.query(Slide).filter_by(post_id=post.id).all()
        }
    if not data.get("grounding", {}).get("supported"):
        raise HTTPException(409, "Current script and caption need source grounding")
    if data.get("voiceId") and "AI-generated" not in data.get("caption", ""):
        raise HTTPException(409, "Add the AI-generated narration disclosure before review")
    render_id = data.get("renderId")
    if not render_id or data.get("renderHash") != timeline_hash(data):
        raise HTTPException(409, "Render and validate the current timeline before review")
    row, saved, _ = asset_bytes(db, render_id, output_id=output.id)
    if not saved["validation"].get("passed"):
        raise HTTPException(409, "Rendered MP4 has not passed validation")
    return {row.id: saved["sha256"]}


def timeline_hash(data):
    payload = {
        key: data.get(key)
        for key in ("scenes", "caption", "voiceId", "subtitles", "music", "source")
    }
    # Preserve existing validated hashes when subtitles still follow the script.
    if data.get("subtitleCues") is not None:
        payload["subtitleCues"] = data["subtitleCues"]
    if data.get("subtitleStyle") is not None:
        payload["subtitleStyle"] = data["subtitleStyle"]
    if data.get("musicAssetId") or data.get("voiceGainDb", 0) != 0:
        payload["audioMix"] = {
            "musicAssetId": data.get("musicAssetId"),
            "voiceGainDb": data.get("voiceGainDb", 0),
            "musicGainDb": data.get("musicGainDb", -18),
            "ducking": data.get("ducking", True),
        }
    return digest(payload)
