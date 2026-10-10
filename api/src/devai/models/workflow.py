"""Persistent editorial queue, leased jobs, and immutable publishing media."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from devai.core.database import Base
from devai.models.content import utc_now


class Topic(Base):
    __tablename__ = "topics"
    __table_args__ = (UniqueConstraint("workspace_id", "url", name="uq_topics_workspace_url"),)
    workspace_id: Mapped[str] = mapped_column(
        String, default="00000000-0000-4000-8000-000000000001", index=True, nullable=False
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[str] = mapped_column(String(500))
    source: Mapped[str] = mapped_column(String(200))
    excerpt: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(40))
    priority: Mapped[int] = mapped_column(Integer, default=50)
    selected: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(30), default="queued")
    verification: Mapped[str] = mapped_column(String(40), default="unverified")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    post_id: Mapped[str | None] = mapped_column(String)
    job_id: Mapped[str | None] = mapped_column(String)
    error: Mapped[str | None] = mapped_column(Text)


class Job(Base):
    __tablename__ = "jobs"
    workspace_id: Mapped[str] = mapped_column(
        String, default="00000000-0000-4000-8000-000000000001", index=True, nullable=False
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    kind: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    result_json: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)
    step: Mapped[str] = mapped_column(String(300), default="Waiting for worker")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    total: Mapped[int] = mapped_column(Integer, default=1)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    active_key: Mapped[str | None] = mapped_column(String, unique=True)
    schedule_key: Mapped[str | None] = mapped_column(String, unique=True)
    lease_token: Mapped[str | None] = mapped_column(String)
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MediaAsset(Base):
    __tablename__ = "media_assets"
    workspace_id: Mapped[str] = mapped_column(
        String, default="00000000-0000-4000-8000-000000000001", index=True, nullable=False
    )
    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    post_id: Mapped[str] = mapped_column(String, index=True)
    version: Mapped[str] = mapped_column(String)
    slide_id: Mapped[str] = mapped_column(String)
    path: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64))
