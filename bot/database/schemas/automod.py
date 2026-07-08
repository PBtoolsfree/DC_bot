"""Pydantic schemas for AutoMod configuration validation."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AutoModAction(str, Enum):
    """Supported punishments for AutoMod violations."""

    DELETE = "delete"
    WARN = "warn"
    TIMEOUT = "timeout"
    KICK = "kick"
    BAN = "ban"
    SOFTBAN = "softban"
    LOCK_CHANNEL = "lock_channel"
    SLOWMODE = "slowmode"
    NOTIFY_STAFF = "notify_staff"
    DM_USER = "dm_user"


class RuleAction(BaseModel):
    """Configuration for a single AutoMod action."""

    type: AutoModAction = Field(..., description="The type of punishment to apply")
    duration_seconds: int | None = Field(None, ge=0, description="Duration for timeout/slowmode")
    message: str | None = Field(None, description="Custom message for DM or Warning")


class RuleConfig(BaseModel):
    """Configuration for a specific AutoMod rule."""

    enabled: bool = Field(default=False, description="Whether the rule is active")
    threshold: int | None = Field(None, ge=1, description="Triggers required before action")
    cooldown_seconds: int | None = Field(None, ge=1, description="Time window for triggers")
    actions: list[RuleAction] = Field(default_factory=list, description="Actions to execute")

    # Exceptions
    ignored_roles: list[int] = Field(default_factory=list, description="Role IDs to ignore")
    ignored_channels: list[int] = Field(default_factory=list, description="Channel IDs to ignore")
    ignored_users: list[int] = Field(default_factory=list, description="User IDs to ignore")
    ignored_categories: list[int] = Field(
        default_factory=list, description="Category IDs to ignore"
    )

    # Lists
    whitelist: list[str] = Field(
        default_factory=list, description="Allowed items (words, links, domains)"
    )
    blacklist: list[str] = Field(
        default_factory=list, description="Blocked items (words, links, domains)"
    )


class EscalationRule(BaseModel):
    """Rule for escalating punishments based on total recent violations."""

    violation_count: int = Field(..., ge=2, description="Number of recent violations required")
    time_window_seconds: int = Field(..., ge=60, description="Time window for violations")
    actions: list[RuleAction] = Field(
        default_factory=list, description="Actions to execute instead"
    )


class AutoModSettings(BaseModel):
    """Master configuration schema for the AutoMod module."""

    # Spam Protection
    spam_messages: RuleConfig = Field(default_factory=RuleConfig)
    spam_caps: RuleConfig = Field(default_factory=RuleConfig)
    spam_emojis: RuleConfig = Field(default_factory=RuleConfig)
    spam_reactions: RuleConfig = Field(default_factory=RuleConfig)
    spam_mentions: RuleConfig = Field(default_factory=RuleConfig)
    spam_mass_mentions: RuleConfig = Field(default_factory=RuleConfig)
    spam_threads: RuleConfig = Field(default_factory=RuleConfig)
    spam_attachments: RuleConfig = Field(default_factory=RuleConfig)
    spam_media: RuleConfig = Field(default_factory=RuleConfig)
    spam_duplicates: RuleConfig = Field(default_factory=RuleConfig)

    # Link Filtering
    links_invites: RuleConfig = Field(default_factory=RuleConfig)
    links_external: RuleConfig = Field(default_factory=RuleConfig)
    links_scam: RuleConfig = Field(default_factory=RuleConfig)
    links_phishing: RuleConfig = Field(default_factory=RuleConfig)
    links_fake_giveaways: RuleConfig = Field(default_factory=RuleConfig)

    # Profanity & Content Filtering
    words_profanity: RuleConfig = Field(default_factory=RuleConfig)
    words_custom: RuleConfig = Field(default_factory=RuleConfig)
    words_regex: RuleConfig = Field(default_factory=RuleConfig)

    # Security / Abuse
    abuse_zalgo: RuleConfig = Field(default_factory=RuleConfig)
    abuse_invisible: RuleConfig = Field(default_factory=RuleConfig)
    abuse_unicode: RuleConfig = Field(default_factory=RuleConfig)

    # Escalations
    escalation_rules: list[EscalationRule] = Field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AutoModSettings":
        """Safely parse from dictionary, falling back to defaults for missing fields."""
        return cls(**data)
