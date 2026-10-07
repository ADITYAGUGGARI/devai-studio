"""Persisted content, source identities, and review/publishing audit history.

Column names and string versions/positions preserve the existing database schema.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
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
