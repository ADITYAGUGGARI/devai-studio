import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from devai.services import research
from devai.services.research import create_editorial_draft, discover


def mock_transport(monkeypatch, handler):
    client_type = httpx.Client
    monkeypatch.setattr(
        research.httpx,
        "Client",
        lambda **kwargs: client_type(transport=httpx.MockTransport(handler), **kwargs),
    )


def test_draft_has_eight_slides_and_source():
    d = create_editorial_draft(
        {"title": "AI coding update", "url": "https://example.com/announcement"}
    )
    assert len(d["slides"]) == 8
    assert "https://example.com/announcement" in d["caption"]
    assert "primary source" in d["slides"][1]["body"].lower()


def test_feed_failure_does_not_invent_news(monkeypatch):
    from devai.services import research

    def fail(*args, **kwargs):
        raise TimeoutError("offline")

    monkeypatch.setattr(research, "fetch_feed", fail)
    d = discover({"test": "https://example.com/feed"})
    assert d["articles"] == []
    assert len(d["errors"]) == 1


def test_large_feed_is_complete_and_prefers_full_rss_content(monkeypatch):
    xml = (
        '<rss xmlns:content="http://purl.org/rss/1.0/modules/content/"><channel><item>'
        "<title>AI coding update</title><link>https://github.blog/story/</link>"
        "<description>Short summary</description><content:encoded><![CDATA[<p>"
        + "Official evidence. " * 65_000
        + "</p>]]></content:encoded></item></channel></rss>"
    )
    assert len(xml) > 1_000_000
    mock_transport(
        monkeypatch,
        lambda request: httpx.Response(
            200, text=xml, headers={"content-type": "application/rss+xml"}
        ),
    )
    items = research.fetch_feed("https://github.blog/feed/")
    assert len(items) == 1
    assert research.clean_excerpt(items[0]["summary"]).startswith("Official evidence.")


def test_all_bounded_feed_entries_are_retained(monkeypatch):
    xml = (
        "<rss><channel>"
        + "".join(
            f"<item><title>AI code {index}</title><link>https://github.blog/story-{index}</link></item>"
            for index in range(75)
        )
        + "</channel></rss>"
    )
    mock_transport(
        monkeypatch,
        lambda request: httpx.Response(
            200, text=xml, headers={"content-type": "application/rss+xml"}
        ),
    )
    assert len(research.fetch_feed("https://github.blog/feed/")) == 75


def test_rdf_feed_is_supported(monkeypatch):
    rdf = '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns="http://purl.org/rss/1.0/" xmlns:dc="http://purl.org/dc/elements/1.1/"><item><title>AI developer paper</title><link>https://arxiv.org/abs/2610.12345</link><description>Source excerpt</description><dc:date>2026-10-08T00:00:00Z</dc:date></item></rdf:RDF>'
    mock_transport(
        monkeypatch,
        lambda request: httpx.Response(
            200, text=rdf, headers={"content-type": "application/rss+xml"}
        ),
    )
    item = research.fetch_feed("https://rss.arxiv.org/rss/cs.SE")[0]
    assert item["title"] == "AI developer paper"
    assert item["summary"] == "Source excerpt"
    assert item["published"] == "2026-10-08T00:00:00Z"


def test_atom_escaped_html_is_readable_evidence(monkeypatch):
    xml = """<feed xmlns="http://www.w3.org/2005/Atom"><entry>
    <title>AI developer tools</title><link href="https://github.com/openai/codex/releases/tag/v1"/>
    <updated>2026-10-07T10:00:00Z</updated>
    <content type="html">&lt;p&gt;New coding features&lt;/p&gt;&lt;p&gt;Improved tools&lt;/p&gt;</content>
    </entry></feed>"""
    mock_transport(
        monkeypatch,
        lambda request: httpx.Response(
            200, text=xml, headers={"content-type": "application/atom+xml"}
        ),
    )
    item = research.fetch_feed("https://github.com/openai/codex/releases.atom")[0]
    excerpt = research.clean_excerpt(item["summary"])
    assert "New coding features" in excerpt and "Improved tools" in excerpt
    assert "<p>" not in excerpt and "&lt;" not in excerpt


def test_feed_follows_only_same_publisher_redirect(monkeypatch):
    requests = []

    def respond(request):
        requests.append(str(request.url))
        if request.url.path == "/feed":
            return httpx.Response(301, headers={"location": "/feed/"})
        return httpx.Response(
            200, text="<rss><channel/></rss>", headers={"content-type": "text/xml"}
        )

    mock_transport(monkeypatch, respond)
    assert research.fetch_feed("https://github.blog/feed") == []
    assert requests == ["https://github.blog/feed", "https://github.blog/feed/"]


@pytest.mark.parametrize(
    "destination",
    [
        "http://github.blog/feed/",
        "https://127.0.0.1/feed/",
        "https://github.blog:8080/feed/",
        "https://user:password@github.blog/feed/",
    ],
)
def test_redirect_to_unsafe_destination_is_not_requested(monkeypatch, destination):
    requests = []

    def respond(request):
        requests.append(str(request.url))
        return httpx.Response(302, headers={"location": destination})

    mock_transport(monkeypatch, respond)
    with pytest.raises(ValueError, match="permitted HTTPS"):
        research.fetch_feed("https://github.blog/feed/")
    assert len(requests) == 1


def test_download_limit_fails_explicitly_instead_of_parsing_truncated_xml():
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200, content=b"x" * 101, headers={"content-type": "text/xml"}
            )
        )
    ) as client:
        with pytest.raises(ValueError, match="100-byte download limit"):
            research._fetch_bounded(client, "https://github.blog/feed/", 100, {"github.blog"})


def test_sufficient_feed_evidence_does_not_need_article_access(monkeypatch):
    def unexpected(*_):
        raise AssertionError("Full feed evidence should not require another network request")

    monkeypatch.setattr(research, "fetch_article", unexpected)
    article = {"source": "GitHub Blog", "summary": "Verified feed evidence. " * 30}
    warnings = []
    assert research.article_evidence(article, warnings) == article["summary"].strip()
    assert warnings == []


def test_short_blocked_article_reports_http_reason_without_using_it_as_evidence(monkeypatch):
    mock_transport(monkeypatch, lambda request: httpx.Response(403, text="Blocked"))
    article = {
        "source": "OpenAI News",
        "url": "https://openai.com/index/story/",
        "summary": "Short",
    }
    warnings = []
    assert research.article_evidence(article, warnings) == "Short"
    assert warnings == ["OpenAI News: article HTTP 403; insufficient readable source evidence"]


def test_daily_summary_preserves_history_and_returns_latest_research_job(client):
    from devai.models import DailyRun, Job

    now = datetime.now(UTC)
    historical_result = {"post_id": "existing-draft", "warnings": ["GitHub Blog: ParseError"]}
    factory = client.app.state.session_factory
    with factory.begin() as db:
        db.add(
            DailyRun(
                id="old-daily",
                local_date=now.date().isoformat(),
                timezone="America/Chicago",
                status="completed_with_warnings",
                started_at=now - timedelta(hours=2),
                finished_at=now - timedelta(hours=1),
                result_json=json.dumps(historical_result),
            )
        )
        db.add(
            Job(
                id="old-refresh",
                kind="research",
                status="completed",
                created_at=now - timedelta(minutes=20),
            )
        )
        db.add(
            Job(
                id="current-refresh",
                kind="research",
                status="running",
                created_at=now - timedelta(minutes=10),
            )
        )
        db.add(Job(id="newer-artwork", kind="artwork", status="completed", created_at=now))
    response = client.get("/research/daily/latest", headers={"X-API-Key": "test-secret"})
    assert response.status_code == 200
    summary = response.json()
    assert summary["latest_research"]["id"] == "current-refresh"
    assert summary["latest_research"]["status"] == "running"
    assert summary["run"]["result"] == historical_result
    with factory() as db:
        assert json.loads(db.get(DailyRun, "old-daily").result_json) == historical_result


def test_daily_summary_without_jobs_remains_compatible(client):
    response = client.get("/research/daily/latest", headers={"X-API-Key": "test-secret"})
    assert response.status_code == 200
    assert response.json()["latest_research"] is None
    assert response.json()["run"] is None
