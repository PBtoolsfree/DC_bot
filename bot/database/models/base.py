"""SQLAlchemy declarative base and common mixins.

All ORM models inherit from Base. Common columns (created_at, updated_at)
are provided via the TimestampMixin.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models.

    Provides:
    - Automatic __tablename__ generation (lowercase class name + 's')
    - Common repr format
    """

    def __repr__(self) -> str:
        """Generate a debug-friendly representation of the model."""
        columns = ", ".join(
            f"{col.name}={getattr(self, col.name)!r}"
            for col in self.__table__.columns
            if col.primary_key
        )
        return f"<{self.__class__.__name__}({columns})>"


class TimestampMixin:
    """Mixin that adds created_at and updated_at columns.

    These are automatically managed by the database:
    - created_at: Set to UTC now on INSERT
    - updated_at: Set to UTC now on INSERT and UPDATE
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class SnowflakeMixin:
    """Mixin for models keyed by a Discord snowflake ID.

    Discord IDs are 64-bit integers (snowflakes), so we use BigInteger.
    """

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=False,
        comment="Discord snowflake ID",
    )
