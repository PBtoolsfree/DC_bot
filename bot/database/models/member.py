"""Member-related database models.

Models:
- MemberData: Per-guild member tracking (XP, notes)
- Warning: Individual warnings issued to members
- ModAction: Full moderation action audit log
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.database.models.base import Base, TimestampMixin


class ModActionType(str, Enum):
    """Enumeration of moderation action types."""

    WARN = "warn"
    MUTE = "mute"
    UNMUTE = "unmute"
    KICK = "kick"
    BAN = "ban"
    UNBAN = "unban"
    TIMEOUT = "timeout"
    UNTIMEOUT = "untimeout"
    SOFTBAN = "softban"
    PURGE = "purge"
    LOCKDOWN = "lockdown"
    UNLOCK = "unlock"
    SLOWMODE = "slowmode"
    NOTE = "note"
    # Auto-moderation actions
    AUTO_TIMEOUT = "auto_timeout"
    AUTO_WARN = "auto_warn"
    AUTO_KICK = "auto_kick"
    AUTO_BAN = "auto_ban"
    AUTO_DELETE = "auto_delete"
    # Security actions
    ANTI_NUKE = "anti_nuke"
    ANTI_RAID = "anti_raid"


class MemberData(Base, TimestampMixin):
    """Per-guild member data tracking.

    Stores member-specific data per guild: XP, level, notes, etc.
    The primary key is a composite of (guild_id, user_id).
    """

    __tablename__ = "member_data"
    __table_args__ = (
        Index("ix_member_data_guild_user", "guild_id", "user_id", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("guild_configs.id", ondelete="CASCADE"),
        nullable=False,
        comment="Guild this member data belongs to",
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="Discord user ID",
    )

    # Cached display info
    username: Mapped[str] = mapped_column(
        String(100),
        default="Unknown",
        comment="Cached username",
    )
    display_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Cached display/nickname",
    )

    # Moderation state
    is_muted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Whether member is currently muted",
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Whether member has completed verification",
    )
    total_warnings: Mapped[int] = mapped_column(
        default=0,
        comment="Running total of active warnings",
    )
    total_messages: Mapped[int] = mapped_column(
        default=0,
        comment="Total messages sent in this guild (for analytics)",
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Moderator notes about this member",
    )

    # Relationships
    warnings: Mapped[list[Warning]] = relationship(
        "Warning",
        back_populates="member",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    mod_actions: Mapped[list[ModAction]] = relationship(
        "ModAction",
        back_populates="member",
        cascade="all, delete-orphan",
        lazy="selectin",
        foreign_keys="[ModAction.member_data_id]",
    )

    def __repr__(self) -> str:
        return (
            f"<MemberData(guild_id={self.guild_id}, "
            f"user_id={self.user_id}, warnings={self.total_warnings})>"
        )


class Warning(Base, TimestampMixin):
    """Individual warning record.

    Each warning is a separate row tied to a MemberData entry.
    Warnings can be active or pardoned (cleared by a moderator).
    """

    __tablename__ = "warnings"
    __table_args__ = (
        Index("ix_warnings_guild_user", "guild_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="Guild where the warning was issued",
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="Warned user's Discord ID",
    )
    moderator_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="Moderator who issued the warning",
    )
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="No reason provided",
        comment="Warning reason",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Whether this warning is still active",
    )
    pardoned_by: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Moderator who pardoned/cleared this warning",
    )
    pardoned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the warning was pardoned",
    )

    # FK to MemberData
    member_data_id: Mapped[int | None] = mapped_column(
        ForeignKey("member_data.id", ondelete="CASCADE"),
        nullable=True,
        comment="FK to member_data for cascading deletes",
    )

    # Relationship
    member: Mapped[MemberData | None] = relationship(
        "MemberData",
        back_populates="warnings",
    )

    def __repr__(self) -> str:
        return (
            f"<Warning(id={self.id}, guild={self.guild_id}, "
            f"user={self.user_id}, active={self.is_active})>"
        )


class ModAction(Base, TimestampMixin):
    """Full moderation action audit log.

    Records every moderation action taken (manual or automatic),
    including the action type, target, moderator, reason, and duration.
    This is the central audit trail for all moderation activity.
    """

    __tablename__ = "mod_actions"
    __table_args__ = (
        Index("ix_mod_actions_guild_user", "guild_id", "user_id"),
        Index("ix_mod_actions_guild_type", "guild_id", "action_type"),
        Index("ix_mod_actions_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="Guild where the action occurred",
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="Target user's Discord ID",
    )
    moderator_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="Moderator or bot user ID who performed the action",
    )
    action_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="Action type from ModActionType enum",
    )
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="No reason provided",
        comment="Reason for the action",
    )
    duration_seconds: Mapped[int | None] = mapped_column(
        nullable=True,
        comment="Duration in seconds (for timeouts, mutes)",
    )
    details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Additional details (e.g., number of messages purged)",
    )
    is_automated: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Whether this action was triggered by auto-moderation",
    )

    # FK to MemberData (optional, for cascading)
    member_data_id: Mapped[int | None] = mapped_column(
        ForeignKey("member_data.id", ondelete="SET NULL"),
        nullable=True,
        comment="FK to member_data for relationship",
    )

    # Relationship
    member: Mapped[MemberData | None] = relationship(
        "MemberData",
        back_populates="mod_actions",
        foreign_keys=[member_data_id],
    )

    def __repr__(self) -> str:
        return (
            f"<ModAction(id={self.id}, type={self.action_type}, "
            f"guild={self.guild_id}, user={self.user_id})>"
        )
