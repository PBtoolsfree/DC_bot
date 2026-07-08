"""Database models for the Verification System."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from bot.database.models.base import Base


class VerificationSettings(Base):
    """Guild-specific configuration for the verification system."""

    __tablename__ = "verification_settings"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Mode: "adaptive", "button", "math", "word", "image", "manual"
    # Adaptive uses Risk Engine
    verification_type: Mapped[str] = mapped_column(String(20), default="button", nullable=False)

    # Roles
    quarantine_role_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    verified_role_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    temporary_role_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Channels
    verification_channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    log_channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Thresholds
    timeout_minutes: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    risk_threshold_high: Mapped[int] = mapped_column(
        Integer, default=70, nullable=False
    )  # e.g. score > 70 requires Image/Manual

    # Embed & Localization
    language: Mapped[str] = mapped_column(String(10), default="en-US", nullable=False)
    custom_embed_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Flags
    delete_failed_messages: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    kick_on_timeout: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class VerificationSession(Base):
    """Tracks an active verification attempt to prevent reuse and replay attacks."""

    __tablename__ = "verification_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(64), index=True, unique=True, nullable=False
    )  # UUID or HMAC

    guild_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)

    # "pending", "quarantined", "challenge_issued", "verified", "failed", "manual_review"
    state: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)

    verification_type: Mapped[str] = mapped_column(String(20), nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Answer expected from the user (hashed or raw if temp)
    expected_answer: Mapped[str | None] = mapped_column(String(255), nullable=True)

    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class VerificationHistory(Base):
    """Permanent audit log for verification attempts."""

    __tablename__ = "verification_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)

    # "success", "failed", "timeout", "rejected"
    result: Mapped[str] = mapped_column(String(20), index=True, nullable=False)

    verification_type: Mapped[str] = mapped_column(String(20), nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    time_taken_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # If approved/rejected manually
    moderator_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, server_default=func.now(), nullable=False
    )
