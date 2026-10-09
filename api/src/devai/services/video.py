"""Actual MP4 assembly and decode validation; scene collections are never videos."""

import json
import os
import platform
import shutil
import subprocess
import uuid
from fractions import Fraction
from pathlib import Path


def binary(name):
    configured = os.getenv(name.upper() + "_BIN")
    path = configured or shutil.which(name)
    if not path:
        raise ValueError(f"{name} is unavailable on the worker; install FFmpeg before rendering")
    return path


def execute(arguments, *, timeout=240):
    try:
        result = subprocess.run(arguments, capture_output=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        raise ValueError("Video processing timed out; previous renders are preserved") from exc
    if result.returncode:
        # FFmpeg stderr includes private paths; do not return it to clients.
        raise ValueError("Video processing failed; check worker codec support and media inputs")
    return result.stdout


def probe(path):
    return json.loads(
        execute(
            [
                binary("ffprobe"),
                "-v",
                "error",
                "-show_streams",
                "-show_format",
                "-of",
                "json",
                str(path),
            ]
        )
    )


def validate_mp4(path, *, require_audio=True):
    report = probe(path)
    streams = report.get("streams", [])
    videos = [item for item in streams if item.get("codec_type") == "video"]
    audios = [item for item in streams if item.get("codec_type") == "audio"]
    duration = float(report.get("format", {}).get("duration", 0))
    issues = []
    if len(videos) != 1:
        issues.append("One video stream is required")
    else:
        video = videos[0]
        if video.get("codec_name") != "h264" or (video.get("width"), video.get("height")) != (
            1080,
            1920,
        ):
            issues.append("Video must be H.264 at 1080 × 1920")
        if Fraction(video.get("avg_frame_rate", "0/1")) != 30:
            issues.append("Video must run at 30 frames per second")
        if int(video.get("bit_rate", 0)) > 25_000_000:
            issues.append("Video bitrate exceeds 25 Mbps")
    if not 30 <= duration <= 40.1:
        issues.append("Video duration must be 30–40 seconds")
    if require_audio and not audios:
        issues.append("Configured narration is missing")
    for audio in audios:
        if audio.get("codec_name") != "aac" or int(audio.get("sample_rate", 0)) != 48000:
            issues.append("Audio must be AAC at 48 kHz")
    if "mp4" not in report.get("format", {}).get("format_name", ""):
        issues.append("A valid MP4 container is required")
    if not issues:
        execute(
            [binary("ffmpeg"), "-nostdin", "-v", "error", "-i", str(path), "-f", "null", "-"],
            timeout=120,
        )
    return {
        "passed": not issues,
        "issues": issues,
        "duration_seconds": duration,
        "width": 1080 if videos else None,
        "height": 1920 if videos else None,
        "decoded": not issues,
        "audio_present": bool(audios),
    }


def render_video(scenes, *, audio_path, output_directory, progress):
    if not scenes or not 30 <= sum(scene["duration"] for scene in scenes) <= 40:
        raise ValueError("Scene durations must total 30–40 seconds")
    directory = Path(output_directory) / str(uuid.uuid4())
    directory.mkdir(parents=True, exist_ok=False)
    ffmpeg = binary("ffmpeg")
    codec = os.getenv(
        "REEL_VIDEO_ENCODER", "h264_videotoolbox" if platform.system() == "Darwin" else "libx264"
    ) or ("h264_videotoolbox" if platform.system() == "Darwin" else "libx264")
    if codec not in {"libx264", "h264_videotoolbox"}:
        raise ValueError("Unsupported worker H.264 encoder")
    parts = []
    for index, scene in enumerate(scenes):
        progress(index, len(scenes) + 2, f"Rendering scene {index + 1}")
        image = Path(scene["image_path"])
        if not image.is_file() or not 1 <= scene["duration"] <= 15:
            raise ValueError("Every scene needs an available image and a duration of 1–15 seconds")
        target = directory / f"scene-{index:02}.mp4"
        execute(
            [
                ffmpeg,
                "-nostdin",
                "-v",
                "error",
                "-loop",
                "1",
                "-i",
                str(image),
                "-t",
                str(scene["duration"]),
                "-vf",
                "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1",
                "-r",
                "30",
                "-c:v",
                codec,
                "-b:v",
                "6M",
                "-pix_fmt",
                "yuv420p",
                "-an",
                str(target),
            ]
        )
        parts.append(target)
    manifest = directory / "scenes.ffconcat"
    manifest.write_text(
        "ffconcat version 1.0\n" + "".join(f"file '{part.name}'\n" for part in parts)
    )
    progress(len(scenes), len(scenes) + 2, "Assembling MP4")
    target = directory / "reel.mp4"
    command = [ffmpeg, "-nostdin", "-v", "error", "-f", "concat", "-safe", "1", "-i", str(manifest)]
    if audio_path is not None:
        if not Path(audio_path).is_file():
            raise ValueError("Narration audio is unavailable; regenerate it before rendering")
        audio_duration = float(probe(audio_path).get("format", {}).get("duration", 0))
        if audio_duration > sum(scene["duration"] for scene in scenes) + 0.05:
            raise ValueError(
                "Narration exceeds the scene timeline; shorten the script or extend scenes before rendering"
            )
        command += [
            "-i",
            str(audio_path),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-af",
            "apad,loudnorm=I=-16:TP=-1:LRA=11",
            "-c:a",
            "aac",
            "-ar",
            "48000",
            "-b:a",
            "128k",
        ]
    command += [
        "-c:v",
        "copy",
        "-t",
        str(sum(scene["duration"] for scene in scenes)),
        "-movflags",
        "+faststart",
        str(target),
    ]
    execute(command)
    progress(len(scenes) + 1, len(scenes) + 2, "Validating video and audio")
    report = validate_mp4(target, require_audio=audio_path is not None)
    if not report["passed"]:
        raise ValueError("Rendered MP4 failed validation: " + "; ".join(report["issues"]))
    progress(len(scenes) + 2, len(scenes) + 2, "MP4 validated")
    return {"path": str(target), "validation": report}
