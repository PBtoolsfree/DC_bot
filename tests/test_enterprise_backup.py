"""Tests for Backup System."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bot.services.backup.backup_service import BackupService


@pytest.mark.asyncio
@patch("bot.services.backup.backup_service.StreamingService")
async def test_create_backup_payload(mock_streaming: AsyncMock) -> None:
    mock_streaming.broadcast = AsyncMock()
    session = AsyncMock()
    
    mock_guild = MagicMock()
    mock_guild.id = 123
    
    mock_role = MagicMock()
    mock_role.id = 1
    mock_role.name = "Admin"
    mock_role.color.value = 16711680
    mock_role.permissions.value = 8
    mock_role.position = 10
    mock_role.is_default.return_value = False
    mock_role.managed = False
    
    mock_guild.roles = [mock_role]
    mock_guild.categories = []
    mock_guild.channels = []
    
    backup = await BackupService.create_backup(session, mock_guild, creator_id=999, name="Test Backup")
    
    assert backup.guild_id == 123
    assert backup.name == "Test Backup"
    assert len(backup.payload["roles"]) == 1
    assert backup.payload["roles"][0]["name"] == "Admin"
