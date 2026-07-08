"""Unit tests for the Logging and Export services."""

import datetime
from unittest.mock import MagicMock

import pytest

from bot.database.models.logging import ActionLog
from bot.database.schemas.logging import LoggingSettings
from bot.services.logging.export_service import ExportService
from bot.services.logging.logging_service import LoggingService


def test_sensitive_data_masking() -> None:
    settings = LoggingSettings(mask_ips=True, mask_emails=True)
    
    text = "User IP is 192.168.1.1 and email is test@example.com."
    masked = LoggingService.mask_sensitive_data(text, settings)
    
    assert "192.168.1.1" not in masked
    assert "[REDACTED IP]" in masked
    assert "test@example.com" not in masked
    assert "[REDACTED EMAIL]" in masked


def test_sensitive_data_masking_disabled() -> None:
    settings = LoggingSettings(mask_ips=False, mask_emails=False)
    
    text = "User IP is 192.168.1.1 and email is test@example.com."
    masked = LoggingService.mask_sensitive_data(text, settings)
    
    assert "192.168.1.1" in masked
    assert "test@example.com" in masked


def test_export_service_csv() -> None:
    log1 = ActionLog(
        id=1, guild_id=123, action_type="test_action", 
        executor_id=456, created_at=datetime.datetime(2023, 1, 1, tzinfo=datetime.timezone.utc),
        before_data={"test": "data"}
    )
    
    csv_buf = ExportService.generate_csv([log1])
    csv_str = csv_buf.getvalue()
    
    assert "test_action" in csv_str
    assert "456" in csv_str
    assert '""test"": ""data""' in csv_str


def test_export_service_json() -> None:
    log1 = ActionLog(
        id=1, guild_id=123, action_type="test_action", 
        executor_id=456, created_at=datetime.datetime(2023, 1, 1, tzinfo=datetime.timezone.utc),
        before_data={"test": "data"}
    )
    
    json_str = ExportService.generate_json([log1])
    
    assert '"action_type": "test_action"' in json_str
    assert '"test": "data"' in json_str
