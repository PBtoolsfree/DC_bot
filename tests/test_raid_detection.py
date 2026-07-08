"""Unit tests for the Raid Detection service."""

from unittest.mock import AsyncMock

import pytest

from bot.database.schemas.security import AntiNukeRule
from bot.services.security.raid_detection_service import RaidDetectionService


@pytest.mark.asyncio
async def test_add_action_disabled() -> None:
    mock_redis = AsyncMock()
    service = RaidDetectionService(mock_redis)

    rule = AntiNukeRule(enabled=False, threshold=3)
    exceeded = await service.add_action_and_check(123, "test_action", rule, 456)

    assert exceeded is False
    mock_redis.zadd.assert_not_called()


@pytest.mark.asyncio
async def test_add_action_below_threshold() -> None:
    mock_redis = AsyncMock()
    mock_redis.zcard.return_value = 2  # Below threshold of 3
    service = RaidDetectionService(mock_redis)

    rule = AntiNukeRule(enabled=True, threshold=3)
    exceeded = await service.add_action_and_check(123, "test_action", rule, 456)

    assert exceeded is False
    mock_redis.zadd.assert_awaited_once()
    mock_redis.zcard.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_action_exceeds_threshold() -> None:
    mock_redis = AsyncMock()
    mock_redis.zcard.return_value = 3  # Meets threshold of 3
    service = RaidDetectionService(mock_redis)

    rule = AntiNukeRule(enabled=True, threshold=3)
    exceeded = await service.add_action_and_check(123, "test_action", rule, 456)

    assert exceeded is True
    mock_redis.zadd.assert_awaited_once()
    mock_redis.zcard.assert_awaited_once()
