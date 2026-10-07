"""Daily source discovery. Never auto-approves or publishes."""

import uuid

from devai.services.research import create_editorial_draft, discover
from devai.services.source_urls import canonical_source_url


def ingest(
    session_factory, source_model, post_model, slide_model, audit_model, *, articles=None, limit=5
):
    """Idempotent per canonical URL; callers must serialize concurrent invocations."""
    if articles is None:
        report = discover()
        articles = report["articles"]
        errors = report["errors"]
    else:
        errors = []
    created = []
    skipped = []
    for article in articles[:limit]:
        try:
            url = canonical_source_url(article.get("url", ""))
        except ValueError:
            continue
        with session_factory.begin() as db:
            if db.query(source_model).filter_by(url=url).first():
                skipped.append(url)
                continue
            payload = create_editorial_draft({**article, "url": url})
            pid = str(uuid.uuid4())
            db.add(
                post_model(
                    id=pid, title=payload["title"], caption=payload["caption"], status="draft"
                )
            )
            for i, slide in enumerate(payload["slides"], 1):
                db.add(
                    slide_model(
                        id=str(uuid.uuid4()),
                        post_id=pid,
                        position=f"{i:03d}",
                        headline=slide["headline"],
                        body=slide["body"],
                    )
                )
            db.add(
                source_model(
                    id=str(uuid.uuid4()),
                    url=url,
                    title=article["title"][:500],
                    source=article.get("source", "Unknown")[:200],
                    post_id=pid,
                )
            )
            db.add(
                audit_model(
                    id=str(uuid.uuid4()),
                    post_id=pid,
                    event="daily discovery: unverified editorial scaffold; approval required",
                )
            )
            created.append(pid)
    return {
        "created_post_ids": created,
        "skipped_urls": skipped,
        "feed_errors": errors,
        "verification_required": True,
    }
