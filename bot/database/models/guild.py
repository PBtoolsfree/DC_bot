"""Guild-related database models.

Models:
- GuildConfig: Per-server settings (log channel, welcome channel, etc.)
- GuildModuleSettings: Per-module enable/disable + JSON config per guild
- GuildPremium: Premium tier tracking per guild
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.database.models.base import Base, SnowflakeMixin, TimestampMixin


class GuildConfig(Base, SnowflakeMixin, TimestampMixin):
    """Core per-guild configuration.

    Every guild the bot is in gets a row here. Stores top-level settings
    like log channels, locale, and the guild's display name cache.
    """

    __tablename__ = "guild_configs"

    # Cached guild info (updated on guild_update events)
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Unknown",
        comment="Cached guild name",
    )
    icon_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="Cached guild icon hash",
    )
    owner_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
        comment="Guild owner's Discord ID",
    )
    member_count: Mapped[int] = mapped_column(
        default=0,
        comment="Cached member count",
    )

    # Channel IDs for various log destinations
    mod_log_channel_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Channel for moderation action logs",
    )
    server_log_channel_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Channel for server event logs (joins, leaves, edits)",
    )
    message_log_channel_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Channel for message edit/delete logs",
    )
    welcome_channel_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Channel for welcome messages",
    )
    verification_channel_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Channel for verification panel",
    )
    suggestion_channel_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Channel for suggestion submissions",
    )
    ticket_category_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Category under which ticket channels are created",
    )
    ticket_log_channel_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Channel for ticket transcripts",
    )

    # Role IDs
    mute_role_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Muted role ID (for legacy mute, timeout is preferred)",
    )
    verified_role_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Role assigned upon verification",
    )
    auto_role_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Role auto-assigned on join",
    )

    # Welcome messages
    welcome_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Welcome message template with {user}, {server}, {count} placeholders",
    )
    welcome_dm_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="DM welcome message template",
    )
    leave_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Leave message template",
    )
    welcome_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Whether welcome messages are enabled",
    )

    # Locale and timezone
    locale: Mapped[str] = mapped_column(
        String(10),
        default="en-US",
        comment="Guild locale for localized messages",
    )
    timezone: Mapped[str] = mapped_column(
        String(50),
        default="UTC",
        comment="Guild timezone for scheduled events",
    )

    # Relationships
    module_settings: Mapped[list[GuildModuleSettings]] = relationship(
        "GuildModuleSettings",
        back_populates="guild",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    premium: Mapped[GuildPremium | None] = relationship(
        "GuildPremium",
        back_populates="guild",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )


class GuildModuleSettings(Base, TimestampMixin):
    """Per-module configuration for a guild.

    Each cog module (moderation, automod, security, etc.) gets its own row
    with an enable/disable flag and a JSONB config blob for module-specific
    settings.

    This allows each module to store arbitrary settings without schema changes.
    """

    __tablename__ = "guild_module_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("guild_configs.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK to guild_configs",
    )
    module_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Module identifier (e.g., 'automod', 'security', 'welcome')",
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Whether this module is enabled for the guild",
    )
    config: Mapped[dict] = mapped_column(  # type: ignore[type-arg]
        JSON,
        default=dict,
        server_default="{}",
        comment="Module-specific configuration as JSON",
    )

    # Relationship
    guild: Mapped[GuildConfig] = relationship(
        "GuildConfig",
        back_populates="module_settings",
    )

    def __repr__(self) -> str:
        return (
            f"<GuildModuleSettings(guild_id={self.guild_id}, "
            f"module={self.module_name}, enabled={self.enabled})>"
        )


class GuildPremium(Base, TimestampMixin):
    """Premium subscription tracking per guild.

    Tracks which guilds have premium features activated,
    their tier, and subscription dates.
    """

    __tablename__ = "guild_premiums"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("guild_configs.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        comment="FK to guild_configs",
    )
    tier: Mapped[str] = mapped_column(
        String(20),
        default="free",
        comment="Premium tier: free, basic, pro, enterprise",
    )
    activated_by: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="Discord user ID who activated premium",
    )
    activated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="When premium was activated",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When premium expires (null = lifetime)",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Whether premium is currently active",
    )

    # Relationship
    guild: Mapped[GuildConfig] = relationship(
        "GuildConfig",
        back_populates="premium",
    )

    def __repr__(self) -> str:
        return (
            f"<GuildPremium(guild_id={self.guild_id}, "
            f"tier={self.tier}, active={self.is_active})>"
        )
