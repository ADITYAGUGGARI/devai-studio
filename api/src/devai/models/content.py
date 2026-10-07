"""Persisted content, source identities, and review/publishing audit history.

Column names and string versions/positions preserve the existing database schema.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from devai.core.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    caption: Mapped[str | None] = mapped_column(Text, default="")
    status: Mapped[str | None] = mapped_column(String, default="draft")
    version: Mapped[str | None] = mapped_column(String, default="1")
    created: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)


class Slide(Base):
    __tablename__ = "slides"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    post_id: Mapped[str | None] = mapped_column(String, ForeignKey("posts.id"))
    position: Mapped[str | None] = mapped_column(String)
    headline: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text)
    visual_direction: Mapped[str | None] = mapped_column(Text)
    artwork_path: Mapped[str | None] = mapped_column(Text)


class PublishAttempt(Base):
    __tablename__ = "publish_attempts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    post_id: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    external_id: Mapped[str | None] = mapped_column(String)
    error: Mapped[str | None] = mapped_column(Text)
    created: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)


class Audit(Base):
    __tablename__ = "audit"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    post_id: Mapped[str | None] = mapped_column(String)
    event: Mapped[str | None] = mapped_column(String)
    created: Mapped[datetime | None] = mapped_column(DateTime, default=utc_now)


class SourceCandidate(Base):
    __tablename__ = "source_candidates"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str] = mapped_column(String(200), nullable=False)
    post_id: Mapped[str] = mapped_column(String, nullable=False)
    created: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=utc_now)


class ArticleEvidence(Base):
    """A bounded plain-text source snapshot used to ground one editorial draft."""

    __tablename__ = "article_evidence"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    post_id: Mapped[str] = mapped_column(String, ForeignKey("posts.id"), nullable=False)
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True)
    source_title: Mapped[str] = mapped_column(String(500), nullable=False)
    source_name: Mapped[str] = mapped_column(String(200), nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    topic: Mapped[str] = mapped_column(String(40), nullable=False)
    editorial_angle: Mapped[str] = mapped_column(String(300), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class DailyRun(Base):
    """Durable per-local-day claim and outcome for the one-post editorial cadence."""

    __tablename__ = "daily_runs"
    __table_args__ = (
        UniqueConstraint("local_date", "timezone", name="uq_daily_runs_date_timezone"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    local_date: Mapped[str] = mapped_column(String(10), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    result_json: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
