"""Expiring email challenges; codes are never stored in readable form."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from devai.core.database import Base
from devai.models.content import utc_now


class EmailChallenge(Base):
    __tablename__ = "email_challenges"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String(254), index=True)
    address_hash: Mapped[str] = mapped_column(String(64), index=True)
    code_hash: Mapped[str] = mapped_column(String(64))
    action_hash: Mapped[str | None] = mapped_column(String(64), unique=True)
    request_hash: Mapped[str | None] = mapped_column(String(64))
    delivery_status: Mapped[str] = mapped_column(String(20), default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    consumed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class UserProfile(Base):
    __tablename__ = "user_profiles"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(80), default="")
    locale: Mapped[str] = mapped_column(String(10), default="en")
    time_zone: Mapped[str] = mapped_column(String(100), default="America/Chicago")
    revision: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
