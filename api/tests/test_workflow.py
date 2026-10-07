"""Exercise the persistent UI workflow through real routes with mocked providers."""

import base64
import hashlib
import json
from datetime import UTC, datetime, timedelta
from io import BytesIO

import pytest
from PIL import Image

from devai.models import Job, Post, Slide
from devai.services import artwork, jobs, topics
from devai.services.provider import ProviderError

HEADERS = {"x-api-key": "test-secret"}


def png(index=0):
    stream = BytesIO()
    Image.new("RGB", (1080, 1350), (index % 255, 140, 210)).save(stream, format="PNG")
    return stream.getvalue()


def add_topic(client, url="https://example.com/story"):
    result = client.post(
        "/topics",
        headers=HEADERS,
        json={
            "title": "New AI workflow for developers",
            "url": url,
            "excerpt": "A primary source explains an executable workflow for AI software engineering. "
            * 12,
            "category": "architecture",
        },
    )
    assert result.status_code == 201
    return result.json()["id"]


def fake_art(monkeypatch):
    prompts = []

    def create(prompt, **_):
        prompts.append(prompt)
        return png(len(prompts))

    monkeypatch.setattr(artwork, "_generate_image", create)
    monkeypatch.setattr(
        artwork,
        "validate_image",
        lambda *_: {"passed": True, "issues": [], "human_review_required": True},
    )
    return prompts


def test_topic_selection_complete_images_validation_review_and_export(
    client, monkeypatch, tmp_path
):
    topic_id = add_topic(client)
    assert (
        client.post(
            f"/topics/{topic_id}/generate", headers=HEADERS, json={"slide_count": 6}
        ).status_code
        == 409
    )
    client.post(f"/topics/{topic_id}/verify", headers=HEADERS)
    monkeypatch.setenv("CAROUSEL_ARTWORK_DIR", str(tmp_path))

    def generate(title, url, excerpt, **options):
        return {
            "title": "Executable AI workflows explained",
            "caption": f"Original advice. Source: {url}",
            "editorial_angle": "How do executable workflow primitives help?",
            "slides": [
                {
                    "headline": f"Workflow principle {n}",
                    "body": f"Engineering example {n}.",
                    "visual_direction": f"Unique tactile visual metaphor {n}",
                }
                for n in range(options["slide_count"])
            ],
        }

    monkeypatch.setattr(topics, "generate", generate)
    monkeypatch.setattr(
        topics,
        "verify_copy",
        lambda *_: {"supported": True, "issues": [], "claims": [], "human_review_required": True},
    )
    prompts = fake_art(monkeypatch)
    response = client.post(f"/topics/{topic_id}/generate", headers=HEADERS, json={"slide_count": 6})
    assert response.status_code == 202
    job_id = response.json()["id"]
    duplicate = client.post(
        f"/topics/{topic_id}/generate", headers=HEADERS, json={"slide_count": 6}
    )
    assert duplicate.json()["id"] == job_id
    assert jobs.work_once(client.app.state.session_factory)
    job = client.get(f"/jobs/{job_id}", headers=HEADERS).json()
    assert job["status"] == "completed", job
    post_id = job["result"]["post_id"]
    post = client.get(f"/posts/{post_id}", headers=HEADERS).json()
    assert len(post["slides"]) == 6 and post["status"] == "draft"
    assert len(set(prompts)) == 6 and all(
        "COMPLETE" in prompt and "EXACT" in prompt for prompt in prompts
    )
    assert post["evidence"]["source_url"] == "https://example.com/story"
    for slide in post["slides"]:
        assert slide["composition_mode"] == "ai_native" and slide["validation"]["passed"]
        preview = client.get(f"/posts/{post_id}/slides/{slide['id']}/image", headers=HEADERS)
        with client.app.state.session_factory() as db:
            saved = db.get(Slide, slide["id"])
            assert (
                hashlib.sha256(preview.content).hexdigest()
                == json.loads(saved.validation_json)["image_sha256"]
            )
    assert client.get(f"/posts/{post_id}/export", headers=HEADERS).status_code == 200
    client.post(f"/posts/{post_id}/submit", headers=HEADERS)
    assert client.post(f"/posts/{post_id}/approve", headers=HEADERS).status_code == 200
    slide = post["slides"][1]
    regenerate = client.post(f"/posts/{post_id}/slides/{slide['id']}/regenerate", headers=HEADERS)
    assert regenerate.status_code == 202
    assert (
        client.patch(f"/posts/{post_id}", headers=HEADERS, json={"title": "Late edit"}).status_code
        == 409
    )
    assert client.get(f"/posts/{post_id}", headers=HEADERS).json()["status"] == "draft"
    jobs.work_once(client.app.state.session_factory)
    assert len(prompts) == 7


def test_partial_artwork_retry_resumes_successful_slides(client, ready_post, monkeypatch, tmp_path):
    post_id = ready_post()
    monkeypatch.setenv("CAROUSEL_ARTWORK_DIR", str(tmp_path / "generated"))
    calls = []

    def generate(prompt, **_):
        calls.append(prompt)
        if len(calls) == 2:
            raise ProviderError("Temporary rate limit", retryable=True)
        return png(50 + len(calls))

    monkeypatch.setattr(artwork, "_generate_image", generate)
    monkeypatch.setattr(artwork, "validate_image", lambda *_: {"passed": True, "issues": []})
    job_id = client.post(f"/posts/{post_id}/artwork", headers=HEADERS).json()["id"]
    jobs.work_once(client.app.state.session_factory)
    assert client.get(f"/jobs/{job_id}", headers=HEADERS).json()["status"] == "retry_wait"
    assert client.post(f"/jobs/{job_id}/retry", headers=HEADERS).status_code == 202
    jobs.work_once(client.app.state.session_factory)
    assert client.get(f"/jobs/{job_id}", headers=HEADERS).json()["status"] == "completed"
    assert len(calls) == 7  # Six images and one failed request, not two full carousels.


def test_validation_failure_saved_and_blocks_approval(client, ready_post, monkeypatch, tmp_path):
    post_id = ready_post()
    monkeypatch.setenv("CAROUSEL_ARTWORK_DIR", str(tmp_path / "bad"))
    fake_art(monkeypatch)
    monkeypatch.setattr(
        artwork, "validate_image", lambda *_: {"passed": False, "issues": ["Wrong headline"]}
    )
    slide = client.get(f"/posts/{post_id}", headers=HEADERS).json()["slides"][0]
    job_id = client.post(
        f"/posts/{post_id}/slides/{slide['id']}/regenerate", headers=HEADERS
    ).json()["id"]
    jobs.work_once(client.app.state.session_factory)
    assert client.get(f"/jobs/{job_id}", headers=HEADERS).json()["status"] == "failed"
    updated = client.get(f"/posts/{post_id}", headers=HEADERS).json()
    assert updated["slides"][0]["validation"]["passed"] is False
    client.post(f"/posts/{post_id}/submit", headers=HEADERS)
    assert client.post(f"/posts/{post_id}/approve", headers=HEADERS).status_code == 409


def test_vision_checks_transcribed_copy_not_model_assertions(monkeypatch):
    data = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "headline": "Wrong headline",
                            "body": "Saved body",
                            "legible": True,
                            "clipped": False,
                            "extra_claims": False,
                            "issues": [],
                        }
                    )
                }
            }
        ]
    }
    monkeypatch.setattr(artwork, "post_json", lambda *_args, **_kwargs: data)
    assert (
        artwork.validate_image(png(), {"headline": "Saved headline", "body": "Saved body"})[
            "passed"
        ]
        is False
    )


def test_research_queue_is_prioritized_persistent_and_idempotent(client, monkeypatch):
    now = datetime.now(UTC)
    articles = [
        {
            "title": "AI agent tools for developers",
            "url": "https://github.blog/ai-agent-tools/",
            "source": "GitHub Blog",
            "summary": "Official release evidence. " * 30,
            "published_at": now,
        }
    ]
    monkeypatch.setattr(topics, "_safe_article_evidence", lambda item: item["summary"])
    report = topics.research_queue(
        client.app.state.session_factory,
        discover_fn=lambda **_: {"articles": articles, "errors": ["One unavailable feed"]},
    )
    assert len(report["created_topic_ids"]) == 1
    second = topics.research_queue(
        client.app.state.session_factory,
        discover_fn=lambda **_: {"articles": articles, "errors": []},
    )
    assert second["created_topic_ids"] == []
    queued = client.get("/topics", headers=HEADERS).json()[0]
    assert queued["verification"] == "primary_source" and queued["published_at"]
    assert (
        client.patch(f"/topics/{queued['id']}", headers=HEADERS, json={"priority": 99}).json()[
            "priority"
        ]
        == 99
    )
    client.patch(f"/topics/{queued['id']}", headers=HEADERS, json={"status": "archived"})
    assert (
        client.post(f"/topics/{queued['id']}/generate", headers=HEADERS, json={}).status_code == 409
    )


def test_job_claim_and_expired_lease_recovery(client):
    factory = client.app.state.session_factory
    first = jobs.enqueue(factory, "research", {}, key="research")
    assert jobs.enqueue(factory, "research", {}, key="research")["id"] == first["id"]
    claim = jobs._claim(factory)
    assert claim and jobs._claim(factory) is None
    with factory.begin() as db:
        db.get(Job, first["id"]).lease_until = datetime.now(UTC) - timedelta(seconds=1)
    recovered = jobs._claim(factory)
    assert recovered and recovered["token"] != claim["token"]
    with pytest.raises(RuntimeError, match="lease"):
        jobs._update(factory, claim, step="Old worker")


def test_interrupted_publish_is_not_claimed_again(client, ready_post):
    factory = client.app.state.session_factory
    post_id = ready_post()
    job = jobs.enqueue(
        factory, "publish", {"post_id": post_id, "version": "1"}, key=f"post:{post_id}"
    )
    assert jobs._claim(factory)
    with factory.begin() as db:
        db.get(Job, job["id"]).lease_until = datetime.now(UTC) - timedelta(seconds=1)
        db.get(Post, post_id).status = "publishing"
    assert jobs._claim(factory) is None
    assert (
        client.get(f"/jobs/{job['id']}", headers=HEADERS).json()["status"] == "needs_reconciliation"
    )


def test_unsupported_copy_never_saves_post(client, monkeypatch):
    topic_id = add_topic(client)
    client.post(f"/topics/{topic_id}/verify", headers=HEADERS)
    monkeypatch.setattr(topics, "generate", lambda *_args, **_kwargs: {"title": "Invented fact"})
    monkeypatch.setattr(
        topics, "verify_copy", lambda *_: {"supported": False, "issues": ["Invented benchmark"]}
    )
    job_id = client.post(f"/topics/{topic_id}/generate", headers=HEADERS, json={}).json()["id"]
    jobs.work_once(client.app.state.session_factory)
    assert client.get(f"/jobs/{job_id}", headers=HEADERS).json()["status"] == "failed"
    assert client.get("/posts", headers=HEADERS).json() == []


def test_daily_job_deduplicated_across_scheduler_restarts(client):
    factory = client.app.state.session_factory
    now = datetime.now(UTC)
    first = jobs.enqueue_daily(factory, "UTC", now=now)
    second = jobs.enqueue_daily(factory, "UTC", now=now)
    assert first["id"] == second["id"]


def test_image_request_includes_complete_copy_and_normalizes_only(monkeypatch):
    def provider(path, payload, **_):
        assert path == "images/generations" and payload["size"] == "1088x1360"
        assert "exact_headline" in payload["prompt"]
        return {"data": [{"b64_json": base64.b64encode(png()).decode()}]}

    monkeypatch.setattr(artwork, "post_json", provider)
    prompt = artwork._image_prompt(
        "AI",
        {
            "headline": "Exact headline",
            "body": "Exact body",
            "visual_direction": "Invent new visual",
        },
        1,
        6,
    )
    assert Image.open(BytesIO(artwork._generate_image(prompt))).size == (1080, 1350)
