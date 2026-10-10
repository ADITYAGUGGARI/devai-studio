"""Real persistence and ranking with isolated external source fixtures."""

from datetime import UTC, datetime, timedelta

import httpx
import pytest

from devai.core.workspaces import scoped_factory
from devai.models import Job
from devai.models.studio import LEGACY_WORKSPACE
from devai.services.jobs import work_once
from devai.services.research_runs import collect_run

HEADERS = {"x-api-key": "test-secret", "Idempotency-Key": "research-one"}


def test_short_feed_summaries_retrieve_evidence_and_keep_inaccessible_findings(client, monkeypatch):
    run = client.post("/v1/research/runs", headers=HEADERS, json={}).json()
    evidence = "The source describes an available developer API integration. " * 10

    def article(item):
        if item["url"].endswith("readable"):
            return evidence
        raise httpx.HTTPStatusError(
            "test-only inaccessible source",
            request=httpx.Request("GET", item["url"]),
            response=httpx.Response(403),
        )

    monkeypatch.setattr("devai.services.research.fetch_article", article)
    records = [
        {
            "url": f"https://github.blog/{name}",
            "title": "Developer AI API release",
            "summary": "Brief summary",
            "published": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
        }
        for name in ("readable", "inaccessible")
    ]
    result = collect_run(
        scoped_factory(client.app.state.session_factory, LEGACY_WORKSPACE),
        run["runId"],
        lambda *args: None,
        feeds={"GitHub Blog": "fixture"},
        fetch=lambda _: records,
    )
    assert result["counts"] == {"usable": 1, "insufficient_evidence": 1}
    assert any("HTTP 403" in warning for warning in result["warnings"])
    items = client.get(f"/v1/research/runs/{run['runId']}/findings", headers=HEADERS).json()[
        "items"
    ]
    readable = next(item for item in items if item["disposition"] == "usable")
    blocked = next(item for item in items if item["disposition"] == "insufficient_evidence")
    assert readable["evidence"]["excerpt"] == evidence.strip()
    assert readable["evidence"]["kind"] == "publisher_article"
    assert not readable["evidence"]["claims_verified"]
    assert blocked["topicId"] is None


def test_research_retry_retains_active_resource_lock(client):
    run = client.post("/v1/research/runs", headers=HEADERS, json={}).json()
    with client.app.state.session_factory.begin() as db:
        job = db.get(Job, run["jobId"])
        expected_key = job.active_key
        job.status, job.active_key, job.cancel_requested = "failed", None, True
    response = client.post(f"/jobs/{run['jobId']}/retry", headers=HEADERS)
    assert response.status_code == 202, response.text
    with client.app.state.session_factory() as db:
        job = db.get(Job, run["jobId"])
        assert job.active_key == expected_key
        assert not job.cancel_requested
    # A second action must join the active resource rather than enqueue duplicate work.
    second = client.post(
        "/v1/research/runs", headers={**HEADERS, "Idempotency-Key": "research-two"}, json={}
    )
    assert second.status_code == 202
    assert second.json()["jobId"] == run["jobId"]


def test_running_cancellation_keeps_completed_work(client):
    result = client.post("/v1/research/runs", headers=HEADERS, json={}).json()
    identifier = result["jobId"]

    def handler(factory, claim, progress):
        progress(1, 4, "One source collected")
        response = client.post(f"/v1/jobs/{identifier}/cancel", headers=HEADERS)
        assert response.status_code == 200
        progress(2, 4, "Next safe checkpoint")
        pytest.fail("Cancelled job must not continue")

    assert work_once(client.app.state.session_factory, handler=handler)
    with client.app.state.session_factory() as db:
        job = db.get(Job, identifier)
        assert job.status == "cancelled"
        assert job.progress == 1
        assert job.active_key is None


def test_queued_cancellation_never_runs(client):
    result = client.post("/v1/research/runs", headers=HEADERS, json={}).json()
    assert client.post(f"/v1/jobs/{result['jobId']}/cancel", headers=HEADERS).status_code == 200
    assert not work_once(client.app.state.session_factory)


def test_opaque_cursor_has_stable_order_and_rejects_changed_filters(client):
    run = client.post("/v1/research/runs", headers=HEADERS, json={}).json()
    now = datetime.now(UTC)
    records = [
        {
            "url": f"https://github.blog/developer-{index}",
            "title": f"AI developer code release {index}",
            "summary": "Available API integration" * 40,
            "published": (now - timedelta(hours=1)).isoformat(),
        }
        for index in range(30)
    ]
    factory = scoped_factory(client.app.state.session_factory, LEGACY_WORKSPACE)
    collect_run(
        factory,
        run["runId"],
        lambda *args: None,
        feeds={"fixture": "okay"},
        fetch=lambda url: records,
    )
    url = f"/v1/research/runs/{run['runId']}/findings"
    first = client.get(url, headers=HEADERS).json()
    assert len(first["items"]) == 24
    cursor = first["nextCursor"]
    assert isinstance(cursor, str)
    second = client.get(url, headers=HEADERS, params={"cursor": cursor}).json()
    assert len(second["items"]) == 6
    assert not set(row["id"] for row in first["items"]) & set(row["id"] for row in second["items"])
    assert (
        client.get(url, headers=HEADERS, params={"cursor": cursor, "q": "changed"}).status_code
        == 422
    )
    assert client.get(url, headers=HEADERS, params={"cursor": "invalid"}).status_code == 422


def test_idempotent_run_retains_all_dispositions(client):
    first = client.post("/v1/research/runs", headers=HEADERS, json={})
    assert first.status_code == 202, first.text
    assert client.post("/v1/research/runs", headers=HEADERS, json={}).json() == first.json()
    now = datetime.now(UTC)
    captured = [
        {
            "url": "https://github.blog/fresh-code",
            "title": "New AI code integration available",
            "summary": "Developer release API evidence " * 50,
            "published": (now - timedelta(hours=1)).isoformat(),
        },
        {
            "url": "https://github.blog/stale-code",
            "title": "AI code release",
            "summary": "Older",
            "published": (now - timedelta(days=3)).isoformat(),
        },
        {"url": "https://github.blog/undated", "title": "AI code release", "summary": "No date"},
        {
            "url": "https://github.blog/unrelated",
            "title": "Holiday recipe",
            "published": (now - timedelta(hours=2)).isoformat(),
        },
    ]

    def fetch(url):
        if url == "failed":
            raise TimeoutError("offline")
        return captured + [captured[0]]  # Repeated entries must not inflate source coverage.

    factory = scoped_factory(client.app.state.session_factory, LEGACY_WORKSPACE)
    result = collect_run(
        factory,
        first.json()["runId"],
        lambda *args: None,
        feeds={"fixture": "okay", "unavailable": "failed"},
        fetch=fetch,
    )
    assert result["counts"] == {
        "usable": 1,
        "outside_window": 1,
        "date_unverified": 1,
        "excluded_irrelevant": 1,
    }
    assert result["coverage"]["unavailable"]["status"] == "unavailable"
    # A recovered worker replay retains the same identities instead of duplicating topics.
    replay = collect_run(
        factory, first.json()["runId"], lambda *args: None, feeds={"fixture": "okay"}, fetch=fetch
    )
    assert replay["coverage"]["fixture"]["captured"] == 4
    response = client.get(f"/v1/research/runs/{first.json()['runId']}/findings", headers=HEADERS)
    assert response.status_code == 200, response.text
    assert response.json()["total"] == 4
    fresh = next(row for row in response.json()["items"] if row["disposition"] == "usable")
    assert fresh["evidence"]["claims_verified"] is False
    assert fresh["dimensions"]["developer_relevance"] == 1
    assert fresh["publishedAt"] and fresh["capturedAt"]


def test_research_rejects_unsupported_options_without_enqueuing(client):
    response = client.post(
        "/v1/research/runs", headers=HEADERS, json={"window": "last_24_hours", "invented": True}
    )
    assert response.status_code == 422
    with client.app.state.session_factory() as db:
        assert db.query(Job).count() == 0


def test_history_cursor_exposes_older_runs_and_handles_equal_timestamps(client):
    import uuid

    from devai.models.studio import ResearchRun

    now = datetime.now(UTC)
    with client.app.state.session_factory.begin() as db:
        for index in range(30):
            job = Job(id=str(uuid.uuid4()), kind="research_v4", status="completed")
            db.add(job)
            db.flush()
            db.add(
                ResearchRun(
                    id=str(uuid.uuid4()),
                    workspace_id=LEGACY_WORKSPACE,
                    job_id=job.id,
                    window_start=now - timedelta(hours=24),
                    window_end=now,
                    created_by="development",
                    created_at=now,
                )
            )
    first = client.get("/v1/research/runs", headers=HEADERS).json()
    assert len(first["items"]) == 24
    second = client.get(
        "/v1/research/runs", headers=HEADERS, params={"cursor": first["nextCursor"]}
    ).json()
    assert len(second["items"]) == 6
    assert not {row["id"] for row in first["items"]} & {row["id"] for row in second["items"]}
    assert second["nextCursor"] is None
    assert (
        client.get("/v1/research/runs", headers=HEADERS, params={"cursor": "bad"}).status_code
        == 422
    )
