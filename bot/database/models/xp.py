"""Database models for Leveling & XP (Module 12)."""

from sqlalchemy import JSON, BigInteger, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column

from bot.database.models.base import Base


class XPSettings(Base):
    """Guild XP configuration."""

    __tablename__ = "xp_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, index=True, unique=True, nullable=False)

    enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    message_xp_min: Mapped[int] = mapped_column(Integer, default=15)
    message_xp_max: Mapped[int] = mapped_column(Integer, default=25)
    message_cooldown_sec: Mapped[int] = mapped_column(Integer, default=60)

    voice_xp_per_minute: Mapped[int] = mapped_column(Integer, default=10)

    # Store JSON list of channel IDs where XP is disabled
    ignored_channels: Mapped[list[int]] = mapped_column(JSON, default=list)


class UserXP(Base):
    """Tracks XP for a specific user in a specific guild."""

    __tablename__ = "user_xp"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)

    xp: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=0)
    messages_sent: Mapped[int] = mapped_column(Integer, default=0)
    voice_minutes: Mapped[int] = mapped_column(Integer, default=0)


class XPReward(Base):
    """Roles granted automatically at specific levels."""

    __tablename__ = "xp_rewards"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)

    level: Mapped[int] = mapped_column(Integer, nullable=False)
    role_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    remove_on_demotion: Mapped[bool] = mapped_column(Boolean, default=True)
