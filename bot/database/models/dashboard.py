"""Database models for Dashboard Hybrid RBAC."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from bot.database.models.base import Base


class DashboardMember(Base):
    """Represents a Discord user's access rights to the Web Dashboard for a specific guild."""

    __tablename__ = "dashboard_members"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    discord_user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    
    # Pre-defined roles: "owner", "admin", "moderator", "viewer", "custom"
    role: Mapped[str] = mapped_column(String(50), default="viewer", nullable=False)
    
    # Granular custom permissions JSON if role == "custom"
    # Example: {"manage_moderation": true, "manage_security": false}
    permissions: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Audit tracking
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
