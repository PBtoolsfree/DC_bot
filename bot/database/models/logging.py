"""Logging and Audit Database Models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Boolean, DateTime, String, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from bot.database.models.base import Base


class ActionLog(Base):
    """Centralized Audit Log table."""

    __tablename__ = "action_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    
    correlation_id: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    
    action_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    severity: Mapped[int] = mapped_column(Integer, default=1) # 1: Info, 2: Warning, 3: High, 4: Critical
    
    executor_id: Mapped[int | None] = mapped_column(BigInteger, index=True, nullable=True)
    target_id: Mapped[int | None] = mapped_column(BigInteger, index=True, nullable=True)
    channel_id: Mapped[int | None] = mapped_column(BigInteger, index=True, nullable=True)
    
    # Stores old state (e.g., deleted message content, old nickname)
    before_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    # Stores new state (e.g., edited message content, new nickname)
    after_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    
    # Attachments, jump URLs, case IDs
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    
    is_immutable: Mapped[bool] = mapped_column(Boolean, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, server_default=func.now(), nullable=False
    )
