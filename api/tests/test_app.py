import os
import subprocess
import sys

from devai.routes import research

HEADERS = {"x-api-key": "test-secret"}


def test_import_does_not_create_database(tmp_path):
    database = tmp_path / "untouched.sqlite"
    environment = {**os.environ, "DATABASE_URL": f"sqlite:///{database}"}
    subprocess.run(
        [sys.executable, "-c", "import devai.main; import devai.scheduler"],
        env=environment,
        check=True,
    )
    assert not database.exists()


def test_ingest_route_uses_application_database(client, monkeypatch):
    from devai.services import daily

    monkeypatch.setattr(
        daily,
        "discover",
        lambda: {
            "articles": [
                {
                    "title": "AI coding tools",
                    "url": "https://example.com/ai-tools",
                    "source": "Example",
                }
            ],
            "errors": [],
        },
    )
    response = client.post("/research/ingest", headers=HEADERS)
    assert response.status_code == 200
    assert len(response.json()["created_post_ids"]) == 1
    assert client.post("/research/ingest", headers=HEADERS).json()["created_post_ids"] == []
    assert client.get("/posts", headers=HEADERS).json()[0]["status"] == "draft"


def test_generation_route_saves_source_linked_draft(client, monkeypatch):
    url = "https://example.com/agent"
    monkeypatch.setattr(
        research,
        "generate",
        lambda *args: {
            "title": "AI agents in code review",
            "caption": f"Analysis. Source: {url}",
            "slides": [
                {"headline": "Review workflows", "body": "Measure quality on your own workload."}
                for _ in range(8)
            ],
        },
    )
    response = client.post(
        "/research/generate",
        headers=HEADERS,
        json={"title": "AI agents in code review", "url": url, "excerpt": "Source material. " * 20},
    )
    assert response.status_code == 200
    assert response.json()["fact_check_required"]
    post = client.get("/posts", headers=HEADERS).json()[0]
    assert len(post["slides"]) == 8
    assert post["status"] == "draft"
    assert url in post["caption"]
