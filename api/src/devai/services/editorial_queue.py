"""Topic-first discovery: never generate a carousel without a human selection."""

import uuid
from datetime import UTC, datetime, timedelta
from difflib import SequenceMatcher

from devai.models.editorial import EditorialTopic
from devai.services.research import discover
from devai.services.source_urls import canonical_source_url

VALID_STATUSES = frozenset({"queued", "selected", "archived"})


def collect_topics(session_factory, *, now=None, discover_fn=None):
    current = now or datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    report = (discover_fn or discover)(now=current)
    articles = report.get("articles", [])
    created = []
    skipped = []
    with session_factory.begin() as db:
        existing = db.query(EditorialTopic).all()
        known_urls = {topic.source_url for topic in existing}
        known_titles = [topic.title.casefold() for topic in existing]
        for article in articles:
            try:
                url = canonical_source_url(article.get("url", ""))
            except ValueError:
                continue
            title = article.get("title", "").strip()
            published = article.get("published_at")
            if not title or not isinstance(published, datetime):
                skipped.append(url)
                continue
            if published.tzinfo is None:
                published = published.replace(tzinfo=UTC)
            if published > current + timedelta(hours=1) or published < current - timedelta(days=14):
                skipped.append(url)
                continue
            if url in known_urls or any(
                SequenceMatcher(None, title.casefold(), old).ratio() >= 0.90
                for old in known_titles
            ):
                skipped.append(url)
                continue
            age = max(0, (current - published).total_seconds() / 3600)
            topic = EditorialTopic(
                id=str(uuid.uuid4()),
                source_url=url,
                title=title[:500],
                source_name=article.get("source", "Unknown")[:200],
                summary=article.get("summary", "")[:4000],
                angle="Engineering implications, original architecture and tested code",
                published_at=published,
                discovered_at=current,
                status="queued",
                priority=max(0, round(100 - age)),
            )
            db.add(topic)
            known_urls.add(url)
            known_titles.append(title.casefold())
            created.append(topic.id)
    return {"created_topic_ids": created, "skipped_urls": skipped, "warnings": report.get("errors", [])}


def list_topics(session_factory):
    with session_factory() as db:
        rows = db.query(EditorialTopic).order_by(
            EditorialTopic.priority.desc(), EditorialTopic.discovered_at.desc()
        ).all()
        return [
            {
                "id": row.id, "title": row.title, "source_url": row.source_url,
                "source_name": row.source_name, "summary": row.summary,
                "angle": row.angle, "status": row.status, "priority": row.priority,
                "published_at": row.published_at.isoformat() if row.published_at else None,
                "discovered_at": row.discovered_at.isoformat(),
            }
            for row in rows
        ]


def set_topic_status(session_factory, topic_id, status):
    if status not in VALID_STATUSES:
        raise ValueError("Unsupported editorial status")
    with session_factory.begin() as db:
        topic = db.get(EditorialTopic, topic_id)
        if topic is None:
            return False
        topic.status = status
    return True
