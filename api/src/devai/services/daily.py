"""Run at most one evidence-grounded carousel draft per local calendar day."""

import json
import os
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from difflib import SequenceMatcher
from zoneinfo import ZoneInfo

from sqlalchemy.exc import IntegrityError

from devai.models import ArticleEvidence, Audit, DailyRun, Post, Slide, SourceCandidate
from devai.services.generation import generate
from devai.services.research import (
    ARTICLE_HOSTS,
    classify_topic,
    create_editorial_draft,
    discover,
    fetch_article,
)
from devai.services.source_urls import canonical_source_url

# 6 news, 5 tutorials, 4 architecture explainers, 3 tools, 2 engineering insights.
# This shuffled 20-day rotation matches the creator's requested editorial mix.
EDITORIAL_CALENDAR = (
    "news",
    "tutorial",
    "architecture",
    "news",
    "tools",
    "tutorial",
    "news",
    "insight",
    "architecture",
    "tutorial",
    "news",
    "tools",
    "tutorial",
    "architecture",
    "news",
    "tutorial",
    "insight",
    "news",
    "tools",
    "architecture",
)


def ingest(session_factory, candidate_model, post_model, slide_model, audit_model, articles=None):
    """Import link-only research scaffolds for manual curation.

    This legacy endpoint is intentionally separate from the evidence-grounded
    daily pipeline: it creates unverified drafts and never calls a model.
    """
    articles = articles if articles is not None else discover().get("articles", [])
    created, skipped = [], []
    with session_factory.begin() as db:
        existing = {row[0] for row in db.query(candidate_model.url).all()}
        for article in articles:
            try:
                url = canonical_source_url(article.get("url", ""))
            except ValueError:
                continue
            if url in existing:
                skipped.append(url)
                continue
            payload = {
                **article,
                "url": url,
                "title": article.get("title", "AI developer story")[:160],
            }
            content = create_editorial_draft(payload)
            post_id = str(uuid.uuid4())
            db.add(post_model(id=post_id, title=content["title"], caption=content["caption"]))
            db.add(
                candidate_model(
                    id=str(uuid.uuid4()),
                    url=url,
                    title=payload["title"],
                    source=article.get("source", "Unknown")[:200],
                    post_id=post_id,
                )
            )
            for position, slide in enumerate(content["slides"], 1):
                db.add(
                    slide_model(
                        id=str(uuid.uuid4()),
                        post_id=post_id,
                        position=f"{position:03d}",
                        headline=slide["headline"],
                        body=slide["body"],
                        visual_direction=slide.get("visual_direction") or None,
                    )
                )
            db.add(
                audit_model(
                    id=str(uuid.uuid4()),
                    post_id=post_id,
                    event=f"Unverified link scaffold imported from {url}; manual review required",
                )
            )
            created.append(post_id)
            existing.add(url)
    return {"created_post_ids": created, "skipped_urls": skipped}


def topic_for_date(local_date):
    return EDITORIAL_CALENDAR[local_date.timetuple().tm_yday % len(EDITORIAL_CALENDAR)]


def _serialise_run(run):
    started = run.started_at
    if started.tzinfo is None:
        started = started.replace(tzinfo=UTC)
    stale = run.status == "running" and datetime.now(UTC) - started > timedelta(minutes=20)
    status = "failed" if stale else run.status
    finished_at = run.finished_at
    if finished_at and finished_at.tzinfo is None:
        finished_at = finished_at.replace(tzinfo=UTC)
    configuration_ready = bool(os.getenv("OPENAI_API_KEY", "").strip())
    configuration_error = "OPENAI_API_KEY is not configured" in (run.error or "")
    return {
        "id": run.id,
        "local_date": run.local_date,
        "timezone": run.timezone,
        "status": status,
        "attempt_count": run.attempt_count,
        "started_at": started.isoformat(),
        "finished_at": finished_at.isoformat() if finished_at else None,
        "retry_after": (
            (finished_at + timedelta(minutes=30)).isoformat()
            if (
                status == "failed"
                and finished_at
                and run.attempt_count < 3
                and not (configuration_error and configuration_ready)
            )
            else None
        ),
        "result": json.loads(run.result_json) if run.result_json else None,
        "error": "The previous run stopped before it finished." if stale else run.error,
    }


def latest_run(session_factory, timezone=None):
    with session_factory() as db:
        query = db.query(DailyRun)
        if timezone:
            query = query.filter_by(timezone=timezone)
        run = query.order_by(DailyRun.local_date.desc(), DailyRun.started_at.desc()).first()
        return _serialise_run(run) if run else None


def _reserve_run(session_factory, local_date, timezone, now, *, allow_early_retry=False):
    """Claim the local-day slot before network/model calls; recover stale attempts."""
    cutoff = now - timedelta(minutes=20)
    try:
        with session_factory.begin() as db:
            run = (
                db.query(DailyRun)
                .filter_by(local_date=local_date.isoformat(), timezone=timezone)
                .first()
            )
            if run and run.status == "completed":
                return run.id, False, _serialise_run(run)
            if run and run.status == "running":
                started = run.started_at
                if started.tzinfo is None:
                    started = started.replace(tzinfo=UTC)
                if started >= cutoff:
                    return run.id, False, _serialise_run(run)
            if run and run.status == "failed":
                configuration_error = "OPENAI_API_KEY is not configured" in (run.error or "")
                configuration_ready = bool(os.getenv("OPENAI_API_KEY", "").strip())
                if configuration_error and configuration_ready:
                    run.attempt_count = 0
                if run.attempt_count >= 3:
                    return run.id, False, _serialise_run(run)
                if run.finished_at:
                    finished = run.finished_at
                    if finished.tzinfo is None:
                        finished = finished.replace(tzinfo=UTC)
                    if (
                        now - finished < timedelta(minutes=30)
                        and not (configuration_error and configuration_ready)
                        and not allow_early_retry
                    ):
                        return run.id, False, _serialise_run(run)
            if run is None:
                run = DailyRun(
                    id=str(uuid.uuid4()),
                    local_date=local_date.isoformat(),
                    timezone=timezone,
                    status="running",
                    started_at=now,
                )
                db.add(run)
            else:
                run.status = "running"
                run.started_at = now
                run.finished_at = None
                run.result_json = None
                run.error = None
                run.attempt_count += 1
            run_id = run.id
        return run_id, True, None
    except IntegrityError:
        # A second worker that races the unique date/timezone constraint reads the
        # winner's claim rather than generating a second post.
        with session_factory() as db:
            run = (
                db.query(DailyRun)
                .filter_by(local_date=local_date.isoformat(), timezone=timezone)
                .one()
            )
            return run.id, False, _serialise_run(run)


def _finish_run(session_factory, run_id, *, status, result=None, error=None, now=None):
    with session_factory.begin() as db:
        run = db.get(DailyRun, run_id)
        run.status = status
        run.result_json = json.dumps(result, ensure_ascii=False) if result is not None else None
        run.error = error
        run.finished_at = now or datetime.now(UTC)
        return _serialise_run(run)


def _safe_article_evidence(article):
    excerpt = article.get("summary", "").strip()
    source = article.get("source", "")
    if source in ARTICLE_HOSTS:
        try:
            full_text = fetch_article(article)
            if len(full_text) > len(excerpt):
                excerpt = full_text
        except Exception:
            # An RSS summary can still support a draft; inaccessible pages remain
            # visible as the cited primary source and trigger human fact-checking.
            pass
    return excerpt[:6000]


def _recent_angles(session_factory, local_date, timezone):
    cutoff = (local_date - timedelta(days=90)).isoformat()
    with session_factory() as db:
        runs = (
            db.query(DailyRun)
            .filter(DailyRun.local_date >= cutoff, DailyRun.timezone == timezone)
            .order_by(DailyRun.local_date.desc())
            .limit(90)
            .all()
        )
        angles = []
        for run in runs:
            if run.result_json:
                angle = json.loads(run.result_json).get("editorial_angle")
                if angle:
                    angles.append(angle)
        return angles[:12]


def run_daily_pipeline(
    session_factory,
    *,
    timezone="America/Chicago",
    now=None,
    discover_fn: Callable | None = None,
    generate_fn: Callable | None = None,
    allow_early_retry=False,
):
    """Research, draft, renderable-post persistence, and idempotent daily history."""
    local_zone = ZoneInfo(timezone)
    current = now or datetime.now(local_zone)
    if current.tzinfo is None:
        current = current.replace(tzinfo=local_zone)
    local_day = current.astimezone(local_zone).date()
    run_id, claimed, previous = _reserve_run(
        session_factory,
        local_day,
        timezone,
        current.astimezone(UTC),
        allow_early_retry=allow_early_retry,
    )
    if not claimed:
        return previous

    try:
        report = (discover_fn or discover)(now=current.astimezone(UTC))
        warnings = report.get("errors", [])
        candidates = report.get("articles", [])
        if not candidates:
            raise RuntimeError(
                "No recent, source-dated AI developer stories were found. "
                "Check the configured feeds; no post was fabricated."
            )

        desired_topic = topic_for_date(local_day)
        with session_factory() as db:
            known_urls = {candidate.url for candidate in db.query(SourceCandidate.url).all()}
            known_titles = [post.title.casefold() for post in db.query(Post.title).all()]

        eligible = []
        for candidate in candidates:
            try:
                url = canonical_source_url(candidate.get("url", ""))
            except ValueError:
                continue
            published = candidate.get("published_at")
            if not isinstance(published, datetime):
                continue
            if published.tzinfo is None:
                published = published.replace(tzinfo=UTC)
            if url in known_urls:
                continue
            title = candidate.get("title", "").strip()
            if not title or any(
                SequenceMatcher(None, title.casefold(), existing).ratio() >= 0.90
                for existing in known_titles
            ):
                continue
            age_hours = max(0.0, (current.astimezone(UTC) - published).total_seconds() / 3600)
            if age_hours > 14 * 24:
                continue
            summary = candidate.get("summary", "").strip()
            category = classify_topic(title, summary)
            score = (12 if category == desired_topic else 0) + max(0, 72 - age_hours) / 72
            eligible.append((score, candidate, url, published, category))

        if not eligible:
            raise RuntimeError(
                "Recent sources were already used, too short, or too similar to existing posts. "
                "No duplicate draft was created."
            )
        eligible.sort(key=lambda item: item[0], reverse=True)
        selected = None
        for _, candidate, url, published, category in eligible[:8]:
            excerpt = _safe_article_evidence(candidate)
            if len(excerpt) < 240:
                warnings.append(
                    f"{candidate.get('source', 'Source')}: insufficient readable evidence"
                )
                continue
            selected = candidate, url, published, category, excerpt
            break
        if selected is None:
            raise RuntimeError(
                "The recent primary sources did not contain enough readable evidence. "
                "No post was fabricated."
            )
        article, source_url, published_at, source_topic, excerpt = selected
        previous_angles = _recent_angles(session_factory, local_day, timezone)
        generated = (generate_fn or generate)(
            article["title"],
            source_url,
            excerpt,
            topic=desired_topic,
            prior_angles=previous_angles,
        )

        hashtags = generated.get("hashtags", [])
        caption = generated["caption"].strip()
        missing_tags = [tag for tag in hashtags if tag.casefold() not in caption.casefold()]
        if missing_tags:
            caption = f"{caption}\n\n{' '.join(missing_tags)}"
        with session_factory.begin() as db:
            post_id = str(uuid.uuid4())
            post = Post(id=post_id, title=generated["title"], caption=caption)
            db.add(post)
            db.add(
                SourceCandidate(
                    id=str(uuid.uuid4()),
                    url=source_url,
                    title=article["title"][:500],
                    source=article.get("source", "Unknown")[:200],
                    post_id=post_id,
                )
            )
            db.add(
                ArticleEvidence(
                    id=str(uuid.uuid4()),
                    post_id=post_id,
                    source_url=source_url,
                    source_title=article["title"][:500],
                    source_name=article.get("source", "Unknown")[:200],
                    excerpt=excerpt,
                    published_at=published_at,
                    retrieved_at=current.astimezone(UTC),
                    topic=desired_topic,
                    editorial_angle=generated["editorial_angle"],
                    created_at=current.astimezone(UTC),
                )
            )
            for position, slide in enumerate(generated["slides"], 1):
                db.add(
                    Slide(
                        id=str(uuid.uuid4()),
                        post_id=post_id,
                        position=f"{position:03d}",
                        headline=slide["headline"],
                        body=slide["body"],
                    )
                )
            db.add(
                Audit(
                    id=str(uuid.uuid4()),
                    post_id=post_id,
                    event=(
                        f"Daily {desired_topic} draft generated from {source_url}; "
                        "source facts require human verification; approval required"
                    ),
                )
            )
        result = {
            "post_id": post_id,
            "topic": desired_topic,
            "source_topic": source_topic,
            "source_url": source_url,
            "source_title": article["title"],
            "source_published_at": published_at.isoformat(),
            "editorial_angle": generated["editorial_angle"],
            "slide_count": len(generated["slides"]),
            "verification_required": True,
            "warnings": warnings,
        }
        status = "completed_with_warnings" if warnings else "completed"
        return _finish_run(
            session_factory, run_id, status=status, result=result, now=current.astimezone(UTC)
        )
    except Exception as exc:
        return _finish_run(
            session_factory,
            run_id,
            status="failed",
            error=f"{type(exc).__name__}: {str(exc)[:600]}",
            now=current.astimezone(UTC),
        )


def create_additional_post(
    session_factory,
    *,
    timezone="America/Chicago",
    now=None,
    discover_fn: Callable | None = None,
    generate_fn: Callable | None = None,
):
    """Create a fresh, source-grounded draft without replacing today's daily run."""
    local_zone = ZoneInfo(timezone)
    current = now or datetime.now(local_zone)
    if current.tzinfo is None:
        current = current.replace(tzinfo=local_zone)
    current_utc = current.astimezone(UTC)
    desired_topic = topic_for_date(current.astimezone(local_zone).date())
    report = (discover_fn or discover)(now=current_utc)
    candidates = report.get("articles", [])
    with session_factory() as db:
        known_urls = {row[0] for row in db.query(SourceCandidate.url).all()}
        known_titles = [post.title.casefold() for post in db.query(Post).all()]
        prior_angles = [
            row[0]
            for row in db.query(ArticleEvidence.editorial_angle)
            .order_by(ArticleEvidence.created_at.desc())
            .limit(12)
            .all()
        ]

    eligible = []
    for candidate in candidates:
        try:
            url = canonical_source_url(candidate.get("url", ""))
        except ValueError:
            continue
        published = candidate.get("published_at")
        if not isinstance(published, datetime):
            continue
        if published.tzinfo is None:
            published = published.replace(tzinfo=UTC)
        age = current_utc - published
        if url in known_urls or age < timedelta(days=-1) or age > timedelta(days=14):
            continue
        title = candidate.get("title", "").strip()
        if not title or any(
            SequenceMatcher(None, title.casefold(), existing).ratio() >= 0.90
            for existing in known_titles
        ):
            continue
        eligible.append((published, candidate, url))

    selected = None
    warnings = list(report.get("errors", []))
    for published, candidate, url in sorted(eligible, key=lambda item: item[0], reverse=True)[:12]:
        excerpt = _safe_article_evidence(candidate)
        if len(excerpt) < 240:
            warnings.append(f"{candidate.get('source', 'Source')}: insufficient readable evidence")
            continue
        selected = published, candidate, url, excerpt
        break
    if not selected:
        raise RuntimeError(
            "No new recent source with enough evidence was found. Existing stories were skipped."
        )

    published, article, source_url, excerpt = selected
    generated = (generate_fn or generate)(
        article["title"],
        source_url,
        excerpt,
        topic=desired_topic,
        prior_angles=prior_angles,
    )
    post_id = str(uuid.uuid4())
    with session_factory.begin() as db:
        db.add(Post(id=post_id, title=generated["title"], caption=generated["caption"]))
        db.add(
            SourceCandidate(
                id=str(uuid.uuid4()),
                url=source_url,
                title=article["title"][:500],
                source=article.get("source", "Unknown")[:200],
                post_id=post_id,
            )
        )
        db.add(
            ArticleEvidence(
                id=str(uuid.uuid4()),
                post_id=post_id,
                source_url=source_url,
                source_title=article["title"][:500],
                source_name=article.get("source", "Unknown")[:200],
                excerpt=excerpt,
                published_at=published,
                retrieved_at=current_utc,
                topic=desired_topic,
                editorial_angle=generated["editorial_angle"],
                created_at=current_utc,
            )
        )
        for position, slide in enumerate(generated["slides"], 1):
            db.add(
                Slide(
                    id=str(uuid.uuid4()),
                    post_id=post_id,
                    position=f"{position:03d}",
                    headline=slide["headline"],
                    body=slide["body"],
                    visual_direction=slide.get("visual_direction") or None,
                )
            )
        db.add(
            Audit(
                id=str(uuid.uuid4()),
                post_id=post_id,
                event=f"Additional research draft from {source_url}; human verification required",
            )
        )
    return {
        "id": post_id,
        "status": "draft",
        "topic": desired_topic,
        "source_url": source_url,
        "source_title": article["title"],
        "slide_count": len(generated["slides"]),
        "verification_required": True,
        "warnings": warnings,
    }
