"""Frozen rolling-window discovery, including excluded and inaccessible findings."""

import json
import uuid
import xml.etree.ElementTree as ET
from datetime import UTC, datetime

import httpx

from devai.models import Topic
from devai.models.studio import Finding, ResearchRun
from devai.services.research import (
    FEEDS,
    RELEVANT_TITLE,
    classify_topic,
    clean_excerpt,
    fetch_feed,
    parse_published,
    source_error,
)
from devai.services.source_urls import canonical_source_url

WEIGHTS = {
    "developer_relevance": 25,
    "practical_impact": 20,
    "source_strength": 20,
    "recency": 15,
    "novelty": 10,
    "evidence_completeness": 10,
}


def aware(value):
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def rank(title, excerpt, published, window_end, duplicate=False):
    text = f"{title} {excerpt}".lower()
    developer = sum(
        word in text for word in ("code", "software", "developer", "api", "agent", "engineering")
    )
    practical = sum(
        word in text
        for word in ("release", "available", "benchmark", "production", "security", "integration")
    )
    completeness = min(len(excerpt) / 1200, 1)
    dimensions = {
        "developer_relevance": min(developer / 3, 1),
        "practical_impact": min(practical / 2, 1),
        # Publisher identity is not a verification of its claims.
        "source_strength": 0.6 if excerpt else 0.2,
        "recency": max(0, 1 - (aware(window_end) - aware(published)).total_seconds() / 86400)
        if published
        else 0,
        "novelty": 0 if duplicate else 1,
        "evidence_completeness": completeness,
    }
    return round(sum(WEIGHTS[key] * value for key, value in dimensions.items())), dimensions


def collect_run(factory, run_id, progress, *, feeds=None, fetch=None):
    catalog = FEEDS if feeds is None else feeds
    fetch = fetch or fetch_feed
    with factory() as db:
        run = db.get(ResearchRun, run_id)
        start, end = aware(run.window_start), aware(run.window_end)
        coverage = json.loads(run.coverage_json)
    for index, (source, url) in enumerate(catalog.items()):
        progress(index, len(catalog), f"Collecting {source}")
        try:
            items = fetch(url)
            captured = 0
            for item in items:
                try:
                    canonical = canonical_source_url(item["url"])
                except (ValueError, KeyError):
                    continue
                title = str(item.get("title", ""))[:500]
                excerpt = clean_excerpt(item.get("summary", ""))
                published = parse_published(item.get("published", ""))
                category = classify_topic(title, excerpt)
                relevant = bool(RELEVANT_TITLE.search(title))
                disposition = "usable"
                if not published:
                    disposition = "date_unverified"
                elif not start <= aware(published) <= end:
                    disposition = "outside_window"
                elif not relevant:
                    disposition = "excluded_irrelevant"
                with factory.begin() as db:
                    existing = (
                        db.query(Finding).filter_by(run_id=run_id, canonical_url=canonical).first()
                    )
                    if existing:
                        continue  # Same URL in two feeds is one captured identity.
                    topic = db.query(Topic).filter_by(url=canonical).first()
                    duplicate = topic is not None
                    if duplicate and disposition == "usable":
                        disposition = "duplicate"
                    score, dimensions = rank(title, excerpt, published, end, duplicate)
                    if disposition == "usable":
                        topic = Topic(
                            id=str(uuid.uuid4()),
                            url=canonical,
                            title=title,
                            source=source,
                            excerpt=excerpt,
                            category=category,
                            priority=score,
                            published_at=published,
                            verification="unverified",
                        )
                        db.add(topic)
                        db.flush()
                    db.add(
                        Finding(
                            id=str(uuid.uuid4()),
                            run_id=run_id,
                            canonical_url=canonical,
                            topic_id=topic.id if topic else None,
                            title=title,
                            source=source,
                            category=category,
                            published_at=published,
                            disposition=disposition,
                            duplicate_group_id=topic.id if duplicate else None,
                            score=score,
                            dimensions_json=json.dumps(dimensions),
                            evidence_json=json.dumps(
                                {
                                    "excerpt": excerpt,
                                    "kind": "feed_excerpt",
                                    "claims_verified": False,
                                    "captured_at": datetime.now(UTC).isoformat(),
                                    "reason": disposition,
                                }
                            ),
                        )
                    )
                captured += 1
            coverage[source] = {"status": "collected", "captured": captured}
        except (httpx.HTTPError, ET.ParseError, ValueError, TimeoutError) as exc:
            coverage[source] = {"status": "unavailable", "error": source_error(exc)}
        with factory.begin() as db:
            db.get(ResearchRun, run_id).coverage_json = json.dumps(coverage)
    progress(len(catalog), len(catalog), "Ranking snapshots saved")
    with factory() as db:
        counts = {}
        for finding in db.query(Finding).filter_by(run_id=run_id):
            counts[finding.disposition] = counts.get(finding.disposition, 0) + 1
    result = {
        "run_id": run_id,
        "counts": counts,
        "coverage": coverage,
        "coverage_limit": "Configured source feeds only; this is not exhaustive internet coverage.",
        "warnings": [
            f"{name}: {item['error']}"
            for name, item in coverage.items()
            if item["status"] == "unavailable"
        ],
    }
    if coverage and all(item["status"] == "unavailable" for item in coverage.values()):
        from devai.services.topics import ResearchEvidenceError

        raise ResearchEvidenceError(result)
    return result
