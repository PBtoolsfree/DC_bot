"""Pydantic schemas for XP System."""

from pydantic import BaseModel, Field


class XPSettingsSchema(BaseModel):
    enabled: bool
    message_xp_min: int = Field(15, ge=1)
    message_xp_max: int = Field(25, ge=1)
    message_cooldown_sec: int = Field(60, ge=0)
    voice_xp_per_minute: int = Field(10, ge=0)
    ignored_channels: list[str] = Field(default_factory=list)


class XPRewardSchema(BaseModel):
    id: int | None = None
    level: int = Field(..., ge=1)
    role_id: str
    remove_on_demotion: bool = True
