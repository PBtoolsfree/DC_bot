"""Pydantic schemas for Logging System configuration."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# Available log event categories/actions
LogEvent = Literal[
    "message_delete", "message_edit", "bulk_delete", "message_pin",
    "member_join", "member_leave", "role_create", "role_delete", "role_update",
    "channel_create", "channel_delete", "channel_update", "category_change",
    "voice_join", "voice_leave", "voice_move", "voice_mute", "voice_deaf",
    "nick_change", "username_change", "avatar_change", "server_update",
    "emoji_create", "emoji_delete", "emoji_update",
    "sticker_create", "sticker_delete", "sticker_update",
    "webhook_create", "webhook_delete", "webhook_update",
    "invite_create", "invite_delete",
    "thread_create", "thread_delete",
    "stage_event", "scheduled_event",
    "bot_command", "dashboard_action",
    "moderation_action", "automod_violation", "security_incident"
]


class LogChannelConfig(BaseModel):
    """Configuration for a specific log channel mapping."""
    enabled: bool = False
    channel_id: int | None = Field(default=None, description="The Discord Channel ID to send logs to.")
    events: list[LogEvent] = Field(default_factory=list, description="List of events routed to this channel.")


class ExportConfig(BaseModel):
    """Configuration for automated log exports."""
    enabled: bool = False
    format: Literal["json", "csv", "html"] = "csv"
    schedule_interval_days: int = 7


class LoggingSettings(BaseModel):
    """Master configuration schema for the Logging module."""
    enabled: bool = False
    
    # Map friendly names (e.g., 'message_logs', 'mod_logs') to channel configs
    channels: dict[str, LogChannelConfig] = Field(default_factory=dict)
    
    retention_days: int = Field(default=30, ge=1, le=365, description="Number of days to keep logs in DB.")
    export_schedule: ExportConfig = Field(default_factory=ExportConfig)
    
    # Sensitive data masking
    mask_ips: bool = True
    mask_emails: bool = True
    
    @classmethod
    def from_dict(cls, data: dict) -> LoggingSettings:
        """Parse settings from database JSON dictionary."""
        return cls(**data)
