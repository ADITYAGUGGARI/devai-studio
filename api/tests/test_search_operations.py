"""Provider contract fixtures are isolated; no test substitutes for live evidence."""

import json
from datetime import UTC, datetime

import httpx
import pytest
from sqlalchemy import create_engine, inspect

from devai.core.config import Settings
from devai.migrate import run
from devai.models import WorkspaceSetting
from devai.services import artwork, jobs, operations, search


def test_search_uses_only_consulted_primary_urls_with_readable_dated_pages(monkeypatch):
    calls = []

    def response(path, payload):
        calls.append(payload)
        return {
            "output": [
                {
                    "type": "web_search_call",
                    "action": {
                        "sources": [
                            {"url": "https://arxiv.org/abs/test", "title": "Isolated paper"},
                            {"url": "https://untrusted.test/page"},
                        ]
                    },
                }
            ]
        }

    monkeypatch.setattr(search, "post_json", response)
    monkeypatch.setenv("OPENAI_SEARCH_MODEL", "gpt-4.1-mini")
    html = (
        '<meta property="article:published_time" content="bad"><meta name="citation_date" content="2026/10/07"><meta name="citation_title" content="Isolated paper"><article>'
        + "Evidence explicitly provided by an isolated test fixture. " * 20
        + "</article>"
    )
    original = httpx.Client
    monkeypatch.setattr(
        search.httpx,
        "Client",
        lambda **kw: original(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200, text=html, headers={"content-type": "text/html"}
                )
            ),
            **kw,
        ),
    )
    result = search.search_web("Developer paper", now=datetime(2026, 10, 7, tzinfo=UTC))
    assert len(result["articles"]) == 1
    assert result["articles"][0]["url"] == "https://arxiv.org/abs/test"
    assert len(result["articles"][0]["summary"]) >= 240
    assert calls[0]["tools"] == [{"type": "web_search"}]
    assert calls[0]["include"] == ["web_search_call.action.sources"]
    monkeypatch.setenv("OPENAI_SEARCH_MODEL", "gpt-5-mini")
    search.search_web("Developer paper", now=datetime(2026, 10, 7, tzinfo=UTC))
    assert "filters" in calls[-1]["tools"][0]


def test_daily_search_keeps_consulted_urls_and_never_invents_topics(client, monkeypatch):
    monkeypatch.setenv("DAILY_WEB_SEARCH", "true")
    monkeypatch.setattr(
        search,
        "search_web",
        lambda *a, **kw: {
            "articles": [],
            "errors": ["No dated evidence"],
            "searched_urls": ["https://arxiv.org/abs/test"],
        },
    )
    j = jobs.enqueue(
        client.app.state.session_factory,
        "daily_research",
        {"local_date": "2026-10-07", "timezone": "America/Chicago"},
    )
    assert jobs.work_once(client.app.state.session_factory)
    result = client.get("/jobs/" + j["id"], headers={"X-API-Key": "test-secret"}).json()
    assert result["status"] == "failed"
    assert result["result"]["searched_urls"] == ["https://arxiv.org/abs/test"]
    assert result["result"]["warnings"] == ["No dated evidence"]
    assert client.get("/topics", headers={"X-API-Key": "test-secret"}).json() == []


def test_worker_heartbeat_is_persistent_and_expires(client):
    factory = client.app.state.session_factory
    assert not operations.worker_health(factory)["healthy"]
    operations.record_worker_heartbeat(factory)
    assert operations.worker_health(factory)["healthy"]
    with factory.begin() as db:
        db.get(WorkspaceSetting, "worker_heartbeat").value_json = json.dumps(
            {"at": "2000-01-01T00:00:00+00:00"}
        )
    assert not operations.worker_health(factory)["healthy"]


def test_migration_upgrade_downgrade_round_trip(tmp_path):
    engine = create_engine("sqlite:///" + str(tmp_path / "migration.sqlite"))
    run(engine)
    assert "auth_sessions" in inspect(engine).get_table_names()
    run(engine, "downgrade", "base")
    assert "posts" not in inspect(engine).get_table_names()
    run(engine)
    assert "posts" in inspect(engine).get_table_names()
    engine.dispose()


def test_production_refuses_insecure_configuration(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    with pytest.raises(ValueError, match="PostgreSQL"):
        Settings(database_url="sqlite://")
    monkeypatch.setenv("ALLOW_DEV_API_KEY", "false")
    monkeypatch.setenv("COOKIE_SECURE", "true")
    with pytest.raises(ValueError, match="HTTPS"):
        Settings(
            database_url="postgresql+psycopg://local/db", cors_origins=("http://example.test",)
        )
    Settings(database_url="postgresql+psycopg://local/db", cors_origins=("https://example.test",))


def test_image_claim_and_transcription_guards(monkeypatch):
    visible = {
        "headline": "Saved title",
        "body": "Saved body",
        "legible": True,
        "clipped": False,
        "extra_claims": True,
        "issues": ["Invented metric"],
    }
    monkeypatch.setattr(
        artwork,
        "post_json",
        lambda *a, **kw: {"choices": [{"message": {"content": json.dumps(visible)}}]},
    )
    result = artwork.validate_image(
        b"isolated-test-image", {"headline": "Saved title", "body": "Saved body"}
    )
    assert not result["passed"]
    assert result["issues"] == ["Invented metric"]


def test_explicit_migrations_are_required_when_startup_migrations_disabled(tmp_path, monkeypatch):
    from devai.core.database import prepare_database

    monkeypatch.setenv("AUTO_MIGRATE", "false")
    engine = create_engine("sqlite:///" + str(tmp_path / "pending.sqlite"))
    with pytest.raises(RuntimeError, match="migrations are pending"):
        prepare_database(engine)
    run(engine)
    prepare_database(engine)
    engine.dispose()
