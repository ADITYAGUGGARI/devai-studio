from devai.services.research import create_editorial_draft, discover


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
