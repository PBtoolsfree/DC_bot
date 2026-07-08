"""Database models for Welcome/Goodbye/Autorole (Module 10)."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from bot.database.models.base import Base


class WelcomeSettings(Base):
    """Configuration for Welcome & Goodbye."""

    __tablename__ = "welcome_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, index=True, unique=True, nullable=False)

    welcome_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    welcome_channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    welcome_message: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    welcome_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    goodbye_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    goodbye_channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    goodbye_message: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AutoRoleSettings(Base):
    """Configuration for Autoroles."""

    __tablename__ = "autorole_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)

    role_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    target: Mapped[str] = mapped_column(String(20), default="human")  # 'human', 'bot', 'all'
    delay_seconds: Mapped[int] = mapped_column(Integer, default=0)
    requires_verification: Mapped[bool] = mapped_column(Boolean, default=False)
