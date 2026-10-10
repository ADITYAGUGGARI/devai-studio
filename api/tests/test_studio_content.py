"""Real persisted output jobs and media with external-provider fixtures only."""

import base64
import json
import os
import shutil
from io import BytesIO

import httpx
import pytest
from PIL import Image

from devai.models import Job
from devai.services.jobs import work_once
from devai.services.provider import ProviderError, post_json, provider_budget

HEADERS = {"X-API-Key": "test-secret"}


def action(client, path, body, key):
    return client.post(path, headers={**HEADERS, "Idempotency-Key": key}, json=body)


def approved_source(client):
    result = client.post(
        "/topics",
        headers=HEADERS,
        json={
            "title": "Executable developer agents",
            "url": "https://github.blog/test-only-studio-source",
            "excerpt": "The release includes an executable workflow API for software engineers. "
            * 12,
            "category": "architecture",
        },
    )
    assert result.status_code == 201, result.text
    identifier = result.json()["id"]
    assert client.post(f"/topics/{identifier}/verify", headers=HEADERS).status_code == 200
    assert client.post(f"/topics/{identifier}/approve", headers=HEADERS).status_code == 200
    return identifier


def setup(client, topic, formats=None):
    response = action(
        client,
        "/v1/setups",
        {
            "topicId": topic,
            "formats": formats or ["reel"],
            "options": {"voiceId": None, "subtitles": False},
        },
        "setup",
    )
    assert response.status_code == 201, response.text
    return response.json()


def generate(client, saved, formats=None, budget=64):
    caps = client.get("/v1/providers/capabilities", headers=HEADERS).json()
    response = action(
        client,
        f"/v1/setups/{saved['id']}/generate",
        {
            "expectedRevision": saved["revision"],
            "confirmedFormats": formats or ["reel"],
            "capabilityRevision": caps["revision"],
            "confirmedBudget": budget,
            "confirmed": True,
        },
        "generate",
    )
    assert response.status_code == 202, response.text
    return response.json()


def test_setup_requires_approved_evidence_and_preserves_idempotency(client):
    topic = approved_source(client)
    saved = setup(client, topic)
    replay = setup(client, topic)
    assert replay == saved
    changed = action(client, "/v1/setups", {"topicId": topic, "formats": ["carousel"]}, "setup")
    assert changed.status_code == 409
    edit = client.patch(
        f"/v1/setups/{saved['id']}",
        headers={**HEADERS, "Idempotency-Key": "edit"},
        json={"expectedRevision": 99, "topicId": topic, "formats": ["reel"]},
    )
    assert edit.status_code == 409
    assert edit.json()["detail"]["server"]["revision"] == 1
    assert client.get(f"/v1/setups/{saved['id']}", headers=HEADERS).json() == saved


def test_missing_credentials_block_paid_jobs_without_fake_success(client, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    saved = setup(client, approved_source(client))
    caps = client.get("/v1/providers/capabilities", headers=HEADERS).json()
    response = action(
        client,
        f"/v1/setups/{saved['id']}/generate",
        {
            "expectedRevision": 1,
            "confirmedFormats": ["reel"],
            "capabilityRevision": caps["revision"],
            "confirmedBudget": 64,
            "confirmed": True,
        },
        "generate",
    )
    assert response.status_code == 409
    assert client.get("/jobs", headers=HEADERS).json() == []
    assert client.get("/v1/content", headers=HEADERS).json()["items"] == []


def test_output_permissions_distinguish_editor_reviewer_and_viewer(client, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-configuration-not-a-real-key")
    topic = approved_source(client)
    saved = setup(client, topic, ["carousel"])
    created = generate(client, saved, ["carousel"])
    output_id = created["outputIds"][0]
    for role in ("editor", "reviewer", "viewer"):
        email, password = f"{role}@studio.test", "Isolated-permission-test-12345"
        user = client.post(
            "/auth/users",
            headers=HEADERS,
            json={"email": email, "password": password, "role": role},
        )
        assert user.status_code == 201, user.text
        login = client.post("/auth/login", json={"email": email, "password": password})
        assert login.status_code == 200
        headers = {
            "Authorization": f"Bearer {login.json()['token']}",
            "Idempotency-Key": f"{role}-action",
        }
        output = client.get(f"/v1/outputs/{output_id}", headers=headers)
        assert output.status_code == 200
        rejected = client.post(
            f"/v1/outputs/{output_id}/review/approve",
            headers=headers,
            json={
                "expectedRevision": output.json()["revision"],
                "confirmed": True,
                "reviewedAssetIds": ["no-generated-asset"],
                "checklist": {name: True for name in ("sources", "claims", "assets", "caption")},
            },
        )
        assert rejected.status_code == (409 if role == "reviewer" else 403), rejected.text
        setup_response = client.post(
            "/v1/setups", headers=headers, json={"topicId": topic, "formats": ["carousel"]}
        )
        assert setup_response.status_code == (201 if role == "editor" else 403), setup_response.text
    assert len(client.get("/jobs", headers=HEADERS).json()) == 1


def provider_fixture(monkeypatch, *, fail_scene=None):
    images = []
    counters = {"image": 0}
    scene_values = [
        {
            "id": f"scene-{index}",
            "headline": f"Workflow principle {index}",
            "body": "Developer API evidence",
            "script": "The release includes an executable workflow API for software engineers.",
            "durationSec": 7,
            "visualDirection": f"Original tactile engineering metaphor number {index} with cinematic lighting",
        }
        for index in range(5)
    ]

    def respond(url, **kwargs):
        payload = kwargs["json"]
        if url.endswith("images/generations"):
            counters["image"] += 1
            if counters["image"] == fail_scene:
                return httpx.Response(429, json={"error": {"code": "rate_limit"}})
            images.append(payload)
            buffer = BytesIO()
            Image.new("RGB", (1152, 2048), (20 + counters["image"], 80, 60)).save(
                buffer, format="PNG"
            )
            return httpx.Response(
                200, json={"data": [{"b64_json": base64.b64encode(buffer.getvalue()).decode()}]}
            )
        system = payload["messages"][0]["content"]
        if system.startswith("Write an original educational developer Reel"):
            value = {
                "title": "Executable developer workflows",
                "caption": "Developer interpretation. Source: https://github.blog/test-only-studio-source",
                "hashtags": ["#AI", "#Developers", "#Engineering"],
                "scenes": scene_values,
            }
        elif system.startswith("Audit the image"):
            value = json.loads(
                payload["messages"][1]["content"][0]["text"].split(
                    "independently transcribe visible main text: "
                )[1]
            )
            value.update(legible=True, clipped=False, extra_claims=False, issues=[])
        else:
            value = {
                "supported": True,
                "claims": [
                    {
                        "claim": "An executable workflow API is included",
                        "evidence_quote": "The release includes an executable workflow API for software engineers.",
                    }
                ],
                "issues": [],
            }
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(value)}}]})

    monkeypatch.setattr("devai.services.provider.httpx.post", respond)
    return images


@pytest.mark.skipif(
    not (os.getenv("FFMPEG_BIN") or shutil.which("ffmpeg")),
    reason="Actual worker codec dependency is required",
)
def test_actual_reel_pipeline_review_export_and_material_edit_invalidation(
    client, monkeypatch, tmp_path
):
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-provider-fixture")
    monkeypatch.setenv("STUDIO_MEDIA_DIR", str(tmp_path))
    images = provider_fixture(monkeypatch)
    created = generate(client, setup(client, approved_source(client)))
    assert work_once(client.app.state.session_factory)
    output_id = created["outputIds"][0]
    output = client.get(f"/v1/outputs/{output_id}", headers=HEADERS).json()
    assert output["job"]["status"] == "completed", output
    assert output["data"]["stage"] == "mp4_validated"
    assert output["data"]["renderValidation"]["decoded"]
    assert output["data"]["renderCurrent"]
    assert len(images) == 5
    assert all(tag in output["data"]["caption"] for tag in output["data"]["hashtags"])
    assert all(item["size"] == "1152x2048" for item in images)
    assert "privatePath" not in json.dumps(output)
    render_id = output["data"]["renderId"]
    media = client.get(f"/v1/assets/{render_id}", headers={**HEADERS, "Range": "bytes=0-31"})
    assert media.status_code == 206 and len(media.content) == 32
    review = {
        "expectedRevision": output["revision"],
        "confirmed": True,
        "reviewedAssetIds": [render_id],
        "checklist": {name: True for name in ("sources", "claims", "assets", "caption")},
    }
    submitted = action(client, f"/v1/outputs/{output_id}/review/submit", review, "submit")
    assert submitted.status_code == 200, submitted.text
    review["expectedRevision"] = submitted.json()["revision"]
    approved = action(client, f"/v1/outputs/{output_id}/review/approve", review, "approve")
    assert approved.status_code == 200
    assert approved.json()["state"] == "approved"
    assert client.get(f"/v1/outputs/{output_id}/export", headers=HEADERS).content.startswith(b"PK")
    timeline = {
        "expectedRevision": approved.json()["revision"],
        "scenes": [
            {key: scene[key] for key in ("id", "headline", "body", "script", "durationSec")}
            for scene in output["data"]["scenes"]
        ],
        "caption": output["data"]["caption"] + "\nUpdated analysis.",
        "voiceId": None,
        "subtitles": False,
    }
    edited = client.patch(
        f"/v1/outputs/{output_id}/timeline",
        headers={**HEADERS, "Idempotency-Key": "edit"},
        json=timeline,
    )
    assert edited.status_code == 200, edited.text
    assert "approval" not in edited.json()["data"]
    assert not edited.json()["data"]["renderCurrent"]
    assert all(scene["imageCurrent"] for scene in edited.json()["data"]["scenes"])
    assert client.get(f"/v1/assets/{render_id}", headers=HEADERS).status_code == 200
    assert client.get(f"/v1/outputs/{output_id}/export", headers=HEADERS).status_code == 409
    changes = action(
        client,
        f"/v1/outputs/{output_id}/changes",
        {
            "expectedRevision": edited.json()["revision"],
            "notes": "Clarify the engineering example.",
        },
        "request-revision",
    )
    assert changes.status_code == 200, changes.text
    assert changes.json()["state"] == "changes_requested"
    assert client.get(f"/v1/assets/{render_id}", headers=HEADERS).status_code == 200
    restored = action(
        client,
        f"/v1/outputs/{output_id}/versions/restore",
        {
            "expectedRevision": changes.json()["revision"],
            "targetRevision": approved.json()["revision"],
            "confirmed": True,
        },
        "restore-review-version",
    )
    assert restored.status_code == 200, restored.text
    assert restored.json()["revision"] > changes.json()["revision"]
    assert restored.json()["state"] == "draft"
    assert restored.json()["data"]["renderCurrent"]
    assert "approval" not in restored.json()["data"]
    assert restored.json()["data"]["budgetRemaining"] == changes.json()["data"]["budgetRemaining"]
    assert restored.json()["data"]["revisionRequests"] == changes.json()["data"]["revisionRequests"]


@pytest.mark.skipif(
    not (os.getenv("FFMPEG_BIN") or shutil.which("ffmpeg")),
    reason="Worker media dependency is required",
)
def test_partial_scene_retry_reuses_successful_assets_and_budget(client, monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-provider-fixture")
    monkeypatch.setenv("STUDIO_MEDIA_DIR", str(tmp_path))
    provider_fixture(monkeypatch, fail_scene=2)
    created = generate(client, setup(client, approved_source(client)))
    assert work_once(client.app.state.session_factory)
    output_id = created["outputIds"][0]
    failed = client.get(f"/v1/outputs/{output_id}", headers=HEADERS).json()
    assert failed["job"]["status"] == "retry_wait"
    asset_id = failed["data"]["scenes"][0]["imageAssetId"]
    remaining = failed["data"]["budgetRemaining"]
    retried = client.post(f"/jobs/{created['jobIds'][0]}/retry", headers=HEADERS)
    assert retried.status_code == 202, retried.text
    with client.app.state.session_factory() as db:
        assert db.get(Job, created["jobIds"][0]).active_key.endswith(f"output:{output_id}")
    assert work_once(client.app.state.session_factory)
    resumed = client.get(f"/v1/outputs/{output_id}", headers=HEADERS).json()
    assert resumed["job"]["status"] == "completed", resumed
    assert resumed["data"]["scenes"][0]["imageAssetId"] == asset_id
    assert resumed["data"]["budgetRemaining"] < remaining


def test_provider_budget_stops_before_unapproved_network_call(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-fixture")
    calls = []
    monkeypatch.setattr(
        "devai.services.provider.httpx.post", lambda *args, **kwargs: calls.append(args)
    )

    def exhausted():
        raise ProviderError("Authorized budget exhausted")

    with provider_budget(exhausted), pytest.raises(ProviderError, match="budget exhausted"):
        post_json("chat/completions", {})
    assert calls == []
