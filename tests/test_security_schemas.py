"""Unit tests for Security configuration schemas."""

import pytest
from pydantic import ValidationError

from bot.database.schemas.security import (
    AntiNukeConfig,
    AntiNukeRule,
    AntiRaidConfig,
    SecuritySettings,
    WhitelistConfig,
)


def test_anti_nuke_rule_defaults() -> None:
    rule = AntiNukeRule()
    assert rule.enabled is False
    assert rule.threshold == 3
    assert rule.time_window_seconds == 10
    assert rule.action == "ban"


def test_anti_nuke_rule_validation() -> None:
    # Test valid
    rule = AntiNukeRule(enabled=True, threshold=5, time_window_seconds=60, action="kick")
    assert rule.enabled is True
    assert rule.threshold == 5
    assert rule.time_window_seconds == 60
    assert rule.action == "kick"

    # Test invalid threshold
    with pytest.raises(ValidationError):
        AntiNukeRule(threshold=0)

    # Test invalid time window
    with pytest.raises(ValidationError):
        AntiNukeRule(time_window_seconds=0)

    # Test invalid action
    with pytest.raises(ValidationError):
        AntiNukeRule(action="destroy_server")  # type: ignore


def test_security_settings_defaults() -> None:
    settings = SecuritySettings()
    assert settings.enabled is False
    assert isinstance(settings.whitelist, WhitelistConfig)
    assert isinstance(settings.anti_nuke, AntiNukeConfig)
    assert isinstance(settings.anti_raid, AntiRaidConfig)


def test_security_settings_from_dict() -> None:
    data = {
        "enabled": True,
        "anti_nuke": {
            "enabled": True,
            "channel_delete": {
                "enabled": True,
                "threshold": 5,
                "time_window_seconds": 15,
                "action": "timeout",
            },
        },
        "whitelist": {"users": [123, 456], "roles": [789]},
    }

    settings = SecuritySettings.from_dict(data)
    assert settings.enabled is True
    assert settings.anti_nuke.enabled is True
    assert settings.anti_nuke.channel_delete.enabled is True
    assert settings.anti_nuke.channel_delete.threshold == 5
    assert settings.anti_nuke.channel_delete.action == "timeout"
    assert 123 in settings.whitelist.users
    assert 789 in settings.whitelist.roles
