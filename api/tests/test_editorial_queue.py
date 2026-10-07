from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from devai.core.database import Base
from devai.services.editorial_queue import collect_topics, list_topics, set_topic_status


def test_topic_discovery_is_idempotent_and_never_creates_posts():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    now = datetime(2026, 10, 7, 12, tzinfo=UTC)
    article = {
        "title": "New open model for software developers",
        "url": "https://example.com/ai",
        "source": "Example",
        "summary": "Primary-source summary",
        "published_at": now - timedelta(hours=2),
    }

    def fake(**kwargs):
        return {"articles": [article], "errors": []}

    first = collect_topics(sessions, now=now, discover_fn=fake)
    second = collect_topics(sessions, now=now, discover_fn=fake)
    assert len(first["created_topic_ids"]) == 1
    assert second["created_topic_ids"] == []
    topics = list_topics(sessions)
    assert len(topics) == 1 and topics[0]["status"] == "queued"
    assert set_topic_status(sessions, topics[0]["id"], "selected")
    assert list_topics(sessions)[0]["status"] == "selected"
    from devai.models import Post

    with sessions() as db:
        assert db.query(Post).count() == 0


def test_invalid_status_rejected():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    try:
        set_topic_status(sessions, "missing", "published_without_approval")
        assert False
    except ValueError:
        pass
