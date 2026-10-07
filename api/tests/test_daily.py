from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from devai.core.database import Base
from devai.models import ArticleEvidence, Audit, DailyRun, Post, Slide, SourceCandidate
from devai.services.daily import _reserve_run, create_additional_post, ingest


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


def test_manual_retry_can_bypass_scheduler_cooldown_once():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)
    now = datetime(2026, 10, 7, 12, tzinfo=UTC)
    with session.begin() as db:
        db.add(
            DailyRun(
                id="failed-run",
                local_date="2026-10-07",
                timezone="UTC",
                status="failed",
                attempt_count=1,
                started_at=now,
                finished_at=now,
                error="RuntimeError: temporary provider failure",
            )
        )

    _, scheduler_claimed, _ = _reserve_run(session, now.date(), "UTC", now)
    _, manual_claimed, _ = _reserve_run(session, now.date(), "UTC", now, allow_early_retry=True)

    assert not scheduler_claimed
    assert manual_claimed
    with session() as db:
        assert db.get(DailyRun, "failed-run").attempt_count == 2


def test_additional_research_creates_separate_draft_and_skips_used_sources():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)
    now = datetime(2026, 10, 7, 12, tzinfo=UTC)
    article = {
        "title": "A new executable AI workflow for software engineering",
        "url": "https://example.com/ai-workflow",
        "source": "Example Engineering",
        "published_at": datetime(2026, 10, 7, 10, tzinfo=UTC),
        "summary": "This source explains a new executable AI workflow for software engineering. "
        * 8,
    }
    generated = {
        "title": "Build safer AI engineering workflows",
        "caption": "A practical look at executable AI workflows.",
        "editorial_angle": "How do executable primitives make AI workflows safer?",
        "slides": [
            {
                "headline": f"Slide {n}",
                "body": "Useful engineering detail",
                "visual_direction": f"Art {n}",
            }
            for n in range(1, 9)
        ],
    }
    calls = []

    def generate_fn(title, url, excerpt, **kwargs):
        calls.append((title, url, kwargs))
        return generated

    result = create_additional_post(
        session,
        now=now,
        discover_fn=lambda **_: {"articles": [article], "errors": []},
        generate_fn=generate_fn,
    )
    with session() as db:
        post = db.get(Post, result["id"])
        assert post.status == "draft"
        assert db.query(Slide).filter_by(post_id=post.id).count() == 8
        assert db.query(ArticleEvidence).filter_by(post_id=post.id).count() == 1
        assert db.query(DailyRun).count() == 0

    import pytest

    with pytest.raises(RuntimeError, match="No new recent source"):
        create_additional_post(
            session,
            now=now,
            discover_fn=lambda **_: {"articles": [article], "errors": []},
            generate_fn=generate_fn,
        )
    assert len(calls) == 1
