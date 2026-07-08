"""Database models for Dashboard Audit Logging."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from bot.database.models.base import Base


class DashboardAuditLog(Base):
    """Tracks every administrative action performed on the Web Dashboard."""

    __tablename__ = "dashboard_audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    guild_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)

    action: Mapped[str] = mapped_column(String(100), index=True, nullable=False)

    # E.g., Module name, or specific setting key
    target: Mapped[str | None] = mapped_column(String(100), nullable=True)

    old_value: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    new_value: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)

    correlation_id: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, server_default=func.now(), nullable=False
    )
