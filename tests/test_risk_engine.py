"""Unit tests for the Risk Engine service."""

from unittest.mock import MagicMock

import discord
import pytest

from bot.database.schemas.security import SecuritySettings
from bot.services.security.risk_engine_service import RiskEngineService


@pytest.fixture
def mock_guild() -> MagicMock:
    guild = MagicMock(spec=discord.Guild)
    guild.features = ["COMMUNITY"]
    guild.verification_level = discord.VerificationLevel.high
    guild.explicit_content_filter = discord.ContentFilter.all_members
    
    # Create safe roles
    safe_role = MagicMock(spec=discord.Role)
    safe_role.is_default.return_value = False
    safe_role.managed = False
    safe_role.permissions.administrator = False
    safe_role.permissions.manage_guild = False
    safe_role.permissions.ban_members = False
    safe_role.permissions.manage_roles = False
    safe_role.permissions.manage_channels = False
    
    guild.roles = [safe_role, safe_role]
    return guild


def test_health_score_perfect(mock_guild: MagicMock) -> None:
    settings = SecuritySettings(enabled=True)
    settings.anti_nuke.enabled = True
    settings.anti_nuke.channel_delete.enabled = True
    settings.anti_nuke.role_delete.enabled = True
    settings.anti_nuke.member_ban.enabled = True
    
    settings.anti_raid.enabled = True
    settings.anti_raid.mass_join.enabled = True
    settings.anti_raid.invite_spam.enabled = True

    score = RiskEngineService.calculate_health_score(mock_guild, settings)
    assert score == 100


def test_health_score_disabled() -> None:
    settings = SecuritySettings(enabled=False)
    score = RiskEngineService.calculate_health_score(MagicMock(), settings)
    assert score == 0


def test_health_score_missing_anti_nuke(mock_guild: MagicMock) -> None:
    settings = SecuritySettings(enabled=True)
    settings.anti_nuke.enabled = False # -30 points
    
    settings.anti_raid.enabled = True
    settings.anti_raid.mass_join.enabled = True
    settings.anti_raid.invite_spam.enabled = True

    score = RiskEngineService.calculate_health_score(mock_guild, settings)
    assert score == 70


def test_health_score_dangerous_roles(mock_guild: MagicMock) -> None:
    settings = SecuritySettings(enabled=True)
    settings.anti_nuke.enabled = True
    settings.anti_nuke.channel_delete.enabled = True
    settings.anti_nuke.role_delete.enabled = True
    settings.anti_nuke.member_ban.enabled = True
    settings.anti_raid.enabled = True
    settings.anti_raid.mass_join.enabled = True
    settings.anti_raid.invite_spam.enabled = True

    # Add 6 dangerous roles (1 over the limit of 5, so -2 points)
    for _ in range(6):
        dangerous_role = MagicMock(spec=discord.Role)
        dangerous_role.is_default.return_value = False
        dangerous_role.managed = False
        dangerous_role.permissions.administrator = True
        mock_guild.roles.append(dangerous_role)

    score = RiskEngineService.calculate_health_score(mock_guild, settings)
    assert score == 98 # 100 - (6-5)*2
