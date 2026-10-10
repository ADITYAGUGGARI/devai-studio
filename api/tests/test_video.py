"""Actual local codec acceptance; synthetic media is confined to these tests."""

import os
import shutil
import sys

import pytest
from PIL import Image

from devai.services.jobs import JobCancelled
from devai.services.video import binary, execute, render_video, validate_mp4


def test_cancelled_media_process_is_reaped_and_preserves_previous_output(tmp_path):
    pid_file = tmp_path / "child.pid"
    previous = tmp_path / "previous.mp4"
    previous.write_bytes(b"previous successful asset")

    def checkpoint():
        if pid_file.exists():
            raise JobCancelled()

    with pytest.raises(JobCancelled):
        execute(
            [
                sys.executable,
                "-c",
                "import os,sys,time; open(sys.argv[1], 'w').write(str(os.getpid())); time.sleep(60)",
                str(pid_file),
            ],
            timeout=5,
            checkpoint=checkpoint,
        )
    with pytest.raises(ProcessLookupError):
        os.kill(int(pid_file.read_text()), 0)
    assert previous.read_bytes() == b"previous successful asset"


def test_media_timeout_reaps_running_process(tmp_path):
    pid_file = tmp_path / "child.pid"
    with pytest.raises(ValueError, match="timed out"):
        execute(
            [
                sys.executable,
                "-c",
                "import os,sys,time; open(sys.argv[1], 'w').write(str(os.getpid())); time.sleep(60)",
                str(pid_file),
            ],
            timeout=0.5,
            checkpoint=lambda: None,
        )
    with pytest.raises(ProcessLookupError):
        os.kill(int(pid_file.read_text()), 0)


def test_missing_configured_codec_has_actionable_error(monkeypatch):
    monkeypatch.setenv("FFMPEG_BIN", "/definitely/unavailable/devai-ffmpeg")
    with pytest.raises(ValueError, match="unavailable on the worker"):
        binary("ffmpeg")


def test_rejected_video_reports_actual_dimensions(monkeypatch):
    monkeypatch.setattr(
        "devai.services.video.probe",
        lambda _: {
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 640,
                    "height": 360,
                    "avg_frame_rate": "30/1",
                }
            ],
            "format": {"duration": "35", "format_name": "mov,mp4"},
        },
    )
    report = validate_mp4("test-only-fixture", require_audio=False)
    assert not report["passed"]
    assert (report["width"], report["height"]) == (640, 360)


@pytest.mark.skipif(
    not (os.getenv("FFMPEG_BIN") or shutil.which("ffmpeg")),
    reason="FFmpeg codec integration requires the worker media dependency",
)
def test_real_vertical_mp4_is_decodable_and_preserved_on_failure(tmp_path):
    image = tmp_path / "fixture.png"
    Image.new("RGB", (1080, 1920), (40, 70, 60)).save(image)
    progress = []
    result = render_video(
        [{"image_path": str(image), "duration": 7} for _ in range(5)],
        audio_path=None,
        output_directory=tmp_path,
        progress=lambda done, total, stage: progress.append((done, total, stage)),
    )
    assert result["validation"]["passed"]
    assert result["validation"]["decoded"]
    assert 34.9 <= result["validation"]["duration_seconds"] <= 35.1
    assert validate_mp4(result["path"], require_audio=True)["passed"] is False
    saved_bytes = open(result["path"], "rb").read()
    with pytest.raises(ValueError, match="available image"):
        render_video(
            [{"image_path": str(tmp_path / "missing.png"), "duration": 7} for _ in range(5)],
            audio_path=None,
            output_directory=tmp_path,
            progress=lambda *args: None,
        )
    assert open(result["path"], "rb").read() == saved_bytes
    assert progress[-1] == (7, 7, "MP4 validated")


def test_invalid_timeline_fails_before_creating_assets(tmp_path):
    with pytest.raises(ValueError, match="30–40"):
        render_video(
            [{"image_path": "missing", "duration": 10}],
            audio_path=None,
            output_directory=tmp_path,
            progress=lambda *args: None,
        )
    assert list(tmp_path.iterdir()) == []
