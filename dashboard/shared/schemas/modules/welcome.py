"""Pydantic schemas for Welcome APIs."""

from pydantic import BaseModel, Field


class WelcomeSettingsSchema(BaseModel):
    """Schema for Welcome/Goodbye config."""

    guild_id: str
    welcome_enabled: bool
    welcome_channel_id: str | None
    welcome_message: str | None
    welcome_image_url: str | None
    goodbye_enabled: bool
    goodbye_channel_id: str | None
    goodbye_message: str | None


class AutoRoleSchema(BaseModel):
    """Schema for Autorole config."""

    id: int | None = None
    role_id: str
    target: str = Field(..., pattern="^(human|bot|all)$")
    delay_seconds: int = Field(0, ge=0)
    requires_verification: bool = False
