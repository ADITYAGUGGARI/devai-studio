"""Actual MP4 assembly and decode validation; scene collections are never videos."""

import json
import os
import platform
import shutil
import subprocess
import time
import uuid
from fractions import Fraction
from pathlib import Path


def binary(name):
    configured = os.getenv(name.upper() + "_BIN")
    path = configured or shutil.which(name)
    if not path or not shutil.which(path):
        raise ValueError(f"{name} is unavailable on the worker; install FFmpeg before rendering")
    return path


def execute(arguments, *, timeout=240, checkpoint=None):
    if checkpoint is not None:
        checkpoint()
        started = time.monotonic()
        with subprocess.Popen(arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
            try:
                while True:
                    remaining = timeout - (time.monotonic() - started)
                    if remaining <= 0:
                        raise ValueError(
                            "Video processing timed out; previous renders are preserved"
                        )
                    try:
                        output, _ = process.communicate(timeout=min(1, remaining))
                        break
                    except subprocess.TimeoutExpired:
                        checkpoint()
                if process.returncode:
                    raise ValueError(
                        "Video processing failed; check worker codec support and media inputs"
                    )
                checkpoint()
                return output
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.communicate(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.communicate()
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


def validate_mp4(path, *, require_audio=True, checkpoint=None):
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
            checkpoint=checkpoint,
        )
    return {
        "passed": not issues,
        "issues": issues,
        "duration_seconds": duration,
        "width": videos[0].get("width") if videos else None,
        "height": videos[0].get("height") if videos else None,
        "decoded": not issues,
        "audio_present": bool(audios),
    }


def subtitle_file(cues, directory):
    """ASS is video subtitle input, never carousel artwork composition. Preserve code operators."""

    def timestamp(value):
        centiseconds = round(value * 100)
        seconds, centiseconds = divmod(centiseconds, 100)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours}:{minutes:02}:{seconds:02}.{centiseconds:02}"

    rows, previous = [], 0
    for index, cue in enumerate(cues, 1):
        if not 0 <= cue["start"] < cue["end"] <= 40 or cue["start"] < previous:
            raise ValueError("Subtitles must be ordered and fit the 30–40 second timeline")
        text = str(cue["text"]).replace("\r", " ").replace("\n", " ").strip()
        if not text or len(text) > 1000:
            raise ValueError("Each subtitle needs readable text of1–1000characters")
        words, lines, line = text.split(), [], ""
        for word in words:
            if len(line + " " + word) > 36 and line:
                lines.append(line)
                line = word
            else:
                line = (line + " " + word).strip()
        if line:
            lines.append(line)
        chunks = [lines[position : position + 2] for position in range(0, len(lines), 2)]
        duration = (cue["end"] - cue["start"]) / len(chunks)
        for position, chunk in enumerate(chunks):
            literal = r"\N".join(chunk).replace("{", r"\{").replace("}", r"\}")
            rows.append(
                f"Dialogue: 0,{timestamp(cue['start'] + position * duration)},{timestamp(cue['start'] + (position + 1) * duration)},Default,,0,0,0,,{literal}"
            )
        previous = cue["end"]
    target = Path(directory) / "subtitles.ass"
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,52,&H00FFFFFF,&H00FFFFFF,&H00172A23,&H00172A23,0,0,0,0,100,100,0,0,1,3,0,2,80,80,280,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    target.write_text(header + "\n".join(rows) + "\n", encoding="utf-8")
    return target


def assemble_audio(scenes, output_directory, *, checkpoint=None):
    """Align narration to actual scene lengths; never truncate spoken content silently."""
    directory = Path(output_directory) / uuid.uuid4().hex
    directory.mkdir(parents=True, exist_ok=False)
    parts = []
    ffmpeg = binary("ffmpeg")
    for index, scene in enumerate(scenes):
        duration = float(probe(scene["path"]).get("format", {}).get("duration", 0))
        if not duration > 0 or not 1 <= scene["duration"] <= 15:
            raise ValueError("Narration and scene duration must be valid")
        factor = max(1, duration / scene["duration"])
        if factor > 1.25:
            raise ValueError(
                f"Scene {index + 1} narration is too long; shorten its script or extend its duration"
            )
        target = directory / f"audio-{index:02}.wav"
        execute(
            [
                ffmpeg,
                "-nostdin",
                "-v",
                "error",
                "-i",
                str(scene["path"]),
                "-af",
                f"atempo={factor},apad",
                "-t",
                str(scene["duration"]),
                "-ar",
                "48000",
                "-ac",
                "1",
                str(target),
            ],
            checkpoint=checkpoint,
        )
        parts.append(target)
    manifest = directory / "audio.ffconcat"
    manifest.write_text(
        "ffconcat version 1.0\n" + "".join(f"file '{part.name}'\n" for part in parts)
    )
    target = directory / "narration.wav"
    execute(
        [
            ffmpeg,
            "-nostdin",
            "-v",
            "error",
            "-f",
            "concat",
            "-safe",
            "1",
            "-i",
            str(manifest),
            "-c:a",
            "pcm_s16le",
            str(target),
        ],
        checkpoint=checkpoint,
    )
    return target


def render_video(
    scenes, *, audio_path, output_directory, progress, subtitle_cues=None, subtitle_style=None
):
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
            ],
            checkpoint=lambda: progress(index, len(scenes) + 2, f"Rendering scene {index + 1}"),
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
    if subtitle_cues:
        filters = execute([ffmpeg, "-hide_banner", "-filters"]).decode()
        if " subtitles " not in filters:
            raise ValueError(
                "This FFmpeg build lacks libass subtitle support; install the documented worker image"
            )
        subtitles = subtitle_file(subtitle_cues, directory)
        from devai.schemas.studio_content import SubtitleStyle

        style = SubtitleStyle.model_validate(subtitle_style or {}).model_dump()
        formatting = (
            f"FontName=DejaVu Sans,FontSize={style['fontSize']},PrimaryColour=&H00FFFFFF,"
            f"OutlineColour=&H00172A23,BackColour=&H00172A23,BorderStyle={3 if style['background'] else 1},"
            f"Bold={-1 if style['bold'] else 0},Outline=3,MarginL=80,MarginR=80,MarginV=280,"
            f"Alignment={5 if style['position'] == 'middle' else 2}"
        )
        # Paths are generated internally; reject characters with filtergraph meaning.
        if any(character in str(subtitles.resolve()) for character in "':[],;"):
            raise ValueError("Worker media directory contains unsupported subtitle-path characters")
        command += [
            "-vf",
            f"subtitles='{subtitles.resolve()}':force_style='{formatting}'",
            "-c:v",
            codec,
            "-b:v",
            "6M",
            "-pix_fmt",
            "yuv420p",
        ]
    else:
        command += ["-c:v", "copy"]
    command += [
        "-t",
        str(sum(scene["duration"] for scene in scenes)),
        "-movflags",
        "+faststart",
        str(target),
    ]
    execute(
        command,
        checkpoint=lambda: progress(len(scenes), len(scenes) + 2, "Assembling MP4"),
    )
    progress(len(scenes) + 1, len(scenes) + 2, "Validating video and audio")
    report = validate_mp4(
        target,
        require_audio=audio_path is not None,
        checkpoint=lambda: progress(len(scenes) + 1, len(scenes) + 2, "Validating video and audio"),
    )
    if not report["passed"]:
        raise ValueError("Rendered MP4 failed validation: " + "; ".join(report["issues"]))
    progress(len(scenes) + 2, len(scenes) + 2, "MP4 validated")
    return {"path": str(target), "validation": report}
