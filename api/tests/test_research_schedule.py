"""Real workspace persistence, clock boundaries, DST and durable scheduler reservations."""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime, timedelta

from devai.core.workspaces import scoped_factory
from devai.models import Job
from devai.models.studio import LEGACY_WORKSPACE, ResearchRun, Workspace
from devai.services.research_runs import collect_run
from devai.services.research_schedule import enqueue_workspace_schedule, scheduled_instant

HEADERS = {"x-api-key": "test-secret", "Idempotency-Key": "schedule-one"}


def settings_body(revision=1):
    return {
        "expectedRevision": revision,
        "researchEnabled": True,
        "researchLocalTime": "08:00",
        "timeZone": "America/Chicago",
        "categories": ["tools", "architecture"],
        "autoDraftOptions": {"enabled": False},
    }


def test_schedule_save_conflict_and_workspace_isolation(client):
    path = f"/v1/workspaces/{LEGACY_WORKSPACE}/settings"
    initial = client.get(path, headers=HEADERS)
    assert initial.status_code == 200
    assert not initial.json()["researchEnabled"]
    body = settings_body(initial.json()["revision"])
    saved = client.patch(path, headers=HEADERS, json=body)
    assert saved.status_code == 200, saved.text
    assert saved.json()["nextRunAt"]
    assert client.patch(path, headers=HEADERS, json=body).json() == saved.json()
    conflict = client.patch(
        path, headers={**HEADERS, "Idempotency-Key": "schedule-other"}, json=body
    )
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["server"]["revision"] == saved.json()["revision"]
    assert client.get("/v1/workspaces/foreign/settings", headers=HEADERS).status_code == 404
    assert (
        client.patch(path, headers=HEADERS, json={**body, "researchLocalTime": "25:00"}).status_code
        == 422
    )


def test_daily_schedule_is_once_per_studio_and_keeps_frozen_window(client):
    factory = client.app.state.session_factory
    now = datetime(2026, 10, 9, 14, 1, tzinfo=UTC)
    with factory.begin() as db:
        for identifier in ("scheduled-a", "scheduled-b"):
            db.add(
                Workspace(
                    id=identifier,
                    name=identifier,
                    settings_json=json.dumps(
                        {
                            "researchSchedule": {
                                **settings_body(),
                                "effectiveAfterUTC": (now - timedelta(days=1)).isoformat(),
                            }
                        }
                    ),
                )
            )
    first = enqueue_workspace_schedule(factory, "scheduled-a", now=now)
    assert first
    assert (
        enqueue_workspace_schedule(factory, "scheduled-a", now=now + timedelta(minutes=2)) == first
    )
    second = enqueue_workspace_schedule(factory, "scheduled-b", now=now)
    assert second["jobId"] != first["jobId"]
    with factory() as db:
        assert db.query(ResearchRun).filter(ResearchRun.created_by == "scheduler").count() == 2
        job = db.get(Job, first["jobId"])
        assert json.loads(job.payload_json)["categories"] == ["tools", "architecture"]
        original_key = job.active_key
    with factory.begin() as db:
        job = db.get(Job, first["jobId"])
        job.status, job.active_key = "failed", None
    retried = client.post(
        f"/jobs/{first['jobId']}/retry", headers={**HEADERS, "X-Workspace-ID": "scheduled-a"}
    )
    assert retried.status_code == 202, retried.text
    with factory() as db:
        assert db.get(Job, first["jobId"]).active_key == original_key
    assert datetime.fromisoformat(first["windowEndUTC"]) - datetime.fromisoformat(
        first["windowStartUTC"]
    ) == timedelta(hours=24)


def test_parallel_schedule_ticks_share_one_reservation(client):
    factory = client.app.state.session_factory
    now = datetime(2026, 10, 9, 14, 1, tzinfo=UTC)
    with factory.begin() as db:
        db.add(
            Workspace(
                id="parallel-schedule",
                name="Concurrent",
                settings_json=json.dumps(
                    {
                        "researchSchedule": {
                            **settings_body(),
                            "effectiveAfterUTC": (now - timedelta(days=1)).isoformat(),
                        }
                    }
                ),
            )
        )
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(
            pool.map(
                lambda _: enqueue_workspace_schedule(factory, "parallel-schedule", now=now),
                range(8),
            )
        )
    assert len({row["jobId"] for row in results}) == 1


def test_manual_research_freezes_saved_categories_without_losing_captured_findings(client):
    path = f"/v1/workspaces/{LEGACY_WORKSPACE}/settings"
    revision = client.get(path, headers=HEADERS).json()["revision"]
    response = client.patch(
        path, headers=HEADERS, json={**settings_body(revision), "categories": ["tools"]}
    )
    assert response.status_code == 200
    run = client.post(
        "/v1/research/runs", headers={**HEADERS, "Idempotency-Key": "manual-category-run"}, json={}
    ).json()
    now = datetime.now(UTC)
    records = [
        {
            "title": title,
            "summary": "Source fixture evidence " * 20,
            "url": f"https://github.blog/category-{index}",
            "published": (now - timedelta(hours=1)).isoformat(),
        }
        for index, title in enumerate(["AI SDK release", "AI code architecture for production"])
    ]
    result = collect_run(
        scoped_factory(client.app.state.session_factory, LEGACY_WORKSPACE),
        run["runId"],
        lambda *args: None,
        feeds={"fixture": "okay"},
        fetch=lambda _: records,
    )
    assert result["counts"] == {"usable": 1, "excluded_category": 1}
    findings = client.get(f"/v1/research/runs/{run['runId']}/findings", headers=HEADERS).json()
    assert findings["total"] == 2


def test_saving_after_todays_time_does_not_start_immediately(client):
    now = datetime(2026, 10, 9, 15, tzinfo=UTC)
    factory = client.app.state.session_factory
    with factory.begin() as db:
        db.add(
            Workspace(
                id="later",
                name="Later",
                settings_json=json.dumps(
                    {"researchSchedule": {**settings_body(), "effectiveAfterUTC": now.isoformat()}}
                ),
            )
        )
    assert enqueue_workspace_schedule(factory, "later", now=now) is None
    assert enqueue_workspace_schedule(factory, "later", now=now + timedelta(days=1))


def test_spring_gap_and_fall_fold_choose_one_daily_instant():
    assert scheduled_instant(date(2026, 3, 8), "02:30", "America/Chicago") == datetime(
        2026, 3, 8, 8, tzinfo=UTC
    )
    assert scheduled_instant(date(2026, 11, 1), "01:30", "America/Chicago") == datetime(
        2026, 11, 1, 6, 30, tzinfo=UTC
    )
