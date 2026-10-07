"""Persistent primary-source research, priority ranking and deduplication."""

import json
import uuid
from datetime import UTC, datetime, timedelta
from difflib import SequenceMatcher
from urllib.parse import urlsplit

from sqlalchemy.exc import IntegrityError

from devai.models import ArticleEvidence, Audit, Post, Slide, SourceCandidate, Topic
from devai.services.daily import _safe_article_evidence
from devai.services.generation import generate
from devai.services.research import ARTICLE_HOSTS, classify_topic, discover
from devai.services.source_urls import canonical_source_url
from devai.services.verification import verify_copy


def serialise_topic(topic: Topic) -> dict:
    data = {
        k: getattr(topic, k)
        for k in (
            "id",
            "url",
            "title",
            "source",
            "excerpt",
            "category",
            "priority",
            "selected",
            "status",
            "verification",
            "published_at",
            "retrieved_at",
            "post_id",
            "error",
        )
    }
    for key in ("published_at", "retrieved_at"):
        value = data[key]
        if value and value.tzinfo is None:
            data[key] = value.replace(tzinfo=UTC)
    return data


def research_queue(session_factory, *, progress=lambda *_: None, discover_fn=None) -> dict:
    now = datetime.now(UTC)
    report = (discover_fn or discover)(now=now)
    report.setdefault("errors", [])
    created, skipped = [], []
    articles = report.get("articles", [])
    for index, article in enumerate(articles):
        progress(index, max(1, len(articles)), "Checking primary-source evidence")
        try:
            url = canonical_source_url(article["url"])
        except ValueError:
            continue
        published = article.get("published_at")
        if not isinstance(published, datetime):
            continue
        published = published.replace(tzinfo=UTC) if published.tzinfo is None else published
        if not timedelta(days=-1) <= now - published <= timedelta(days=14):
            continue
        host = urlsplit(url).hostname
        if host not in ARTICLE_HOSTS.get(article.get("source"), set()):
            continue
        with session_factory() as db:
            titles = [p.title for p in db.query(Post).all()] + [
                t.title for t in db.query(Topic).all()
            ]
            if (
                db.query(Topic).filter_by(url=url).first()
                or db.query(SourceCandidate).filter_by(url=url).first()
                or any(
                    SequenceMatcher(None, article["title"].casefold(), title.casefold()).ratio()
                    >= 0.90
                    for title in titles
                )
            ):
                skipped.append(url)
                continue
        excerpt = _safe_article_evidence(article)
        if len(excerpt) < 240:
            report["errors"].append(f"{article['source']}: insufficient source evidence")
            continue
        category = classify_topic(article["title"], excerpt)
        freshness = max(0, 35 - max(0, (now - published).days) * 2)
        priority = 40 + freshness + (15 if category in {"tutorial", "architecture"} else 5)
        topic_id = str(uuid.uuid4())
        try:
            with session_factory.begin() as db:
                db.add(
                    Topic(
                        id=topic_id,
                        url=url,
                        title=article["title"][:500],
                        source=article["source"],
                        excerpt=excerpt,
                        category=category,
                        priority=min(100, priority),
                        verification="primary_source",
                        published_at=published,
                        retrieved_at=now,
                    )
                )
            created.append(topic_id)
        except IntegrityError:
            skipped.append(url)
    progress(len(articles), max(1, len(articles)), "Research saved to topic queue")
    if not created and not skipped:
        raise ValueError(
            "No dated primary source with enough readable evidence was found. Retry research or add a verified source manually."
        )
    return {
        "created_topic_ids": created,
        "skipped_urls": skipped,
        "warnings": report.get("errors", []),
    }


def create_from_topic(
    session_factory, topic_id: str, *, slide_count: int = 8, job_id: str | None = None
) -> dict:
    with session_factory.begin() as db:
        topic = db.query(Topic).filter_by(id=topic_id).with_for_update().first()
        if not topic:
            raise LookupError("Topic not found")
        if topic.post_id:
            return {"post_id": topic.post_id}
        if topic.verification not in {"primary_source", "human_verified"}:
            raise ValueError("Review and verify the source before generating")
        if topic.status == "archived" or (topic.job_id and topic.job_id != job_id):
            raise ValueError("Topic is archived or already being generated")
        topic.status, topic.job_id, topic.error = "generating", job_id, None
        packet = serialise_topic(topic)
        angles = [
            e.editorial_angle
            for e in db.query(ArticleEvidence)
            .order_by(ArticleEvidence.created_at.desc())
            .limit(20)
            .all()
        ]
    content = generate(
        packet["title"],
        packet["url"],
        packet["excerpt"],
        topic=packet["category"],
        prior_angles=angles,
        slide_count=slide_count,
    )
    report = verify_copy(packet["excerpt"], content, packet["url"])
    if not report["supported"]:
        raise ValueError("Source grounding failed: " + "; ".join(report["issues"])[:800])
    if not all(s.get("visual_direction") for s in content["slides"]):
        raise ValueError("Generation must provide an individual art direction for every slide")
    new_copy = " ".join(s["headline"] + " " + s["body"] for s in content["slides"]).casefold()
    with session_factory.begin() as db:
        topic = db.query(Topic).filter_by(id=topic_id).with_for_update().first()
        if topic.post_id:
            return {"post_id": topic.post_id}
        if topic.job_id != job_id or topic.status != "generating":
            raise ValueError("Topic ownership changed during generation; discard stale copy")
        for existing in db.query(Post).all():
            text = " ".join(
                (s.headline or "") + " " + (s.body or "")
                for s in db.query(Slide).filter_by(post_id=existing.id).all()
            ).casefold()
            if text and SequenceMatcher(None, new_copy, text).ratio() >= 0.85:
                raise ValueError(
                    "Generated copy overlaps an existing carousel; choose a different topic or angle"
                )
        post_id = str(uuid.uuid4())
        db.add(
            Post(
                id=post_id,
                title=content["title"],
                caption=content["caption"],
                verification_json=json.dumps(report),
            )
        )
        db.add(
            SourceCandidate(
                id=str(uuid.uuid4()),
                url=packet["url"],
                title=packet["title"],
                source=packet["source"],
                post_id=post_id,
            )
        )
        db.add(
            ArticleEvidence(
                id=str(uuid.uuid4()),
                post_id=post_id,
                source_url=packet["url"],
                source_title=packet["title"],
                source_name=packet["source"],
                excerpt=packet["excerpt"],
                published_at=packet["published_at"],
                retrieved_at=packet["retrieved_at"],
                topic=packet["category"],
                editorial_angle=content["editorial_angle"],
            )
        )
        for index, slide in enumerate(content["slides"], 1):
            db.add(
                Slide(
                    id=str(uuid.uuid4()),
                    post_id=post_id,
                    position=f"{index:03d}",
                    headline=slide["headline"],
                    body=slide["body"],
                    visual_direction=slide["visual_direction"],
                    composition_mode="ai_native",
                )
            )
        topic.status, topic.post_id, topic.selected = "used", post_id, False
        db.add(
            Audit(
                id=str(uuid.uuid4()),
                post_id=post_id,
                event="Grounded carousel generated from topic queue; human review required",
            )
        )
    return {"post_id": post_id, "slide_count": len(content["slides"])}
