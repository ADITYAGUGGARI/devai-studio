"""Isolated codec acceptance: synthetic source media, real production assembly."""

import json
import os
import shutil
import sys
import tempfile
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api" / "src"))
from devai.services.video import assemble_audio, binary, execute, render_video
from PIL import Image

with tempfile.TemporaryDirectory(prefix="devai-codec-") as temporary:
    root = Path(temporary)
    still = root / "test-only-still.png"
    Image.new("RGB", (1080, 1920), "#183e32").save(still)
    voice = root / "test-only-audio.wav"
    with wave.open(str(voice), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(48000)
        output.writeframes(bytes(48000 * 2 * 2))
    narration = assemble_audio([{"path": voice, "duration": 7}] * 5, root)
    scenes = [{"image_path": still, "duration": 7}] * 5
    cues = [
        {
            "start": i * 7,
            "end": (i + 1) * 7,
            "text": f"Isolated codec acceptance scene {i + 1}. Readable burned-in subtitles.",
        }
        for i in range(5)
    ]
    result = render_video(
        scenes,
        audio_path=narration,
        output_directory=root,
        progress=lambda *args: None,
        subtitle_cues=cues,
    )
    path, report = Path(result["path"]), result["validation"]
    assert report["passed"] and report["decoded"] and report["audio_present"], report
    assert path.is_file()
    evidence_directory = os.getenv("VERIFY_MEDIA_OUTPUT_DIR")
    if evidence_directory:
        evidence = Path(evidence_directory)
        evidence.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, evidence / "test-only-reel.mp4")
        execute(
            [
                binary("ffmpeg"),
                "-nostdin",
                "-y",
                "-v",
                "error",
                "-ss",
                "1",
                "-i",
                str(path),
                "-frames:v",
                "1",
                str(evidence / "test-only-subtitle-frame.png"),
            ]
        )
    print(json.dumps(report))
