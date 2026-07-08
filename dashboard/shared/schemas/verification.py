"""Pydantic schemas for the Verification Dashboard API."""

from pydantic import BaseModel, Field


class VerificationSettingsUpdate(BaseModel):
    """Schema for updating verification settings from the dashboard."""
    enabled: bool
    verification_type: str = Field(..., description="E.g., button, math, word, image, manual, adaptive")
    
    quarantine_role_id: str | None = None
    verified_role_id: str | None = None
    temporary_role_id: str | None = None
    
    verification_channel_id: str | None = None
    log_channel_id: str | None = None
    
    timeout_minutes: int = Field(ge=1, le=1440)
    max_attempts: int = Field(ge=1, le=10)
    risk_threshold_high: int = Field(ge=1, le=100)
    
    language: str = Field(..., description="E.g., en-US, hi-IN")
    delete_failed_messages: bool
    kick_on_timeout: bool


class VerificationSettingsResponse(VerificationSettingsUpdate):
    """Schema for returning verification settings to the dashboard."""
    guild_id: str
    
    # Can add computed fields or stats here if needed


class VerificationSessionResponse(BaseModel):
    """Schema for a pending verification session shown on the dashboard."""
    session_id: str
    user_id: str
    state: str
    verification_type: str
    risk_score: int
    attempts: int
    expires_at: str
