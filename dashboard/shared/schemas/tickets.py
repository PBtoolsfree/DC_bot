"""Pydantic schemas for the Ticket Dashboard API."""

from pydantic import BaseModel, Field
from datetime import datetime


class TicketCategorySchema(BaseModel):
    """Schema for a Ticket Category."""
    id: int | None = None
    name: str = Field(..., max_length=50)
    description: str | None = Field(None, max_length=200)
    naming_template: str = Field("ticket-{id}", max_length=50)
    support_team_roles: list[int] = Field(default_factory=list)
    category_channel_id: str | None = None
    sla_response_hours: int = Field(24, ge=1, le=720)


class TicketPanelSchema(BaseModel):
    """Schema for a Ticket Panel."""
    id: int | None = None
    channel_id: str
    message_id: str | None = None
    title: str = Field("Open a Ticket", max_length=100)
    description: str | None = Field(None, max_length=2000)
    categories: list[int] = Field(..., min_items=1)


class TicketResponse(BaseModel):
    """Schema for a Ticket shown on the dashboard."""
    id: int
    guild_id: str
    channel_id: str | None
    owner_id: str
    category_id: int
    status: str
    priority: str
    claimed_by_id: str | None
    is_anonymous: bool
    created_at: datetime
    closed_at: datetime | None
