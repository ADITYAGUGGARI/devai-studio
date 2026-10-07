"""Exercise the persistent UI workflow through real routes with mocked providers."""

import base64
import hashlib
import json
from datetime import UTC, datetime, timedelta
from io import BytesIO

import pytest
from PIL import Image

from devai.models import Job, Post, Slide, Topic
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


def test_daily_defaults_to_research_queue_without_generating_posts(client, monkeypatch):
    now = datetime.now(UTC)
    article = {
        "title": "Coding agents and practical production workflows",
        "url": "https://github.blog/agents-production/",
        "source": "GitHub Blog",
        "published_at": now,
        "summary": "Primary announcement for developer tools. " * 20,
    }
    monkeypatch.setattr(topics, "discover", lambda **_: {"articles": [article], "errors": []})
    monkeypatch.setattr(topics, "_safe_article_evidence", lambda item: item["summary"])

    def never_generate(*_, **__):
        raise AssertionError("Topic-first research must never call the copy or image provider")

    monkeypatch.setattr(topics, "generate", never_generate)
    monkeypatch.setattr(artwork, "_generate_image", never_generate)
    response = client.post("/research/daily/run", headers=HEADERS)
    assert response.status_code == 202 and response.json()["kind"] == "daily_research"
    jobs.work_once(client.app.state.session_factory)
    assert len(client.get("/topics", headers=HEADERS).json()) == 1
    assert client.get("/posts", headers=HEADERS).json() == []
    assert (
        client.get("/research/daily/latest", headers=HEADERS).json()["run"]["status"] == "completed"
    )
    assert (
        client.get(f"/jobs/{response.json()['id']}", headers=HEADERS).json()["status"]
        == "completed"
    )


def test_topic_selection_survives_reload_and_legacy_editorial_api(client):
    topic_id = add_topic(client)
    assert client.post(f"/topics/{topic_id}/select", headers=HEADERS).json()["selected"] is True
    assert client.get("/topics", headers=HEADERS).json()[0]["selected"] is True
    assert (
        client.get("/editorial/topics", headers=HEADERS).json()["topics"][0]["status"] == "selected"
    )
    assert (
        client.patch(
            f"/editorial/topics/{topic_id}", headers=HEADERS, json={"status": "archived"}
        ).status_code
        == 200
    )
    assert client.get("/topics", headers=HEADERS).json()[0]["status"] == "archived"


def test_existing_editorial_records_migrate_once_preserving_selection(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from devai.core.database import initialize_database
    from devai.models import EditorialTopic

    engine = create_engine(f"sqlite:///{tmp_path / 'upgrade.sqlite'}")
    initialize_database(engine)
    factory = sessionmaker(bind=engine)
    with factory.begin() as db:
        db.add(
            EditorialTopic(
                id="old-topic",
                source_url="https://example.com/old",
                title="Original saved story",
                source_name="Original publisher",
                summary="Old evidence snapshot",
                status="selected",
                priority=94,
            )
        )
    initialize_database(engine)
    initialize_database(engine)
    with factory() as db:
        assert db.query(Topic).count() == 1
        topic = db.get(Topic, "old-topic")
        assert topic.selected and topic.priority == 94 and topic.verification == "unverified"
        assert topic.excerpt == "Old evidence snapshot"


def test_tampered_image_cannot_be_approved_or_exported(client, ready_post):
    from pathlib import Path

    post_id = ready_post()
    with client.app.state.session_factory() as db:
        slide = db.query(Slide).filter_by(post_id=post_id).first()
        Path(slide.artwork_path).write_bytes(png(123))
    client.post(f"/posts/{post_id}/submit", headers=HEADERS)
    assert client.post(f"/posts/{post_id}/approve", headers=HEADERS).status_code == 409
    assert client.get(f"/posts/{post_id}/export", headers=HEADERS).status_code == 409


def test_api_background_worker_executes_jobs_without_browser_waiting(tmp_path, monkeypatch):
    import time

    from fastapi.testclient import TestClient

    from devai.core.config import Settings
    from devai.core.database import build_engine
    from devai.main import create_app

    now = datetime.now(UTC)
    monkeypatch.setattr(
        topics,
        "discover",
        lambda **_: {
            "articles": [
                {
                    "title": "AI developer agent release",
                    "url": "https://github.blog/background-agent/",
                    "source": "GitHub Blog",
                    "published_at": now,
                    "summary": "Official primary-source release evidence. " * 20,
                }
            ],
            "errors": [],
        },
    )
    monkeypatch.setattr(topics, "_safe_article_evidence", lambda item: item["summary"])
    app = create_app(
        Settings(admin_api_key="test-secret", background_worker_enabled=True, daily_enabled=False),
        engine=build_engine(f"sqlite:///{tmp_path / 'background.sqlite'}"),
    )
    with TestClient(app) as live:
        queued = live.post("/research/refresh", headers=HEADERS)
        assert queued.status_code == 202
        deadline = time.monotonic() + 5
        result = {}
        while time.monotonic() < deadline:
            result = live.get(f"/jobs/{queued.json()['id']}", headers=HEADERS).json()
            if result["status"] in {"completed", "failed"}:
                break
            time.sleep(0.05)
        assert result["status"] == "completed", result
        assert len(live.get("/topics", headers=HEADERS).json()) == 1
        assert live.get("/posts", headers=HEADERS).json() == []


def test_concurrent_job_claims_have_one_owner(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    from sqlalchemy.orm import sessionmaker

    from devai.core.database import build_engine, initialize_database

    engine = build_engine(f"sqlite:///{tmp_path / 'claims.sqlite'}")
    initialize_database(engine)
    factory = sessionmaker(bind=engine)
    jobs.enqueue(factory, "research", {}, key="research")
    with ThreadPoolExecutor(max_workers=4) as pool:
        claims = list(pool.map(lambda _: jobs._claim(factory), range(4)))
    assert len([claim for claim in claims if claim]) == 1


def test_image_text_validation_preserves_code_case_and_word_boundaries():
    assert artwork._normal_text("API_KEY") != artwork._normal_text("api_key")
    assert artwork._normal_text("async def") != artwork._normal_text("asyncdef")
    assert artwork._normal_text("Line one\nLine two") == artwork._normal_text("Line one Line two")
