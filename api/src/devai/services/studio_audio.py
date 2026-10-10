"""Real licensed audio decode and mixing. No provider calls or fabricated media."""

import hashlib
import json
import os
import uuid
from pathlib import Path

from devai.models import Job
from devai.services.jobs import JobCancelled, safe_error
from devai.services.studio_content import asset, document
from devai.services.studio_documents import save_document
from devai.services.video import binary, execute


def validate_audio(path, directory, checkpoint):
    metadata = json.loads(
        execute(
            [
                binary("ffprobe"),
                "-v",
                "error",
                "-protocol_whitelist",
                "file,pipe",
                "-show_streams",
                "-show_format",
                "-of",
                "json",
                str(path),
            ],
            timeout=30,
            checkpoint=checkpoint,
        )
    )
    streams = metadata.get("streams", [])
    duration = float(metadata.get("format", {}).get("duration", 0))
    formats = set(metadata.get("format", {}).get("format_name", "").split(","))
    if not formats.intersection({"wav", "mp3", "mov", "mp4", "m4a"}):
        raise ValueError("The actual file must be WAV, MP3 or M4A audio")
    if len(streams) != 1 or streams[0].get("codec_type") != "audio" or not 0 < duration <= 3600:
        raise ValueError("Upload a single audio track with a readable duration of at most one hour")
    # Validate the entire uploaded track before making even its trimmed version available.
    execute(
        [
            binary("ffmpeg"),
            "-nostdin",
            "-v",
            "error",
            "-protocol_whitelist",
            "file,pipe",
            "-i",
            str(path),
            "-f",
            "null",
            "-",
        ],
        timeout=180,
        checkpoint=checkpoint,
    )
    target = Path(directory) / f"{uuid.uuid4().hex}.wav"
    try:
        execute(
            [
                binary("ffmpeg"),
                "-nostdin",
                "-v",
                "error",
                "-protocol_whitelist",
                "file,pipe",
                "-i",
                str(path),
                "-t",
                "40",
                "-ac",
                "2",
                "-ar",
                "48000",
                "-c:a",
                "pcm_s16le",
                str(target),
            ],
            timeout=90,
            checkpoint=checkpoint,
        )
    except Exception:
        target.unlink(missing_ok=True)
        raise
    return target, {
        "passed": True,
        "decoded": True,
        "duration_seconds": min(duration, 40),
        "original_duration_seconds": duration,
        "trimmed": duration > 40,
    }


def run_upload(factory, claim, progress):
    identifier = claim["payload"]["upload_id"]
    with factory() as db:
        row = document(db, identifier, "audio_upload")
        data = json.loads(row.data_json)
        parent_id = row.parent_id
        if data.get("assetId"):
            return {"asset_id": data["assetId"], "upload_id": identifier}
    path = Path(data["privatePath"])
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != data["sha256"]:
        raise ValueError("Uploaded bytes failed integrity validation; upload the file again")

    def checkpoint():
        progress(0, 2, "Decoding uploaded audio")

    root = Path(os.getenv("STUDIO_MEDIA_DIR", ".local-data/studio-media")) / parent_id
    result = None
    try:
        result, report = validate_audio(path, root, checkpoint)
        with factory.begin() as db:
            job = db.get(Job, claim["id"])
            if job.status != "running" or job.lease_token != claim["token"]:
                raise RuntimeError("Worker lost its upload lease")
            row = document(db, identifier, "audio_upload", lock=True)
            data = json.loads(row.data_json)
            asset_id = asset(
                db,
                parent_id,
                result.read_bytes(),
                kind="audio",
                validation=report,
                content_hash=data["sha256"],
            )
            saved_asset = document(db, asset_id, "asset")
            asset_data = json.loads(saved_asset.data_json)
            asset_data.update(
                license=data["license"], fileName=data["fileName"], uploadedMusic=True
            )
            save_document(
                db,
                asset_id,
                revision=saved_asset.revision,
                data=asset_data,
                actor="worker",
                state="validated",
            )
            data.update(assetId=asset_id, validation=report)
            save_document(
                db, row.id, revision=row.revision, data=data, actor="worker", state="validated"
            )
        progress(2, 2, "Licensed audio validated")
        return {"asset_id": asset_id, "upload_id": identifier}
    except Exception as exc:
        with factory.begin() as db:
            job = db.get(Job, claim["id"])
            if job.status == "running" and job.lease_token == claim["token"]:
                row = document(db, identifier, "audio_upload", lock=True)
                data = json.loads(row.data_json)
                if not data.get("assetId"):
                    data["validationFailure"] = safe_error(exc)
                    save_document(
                        db,
                        row.id,
                        revision=row.revision,
                        data=data,
                        actor="worker",
                        state="cancelled" if isinstance(exc, JobCancelled) else "validation_failed",
                    )
        raise
    finally:
        if result:
            result.unlink(missing_ok=True)


def mix_audio(
    voice_path, music_path, *, duration, voice_gain, music_gain, ducking, directory, checkpoint
):
    target = Path(directory) / f"{uuid.uuid4().hex}-mix.wav"
    args = [binary("ffmpeg"), "-nostdin", "-v", "error"]
    if voice_path:
        args += ["-i", str(voice_path)]
    args += ["-stream_loop", "-1", "-i", str(music_path)]
    music_index = 1 if voice_path else 0
    filters = [f"[{music_index}:a]volume={10 ** (music_gain / 20)}[music]"]
    if voice_path:
        filters += [
            f"[0:a]volume={10 ** (voice_gain / 20)},apad=whole_dur={duration},asplit=2[voice][side]"
        ]
        if ducking:
            filters += [
                "[music][side]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=250[bed]"
            ]
        else:
            filters += ["[side]anullsink", "[music]anull[bed]"]
        filters += [
            "[voice][bed]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95[out]"
        ]
    else:
        filters += ["[music]alimiter=limit=0.95[out]"]
    args += [
        "-filter_complex",
        ";".join(filters),
        "-map",
        "[out]",
        "-t",
        str(duration),
        "-ac",
        "2",
        "-ar",
        "48000",
        "-c:a",
        "pcm_s16le",
        str(target),
    ]
    execute(args, timeout=90, checkpoint=checkpoint)
    return target


def gain_audio(path, gain, directory, checkpoint):
    target = Path(directory) / f"{uuid.uuid4().hex}-gain.wav"
    execute(
        [
            binary("ffmpeg"),
            "-nostdin",
            "-v",
            "error",
            "-i",
            str(path),
            "-af",
            f"volume={10 ** (gain / 20)},alimiter=limit=0.95",
            "-c:a",
            "pcm_s16le",
            str(target),
        ],
        timeout=90,
        checkpoint=checkpoint,
    )
    return target
