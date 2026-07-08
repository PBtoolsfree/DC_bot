"""Tests for XP & Leveling Logic."""

import pytest

from bot.services.xp.xp_service import XPService


@pytest.mark.asyncio
async def test_xp_curve_calculation() -> None:
    service = XPService()

    # 0 XP = Level 0
    assert service._calculate_level(0) == 0

    # 100 XP = Level 1
    assert service._calculate_level(100) == 1

    # 255 XP = Level 2 (100 + 155)
    assert service._calculate_level(255) == 2

    # 475 XP = Level 3 (100 + 155 + 220)
    assert service._calculate_level(475) == 3
