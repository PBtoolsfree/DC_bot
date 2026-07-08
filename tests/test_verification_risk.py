"""Tests for the Risk Engine."""

import datetime
from unittest.mock import MagicMock

import pytest

from bot.services.verification.risk_engine import RiskEngineService


@pytest.mark.asyncio
async def test_calculate_risk_high() -> None:
    """Test high risk calculation for a new account with no avatar."""
    mock_member = MagicMock()
    # Created 1 hour ago
    mock_member.created_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        hours=1
    )
    mock_member.avatar = None
    mock_member.name = "User12345"

    # 40 (age < 1 day) + 20 (no avatar) + 15 (username pattern) = 75
    score = await RiskEngineService.calculate_risk(mock_member)
    assert score == 75


@pytest.mark.asyncio
async def test_calculate_risk_low() -> None:
    """Test low risk calculation for an old account with an avatar."""
    mock_member = MagicMock()
    # Created 3 years ago
    mock_member.created_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        days=1000
    )
    mock_member.avatar = MagicMock()
    mock_member.name = "ValidUser_NoNumbers"

    score = await RiskEngineService.calculate_risk(mock_member)
    assert score == 0


def test_select_provider() -> None:
    """Test provider selection logic."""
    assert RiskEngineService.select_provider(80, 70) == "image"
    assert RiskEngineService.select_provider(40, 70) == "math"
    assert RiskEngineService.select_provider(10, 70) == "button"
