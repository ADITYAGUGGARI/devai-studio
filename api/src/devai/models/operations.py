"""Account security, editorial approvals, immutable revisions and operations."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from devai.core.database import Base
from devai.models.content import utc_now


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(20), default="editor")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    identity: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class TopicApproval(Base):
    __tablename__ = "topic_approvals"
    workspace_id: Mapped[str] = mapped_column(
        String, default="00000000-0000-4000-8000-000000000001", index=True, nullable=False
    )
    topic_id: Mapped[str] = mapped_column(ForeignKey("topics.id"), primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(64))
    approved_by: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class PostRevision(Base):
    __tablename__ = "post_revisions"
    workspace_id: Mapped[str] = mapped_column(
        String, default="00000000-0000-4000-8000-000000000001", index=True, nullable=False
    )
    __table_args__ = (UniqueConstraint("post_id", "version", name="uq_post_revision"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    post_id: Mapped[str] = mapped_column(ForeignKey("posts.id"), index=True)
    version: Mapped[str] = mapped_column(String)
    snapshot_json: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class PublishSchedule(Base):
    __tablename__ = "publish_schedules"
    workspace_id: Mapped[str] = mapped_column(
        String, default="00000000-0000-4000-8000-000000000001", index=True, nullable=False
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    post_id: Mapped[str] = mapped_column(ForeignKey("posts.id"), index=True)
    version: Mapped[str] = mapped_column(String)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(30), default="scheduled")
    active_key: Mapped[str | None] = mapped_column(String, unique=True)
    job_id: Mapped[str | None] = mapped_column(String)
    error: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class UsageEvent(Base):
    __tablename__ = "usage_events"
    workspace_id: Mapped[str] = mapped_column(
        String, default="00000000-0000-4000-8000-000000000001", index=True, nullable=False
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    job_id: Mapped[str | None] = mapped_column(String, index=True)
    provider: Mapped[str] = mapped_column(String, default="openai")
    model: Mapped[str] = mapped_column(String)
    operation: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    images: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost_usd: Mapped[float | None] = mapped_column(Float)
    pricing_json: Mapped[str | None] = mapped_column(Text)
    duration_ms: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class WorkspaceSetting(Base):
    __tablename__ = "workspace_settings"
    key: Mapped[str] = mapped_column(String, primary_key=True)
    value_json: Mapped[str] = mapped_column(Text)
