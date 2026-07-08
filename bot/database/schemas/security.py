"""Pydantic schemas for Security System configuration."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# Using Literal for action types to ensure valid choices
SecurityAction = Literal["warn", "timeout", "kick", "ban", "lock_channel", "remove_roles"]


class WhitelistConfig(BaseModel):
    """Whitelist configuration for bypassing security rules."""
    users: list[int] = Field(default_factory=list, description="User IDs exempt from all security checks")
    roles: list[int] = Field(default_factory=list, description="Role IDs exempt from all security checks")
    bots: list[int] = Field(default_factory=list, description="Bot IDs exempt from anti-bot and anti-nuke")


class AntiNukeRule(BaseModel):
    """Configuration for a specific Anti-Nuke rule."""
    enabled: bool = False
    threshold: int = Field(default=3, ge=1, description="Actions allowed within the time window")
    time_window_seconds: int = Field(default=10, ge=1, description="Time window for threshold")
    action: SecurityAction = Field(default="ban", description="Action to take when triggered")


class AntiNukeConfig(BaseModel):
    """Configuration for Anti-Nuke systems."""
    enabled: bool = False
    channel_create: AntiNukeRule = Field(default_factory=AntiNukeRule)
    channel_delete: AntiNukeRule = Field(default_factory=AntiNukeRule)
    channel_update: AntiNukeRule = Field(default_factory=AntiNukeRule)
    role_create: AntiNukeRule = Field(default_factory=AntiNukeRule)
    role_delete: AntiNukeRule = Field(default_factory=AntiNukeRule)
    role_update: AntiNukeRule = Field(default_factory=AntiNukeRule)
    webhook_create: AntiNukeRule = Field(default_factory=AntiNukeRule)
    webhook_delete: AntiNukeRule = Field(default_factory=AntiNukeRule)
    emoji_create: AntiNukeRule = Field(default_factory=AntiNukeRule)
    emoji_delete: AntiNukeRule = Field(default_factory=AntiNukeRule)
    sticker_create: AntiNukeRule = Field(default_factory=AntiNukeRule)
    sticker_delete: AntiNukeRule = Field(default_factory=AntiNukeRule)
    member_ban: AntiNukeRule = Field(default_factory=AntiNukeRule)
    member_kick: AntiNukeRule = Field(default_factory=AntiNukeRule)


class AntiRaidRule(BaseModel):
    """Configuration for a specific Anti-Raid rule."""
    enabled: bool = False
    threshold: int = Field(default=10, ge=1)
    time_window_seconds: int = Field(default=10, ge=1)
    action: SecurityAction = Field(default="kick")


class AntiRaidConfig(BaseModel):
    """Configuration for Anti-Raid systems."""
    enabled: bool = False
    mass_join: AntiRaidRule = Field(default_factory=AntiRaidRule)
    invite_spam: AntiRaidRule = Field(default_factory=AntiRaidRule)
    everyone_ping: AntiRaidRule = Field(default_factory=AntiRaidRule)
    bot_add: AntiRaidRule = Field(default_factory=AntiRaidRule)


class SimulationConfig(BaseModel):
    """Configuration for simulation mode."""
    enabled: bool = False
    log_channel_id: int | None = Field(default=None, description="Channel ID to send simulation alerts")


class SecuritySettings(BaseModel):
    """Master configuration schema for the Security module."""
    enabled: bool = False
    log_channel_id: int | None = Field(default=None, description="Where to log incidents")
    
    whitelist: WhitelistConfig = Field(default_factory=WhitelistConfig)
    anti_nuke: AntiNukeConfig = Field(default_factory=AntiNukeConfig)
    anti_raid: AntiRaidConfig = Field(default_factory=AntiRaidConfig)
    simulation_mode: SimulationConfig = Field(default_factory=SimulationConfig)

    @classmethod
    def from_dict(cls, data: dict) -> SecuritySettings:
        """Parse settings from database JSON dictionary."""
        return cls(**data)
