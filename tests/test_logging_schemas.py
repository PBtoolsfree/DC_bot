"""Unit tests for Logging configuration schemas."""

import pytest
from pydantic import ValidationError

from bot.database.schemas.logging import (
    ExportConfig,
    LogChannelConfig,
    LoggingSettings,
)


def test_log_channel_config_defaults() -> None:
    config = LogChannelConfig()
    assert config.enabled is False
    assert config.channel_id is None
    assert config.events == []


def test_log_channel_config_validation() -> None:
    config = LogChannelConfig(enabled=True, channel_id=123, events=["message_delete"])
    assert config.enabled is True
    assert config.channel_id == 123
    assert "message_delete" in config.events

    # Test invalid event
    with pytest.raises(ValidationError):
        LogChannelConfig(events=["invalid_event"])  # type: ignore


def test_logging_settings_defaults() -> None:
    settings = LoggingSettings()
    assert settings.enabled is False
    assert settings.channels == {}
    assert settings.retention_days == 30
    assert settings.mask_ips is True
    assert isinstance(settings.export_schedule, ExportConfig)


def test_logging_settings_from_dict() -> None:
    data = {
        "enabled": True,
        "retention_days": 60,
        "mask_ips": False,
        "channels": {
            "messages": {
                "enabled": True,
                "channel_id": 999,
                "events": ["message_delete", "message_edit"],
            }
        },
    }

    settings = LoggingSettings.from_dict(data)
    assert settings.enabled is True
    assert settings.retention_days == 60
    assert settings.mask_ips is False
    assert "messages" in settings.channels
    assert settings.channels["messages"].channel_id == 999
    assert "message_delete" in settings.channels["messages"].events
