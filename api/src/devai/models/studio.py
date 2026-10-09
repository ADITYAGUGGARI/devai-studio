"""Workspace-scoped revisioned documents, research snapshots and durable action receipts."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from devai.core.database import Base
from devai.models.content import utc_now

LEGACY_WORKSPACE = "00000000-0000-4000-8000-000000000001"


class Workspace(Base):
    __tablename__ = "workspaces"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    revision: Mapped[int] = mapped_column(Integer, default=1)
    settings_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Membership(Base):
    __tablename__ = "workspace_members"
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String(20))
    publish_permission: Mapped[int] = mapped_column(Integer, default=0)


class StudioDocument(Base):
    """Typed service schemas validate JSON; CAS revision protects each document head."""

    __tablename__ = "studio_documents"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    kind: Mapped[str] = mapped_column(String(40), index=True)
    parent_id: Mapped[str | None] = mapped_column(String, index=True)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    state: Mapped[str] = mapped_column(String(40), default="draft", index=True)
    data_json: Mapped[str] = mapped_column(Text, default="{}")
    created_by: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class StudioVersion(Base):
    __tablename__ = "studio_versions"
    __table_args__ = (UniqueConstraint("document_id", "revision", name="uq_studio_version"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("studio_documents.id"), index=True)
    revision: Mapped[int] = mapped_column(Integer)
    data_json: Mapped[str] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String(40))
    actor_id: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ResearchRun(Base):
    __tablename__ = "research_runs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), unique=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    policy: Mapped[str] = mapped_column(String(40), default="developer-24h-v1")
    coverage_json: Mapped[str] = mapped_column(Text, default="{}")
    created_by: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Finding(Base):
    __tablename__ = "research_findings"
    __table_args__ = (UniqueConstraint("run_id", "canonical_url", name="uq_run_finding_url"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("research_runs.id"), index=True)
    canonical_url: Mapped[str] = mapped_column(String(2048))
    topic_id: Mapped[str | None] = mapped_column(ForeignKey("topics.id"))
    title: Mapped[str] = mapped_column(String(500))
    source: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(40))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    disposition: Mapped[str] = mapped_column(String(40), index=True)
    duplicate_group_id: Mapped[str | None] = mapped_column(String)
    score: Mapped[int] = mapped_column(Integer)
    dimensions_json: Mapped[str] = mapped_column(Text)
    evidence_json: Mapped[str] = mapped_column(Text)


class ActionReceipt(Base):
    __tablename__ = "action_receipts"
    __table_args__ = (
        UniqueConstraint("workspace_id", "actor_id", "action_key", name="uq_action_key"),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"))
    actor_id: Mapped[str] = mapped_column(String)
    action_key: Mapped[str] = mapped_column(String(200))
    request_hash: Mapped[str] = mapped_column(String(64))
    response_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
