"""Security database models.

Models for Incident tracking, Rollback queues, and Server Snapshots.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from bot.database.models.base import Base


class IncidentReport(Base):
    """Tracks security incidents for the Incident Timeline and Audit Service."""

    __tablename__ = "security_incidents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)

    executor_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    target_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    action: Mapped[str] = mapped_column(String(100), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    case_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rollback_status: Mapped[str] = mapped_column(
        String(50), default="NONE"
    )  # NONE, PENDING, SUCCESS, FAILED

    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SecuritySnapshot(Base):
    """Stores full server snapshots for the Snapshot Manager."""

    __tablename__ = "security_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_by_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # JSON payload containing roles, channels, category structure, permissions
    snapshot_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    is_auto: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
