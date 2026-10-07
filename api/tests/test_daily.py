from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from devai.core.database import Base
from devai.models import Audit, Post, Slide, SourceCandidate
from devai.services.daily import ingest


def test_daily_ingest_idempotent_and_unapproved():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)
    article = {
        "title": "New AI agent tools for software developers",
        "url": "https://example.com/new-agent",
        "source": "Example",
    }
    first = ingest(session, SourceCandidate, Post, Slide, Audit, articles=[article])
    second = ingest(session, SourceCandidate, Post, Slide, Audit, articles=[article])
    assert len(first["created_post_ids"]) == 1
    assert second["created_post_ids"] == []
    assert second["skipped_urls"] == [article["url"]]
    with session() as db:
        posts = db.query(Post).all()
        assert len(posts) == 1 and posts[0].status == "draft"
        assert db.query(Slide).filter_by(post_id=posts[0].id).count() == 8
        assert db.query(Audit).filter_by(post_id=posts[0].id).count() == 1


def test_scheduler_runs_once_per_day():
    import datetime as dt

    from devai.scheduler import should_run

    today = dt.date(2026, 10, 7)
    assert not should_run(dt.datetime(2026, 10, 7, 7, 59), None)
    assert should_run(dt.datetime(2026, 10, 7, 8, 0), None)
    assert not should_run(dt.datetime(2026, 10, 7, 10, 0), today)
