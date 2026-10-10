"""Actual audio upload, decode and mixing; synthetic WAV belongs only to tests."""

import hashlib
import io
import json
import math
import struct
import wave

import pytest
from test_studio_content import HEADERS, action, approved_source, generate, setup

from devai.services.jobs import work_once
from devai.services.studio_audio import mix_audio, validate_audio
from devai.services.video import probe


def wav_bytes():
    stream = io.BytesIO()
    with wave.open(stream, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8000)
        wav.writeframes(
            b"".join(
                struct.pack("<h", int(6000 * math.sin(i * 2 * math.pi * 440 / 8000)))
                for i in range(8000)
            )
        )
    return stream.getvalue()


def test_licensed_upload_is_expiring_private_durable_and_decoded(client, monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-not-a-real-key")
    monkeypatch.setenv("STUDIO_MEDIA_DIR", str(tmp_path))
    content = generate(client, setup(client, approved_source(client)))
    output_id = content["outputIds"][0]
    # Cancel generation before any provider can run; the upload has its own real job.
    job_id = client.get(f"/v1/outputs/{output_id}", headers=HEADERS).json()["job"]["id"]
    assert client.post(f"/v1/jobs/{job_id}/cancel", headers=HEADERS).status_code == 200
    raw = wav_bytes()
    payload = {
        "fileName": "licensed.wav",
        "mimeType": "audio/wav",
        "sizeBytes": len(raw),
        "license": {"acknowledged": True, "basis": "owned", "reference": "Test owner"},
    }
    path = f"/v1/outputs/{output_id}/audio/uploads"
    bad = {**payload, "license": {**payload["license"], "acknowledged": False}}
    assert action(client, path, bad, "no-rights").status_code == 422
    assert (
        action(client, path, {**payload, "sizeBytes": 50 * 1024 * 1024 + 1}, "too-big").status_code
        == 422
    )
    assert (
        action(client, path, {**payload, "fileName": "../unsafe.wav"}, "unsafe").status_code == 422
    )
    prepared = action(client, path, payload, "prepare-audio")
    assert prepared.status_code == 201, prepared.text
    value = prepared.json()
    assert "privateTokenHash" not in json.dumps(value)
    upload_id = value["upload"]["id"]
    headers = {**HEADERS, "Content-Type": "audio/wav", "X-Upload-Token": value["token"]}
    assert (
        client.put(
            value["uploadPath"], headers={**headers, "X-Upload-Token": "wrong"}, content=raw
        ).status_code
        == 403
    )
    assert client.put(value["uploadPath"], headers=headers, content=raw[:-2]).status_code == 422
    assert (
        client.put(value["uploadPath"], headers=headers, content=raw + b"extra").status_code == 413
    )
    response = client.put(value["uploadPath"], headers=headers, content=raw)
    assert response.status_code == 200, response.text
    assert response.json()["sha256"] == hashlib.sha256(raw).hexdigest()
    assert client.put(value["uploadPath"], headers=headers, content=raw).status_code == 200
    assert (
        action(client, value["completePath"], {"sha256": "0" * 64}, "bad-checksum").status_code
        == 409
    )
    completed = action(
        client, value["completePath"], {"sha256": response.json()["sha256"]}, "complete-audio"
    )
    assert completed.status_code == 202, completed.text
    # Worker picks the cancelled generation once, then processes real uploaded bytes.
    factory = client.app.state.session_factory
    for _ in range(3):
        work_once(factory)
    saved = client.get(f"/v1/uploads/{upload_id}", headers=HEADERS).json()
    assert saved["state"] == "validated", saved
    assert saved["data"]["validation"]["decoded"]
    assert saved["job"]["status"] == "completed"
    assert "privatePath" not in json.dumps(saved)
    asset_id = saved["data"]["assetId"]
    result = client.get(f"/v1/assets/{asset_id}", headers=HEADERS)
    assert result.status_code == 200 and result.content.startswith(b"RIFF")
    again = action(
        client, value["completePath"], {"sha256": response.json()["sha256"]}, "complete-again"
    )
    assert again.json()["assetId"] == asset_id


def test_real_audio_decode_and_ducking_mix(tmp_path):
    path = tmp_path / "test.wav"
    path.write_bytes(wav_bytes())
    normalized, report = validate_audio(path, tmp_path, lambda: None)
    assert report["passed"] and report["decoded"]
    for voice, ducking in ((normalized, True), (normalized, False), (None, True)):
        mixed = mix_audio(
            voice,
            normalized,
            duration=35,
            voice_gain=-3,
            music_gain=-18,
            ducking=ducking,
            directory=tmp_path,
            checkpoint=lambda: None,
        )
        result = probe(mixed)
        assert float(result["format"]["duration"]) == pytest.approx(35, abs=0.02)
        assert result["streams"][0]["channels"] == 2
    invalid = tmp_path / "invalid.wav"
    invalid.write_bytes(b"not an audio track")
    with pytest.raises(ValueError):
        validate_audio(invalid, tmp_path, lambda: None)


def test_music_and_edited_subtitles_reach_actual_render_without_regenerating_images(
    client, monkeypatch, tmp_path
):
    from test_studio_content import provider_fixture

    monkeypatch.setenv("OPENAI_API_KEY", "test-only-provider-fixture")
    monkeypatch.setenv("STUDIO_MEDIA_DIR", str(tmp_path))
    images = provider_fixture(monkeypatch)
    created = generate(client, setup(client, approved_source(client)))
    factory = client.app.state.session_factory
    assert work_once(factory)
    output_id = created["outputIds"][0]
    old = client.get(f"/v1/outputs/{output_id}", headers=HEADERS).json()
    assert old["data"]["renderCurrent"]
    raw = wav_bytes()
    prepared = action(
        client,
        f"/v1/outputs/{output_id}/audio/uploads",
        {
            "fileName": "music.wav",
            "mimeType": "audio/wav",
            "sizeBytes": len(raw),
            "license": {"acknowledged": True, "basis": "owned", "reference": "Test owner"},
        },
        "prepare-music",
    ).json()
    uploaded = client.put(
        prepared["uploadPath"],
        headers={**HEADERS, "Content-Type": "audio/wav", "X-Upload-Token": prepared["token"]},
        content=raw,
    )
    assert uploaded.status_code == 200
    assert (
        action(
            client,
            prepared["completePath"],
            {"sha256": uploaded.json()["sha256"]},
            "complete-music",
        ).status_code
        == 202
    )
    assert work_once(factory)
    music = client.get(f"/v1/uploads/{prepared['upload']['id']}", headers=HEADERS).json()["data"][
        "assetId"
    ]
    timeline = {
        "expectedRevision": old["revision"],
        "scenes": [
            {key: s[key] for key in ("id", "headline", "body", "script", "durationSec")}
            for s in old["data"]["scenes"]
        ],
        "caption": old["data"]["caption"],
        "voiceId": None,
        "subtitles": False,
        "subtitleCues": [{"start": 0, "end": 7, "text": "An executable workflow API is included."}],
        "musicAssetId": music,
        "musicGainDb": -12,
        "voiceGainDb": 0,
        "ducking": True,
    }
    invalid = client.patch(
        f"/v1/outputs/{output_id}/timeline",
        headers={**HEADERS, "Idempotency-Key": "bad-gain"},
        json={**timeline, "musicGainDb": 7},
    )
    assert invalid.status_code == 422
    edited = client.patch(
        f"/v1/outputs/{output_id}/timeline",
        headers={**HEADERS, "Idempotency-Key": "music-mix"},
        json=timeline,
    )
    assert edited.status_code == 200, edited.text
    assert not edited.json()["data"]["renderCurrent"]
    assert (
        action(
            client,
            f"/v1/outputs/{output_id}/render",
            {"expectedRevision": edited.json()["revision"], "confirmed": True},
            "render-music",
        ).status_code
        == 202
    )
    assert work_once(factory)
    rendered = client.get(f"/v1/outputs/{output_id}", headers=HEADERS).json()
    assert rendered["data"]["renderCurrent"], rendered
    assert rendered["data"]["renderValidation"]["audio_present"]
    assert rendered["data"]["renderValidation"]["decoded"]
    assert len(images) == 5  # Existing artwork is preserved and reused.
    assert rendered["data"]["renderId"] != old["data"]["renderId"]
    assert client.get(f"/v1/assets/{old['data']['renderId']}", headers=HEADERS).status_code == 200
    assert client.get(f"/v1/outputs/{output_id}/export", headers=HEADERS).status_code == 200
