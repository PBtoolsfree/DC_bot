"""Pydantic schemas for Backup & Restore APIs."""

from datetime import datetime
from pydantic import BaseModel, Field


class BackupResponse(BaseModel):
    """Schema for returning a backup."""
    id: int
    guild_id: str
    creator_id: str
    name: str
    description: str | None
    created_at: datetime


class BackupCreate(BaseModel):
    """Schema for creating a backup."""
    name: str = Field(..., max_length=100)
    description: str | None = Field(None, max_length=500)


class RestorePreviewRequest(BaseModel):
    """Request to preview what will change."""
    backup_id: int
