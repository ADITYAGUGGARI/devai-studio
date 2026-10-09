"""Real persistence and ranking with isolated external source fixtures."""

from datetime import UTC, datetime, timedelta

import pytest

from devai.core.workspaces import scoped_factory
from devai.models import Job
from devai.models.studio import LEGACY_WORKSPACE
from devai.services.jobs import work_once
from devai.services.research_runs import collect_run

HEADERS = {"x-api-key": "test-secret", "Idempotency-Key": "research-one"}


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
        return captured

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
    collect_run(
        factory, first.json()["runId"], lambda *args: None, feeds={"fixture": "okay"}, fetch=fetch
    )
    response = client.get(f"/v1/research/runs/{first.json()['runId']}/findings", headers=HEADERS)
    assert response.status_code == 200, response.text
    assert response.json()["total"] == 4
    fresh = next(row for row in response.json()["items"] if row["disposition"] == "usable")
    assert fresh["evidence"]["claims_verified"] is False
    assert fresh["dimensions"]["developer_relevance"] == 1
    assert fresh["publishedAt"] and fresh["capturedAt"]
