"""Unit tests for AutoMod Pydantic schemas."""

import pytest
from pydantic import ValidationError

from bot.database.schemas.automod import AutoModAction, AutoModSettings, RuleAction, RuleConfig


def test_automod_settings_defaults() -> None:
    """Test that AutoModSettings initializes with safe defaults."""
    settings = AutoModSettings()

    assert settings.spam_messages.enabled is False
    assert settings.links_external.enabled is False
    assert settings.words_profanity.enabled is False
    assert len(settings.escalation_rules) == 0


def test_automod_settings_from_dict() -> None:
    """Test parsing from a dictionary."""
    data = {
        "spam_messages": {
            "enabled": True,
            "threshold": 5,
            "cooldown_seconds": 10,
            "actions": [
                {"type": "warn", "message": "Stop spamming"},
                {"type": "timeout", "duration_seconds": 3600},
            ],
            "ignored_channels": [123456789],
        },
        "links_invites": {"enabled": True, "actions": [{"type": "delete"}]},
    }

    settings = AutoModSettings.from_dict(data)

    assert settings.spam_messages.enabled is True
    assert settings.spam_messages.threshold == 5
    assert len(settings.spam_messages.actions) == 2
    assert settings.spam_messages.actions[0].type == AutoModAction.WARN
    assert settings.spam_messages.actions[1].type == AutoModAction.TIMEOUT
    assert settings.spam_messages.actions[1].duration_seconds == 3600
    assert 123456789 in settings.spam_messages.ignored_channels

    assert settings.links_invites.enabled is True
    assert settings.links_invites.actions[0].type == AutoModAction.DELETE

    # Check that missing fields fall back to defaults
    assert settings.words_profanity.enabled is False


def test_rule_config_validation() -> None:
    """Test validation constraints on RuleConfig."""
    # Threshold must be >= 1
    with pytest.raises(ValidationError):
        RuleConfig(enabled=True, threshold=0)

    # Cooldown must be >= 1
    with pytest.raises(ValidationError):
        RuleConfig(enabled=True, cooldown_seconds=0)


def test_rule_action_validation() -> None:
    """Test validation constraints on RuleAction."""
    # Invalid action type
    with pytest.raises(ValidationError):
        RuleAction(type="explode")  # type: ignore

    # Duration must be >= 0
    with pytest.raises(ValidationError):
        RuleAction(type=AutoModAction.TIMEOUT, duration_seconds=-5)
