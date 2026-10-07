"""Compatibility API for the upstream editorial queue, backed by the unified topic table."""

import uuid
from datetime import UTC, datetime, timedelta
from difflib import SequenceMatcher
from urllib.parse import urlsplit

from devai.models import SourceCandidate, Topic
from devai.services.research import ARTICLE_HOSTS, classify_topic, discover
from devai.services.source_urls import canonical_source_url

VALID_STATUSES = frozenset({"queued", "selected", "archived"})


def collect_topics(session_factory, *, now=None, discover_fn=None):
    current = now or datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    report = (discover_fn or discover)(now=current)
    created, skipped = [], []
    with session_factory.begin() as db:
        existing = db.query(Topic).all()
        known_urls = {t.url for t in existing} | {s.url for s in db.query(SourceCandidate).all()}
        known_titles = [t.title.casefold() for t in existing]
        for article in report.get("articles", []):
            try:
                url = canonical_source_url(article.get("url", ""))
            except ValueError:
                continue
            title, published = article.get("title", "").strip(), article.get("published_at")
            if not title or not isinstance(published, datetime):
                skipped.append(url)
                continue
            published = published.replace(tzinfo=UTC) if published.tzinfo is None else published
            if (
                not timedelta(hours=-1) <= current - published <= timedelta(days=14)
                or url in known_urls
                or any(
                    SequenceMatcher(None, title.casefold(), old).ratio() >= 0.90
                    for old in known_titles
                )
            ):
                skipped.append(url)
                continue
            excerpt = article.get("summary", "")[:6000]
            verified = len(excerpt) >= 240 and urlsplit(url).hostname in ARTICLE_HOSTS.get(
                article.get("source"), set()
            )
            topic_id = str(uuid.uuid4())
            priority = max(0, round(100 - max(0, (current - published).total_seconds() / 3600)))
            db.add(
                Topic(
                    id=topic_id,
                    url=url,
                    title=title[:500],
                    source=article.get("source", "Unknown")[:200],
                    excerpt=excerpt,
                    category=classify_topic(title, excerpt),
                    priority=priority,
                    verification="primary_source" if verified else "unverified",
                    published_at=published,
                    retrieved_at=current,
                )
            )
            known_urls.add(url)
            known_titles.append(title.casefold())
            created.append(topic_id)
    return {
        "created_topic_ids": created,
        "skipped_urls": skipped,
        "warnings": report.get("errors", []),
    }


def list_topics(session_factory):
    with session_factory() as db:
        return [
            {
                "id": t.id,
                "title": t.title,
                "source_url": t.url,
                "source_name": t.source,
                "summary": t.excerpt,
                "angle": "Original developer-focused analysis from source evidence",
                "status": "selected" if t.selected else t.status,
                "priority": t.priority,
                "published_at": t.published_at.isoformat() if t.published_at else None,
                "discovered_at": t.retrieved_at.isoformat(),
            }
            for t in db.query(Topic)
            .order_by(Topic.priority.desc(), Topic.retrieved_at.desc())
            .all()
        ]


def set_topic_status(session_factory, topic_id, status):
    if status not in VALID_STATUSES:
        raise ValueError("Unsupported editorial status")
    with session_factory.begin() as db:
        topic = db.query(Topic).filter_by(id=topic_id).with_for_update().first()
        if not topic:
            return False
        if topic.status in {"used", "generating"}:
            raise ValueError("Generated or generating topics cannot be reset")
        topic.status = "queued" if status == "selected" else status
        topic.selected = status == "selected"
    return True
