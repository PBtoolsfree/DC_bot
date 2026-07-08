"""Database models for the Ticket System."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from bot.database.models.base import Base


class TicketCategory(Base):
    """Configuration for a specific type of ticket (e.g., Bug Report, Support)."""

    __tablename__ = "ticket_categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=True)

    # E.g. "ticket-{user}" or "support-{id}"
    naming_template: Mapped[str] = mapped_column(String(50), default="ticket-{id}", nullable=False)

    # Store JSON array of role IDs
    support_team_roles: Mapped[list[int]] = mapped_column(JSON, default=list, nullable=False)

    category_channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # SLA Settings
    sla_response_hours: Mapped[int] = mapped_column(Integer, default=24, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class TicketPanel(Base):
    """A deployed UI message containing buttons/dropdowns to open tickets."""

    __tablename__ = "ticket_panels"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)

    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    title: Mapped[str] = mapped_column(String(100), default="Open a Ticket", nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=True)

    # List of category IDs to display on this panel
    categories: Mapped[list[int]] = mapped_column(JSON, default=list, nullable=False)


class Ticket(Base):
    """Represents an active or closed ticket."""

    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)

    channel_id: Mapped[int | None] = mapped_column(BigInteger, index=True, nullable=True)
    owner_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)

    category_id: Mapped[int] = mapped_column(
        ForeignKey("ticket_categories.id", ondelete="CASCADE"), nullable=False
    )

    # State Machine: "open", "claimed", "in_progress", "waiting_user", "waiting_staff", "resolved", "closed", "archived", "deleted"
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)

    # Low, Medium, High, Urgent
    priority: Mapped[str] = mapped_column(String(20), default="Medium", nullable=False)

    claimed_by_id: Mapped[int | None] = mapped_column(BigInteger, index=True, nullable=True)

    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TicketMessage(Base):
    """Temporary rolling log of messages inside a ticket for transcripts."""

    __tablename__ = "ticket_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), index=True, nullable=False
    )

    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    author_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    author_name: Mapped[str] = mapped_column(String(100), nullable=False)

    content: Mapped[str] = mapped_column(String(4000), nullable=True)
    # E.g., attachment URLs
    attachments: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class TicketTranscript(Base):
    """Metadata for exported and archived transcripts."""

    __tablename__ = "ticket_transcripts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # E.g., HTML, PDF, Markdown
    format: Mapped[str] = mapped_column(String(10), nullable=False)

    # URL to S3, or local filepath
    url: Mapped[str] = mapped_column(String(500), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class TicketParticipant(Base):
    """Users explicitly added to a ticket channel via commands."""

    __tablename__ = "ticket_participants"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
