"""Unit tests for the Security configuration cogs."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from bot.cogs.security.security_config import SecurityConfigCog
from bot.database.models.guild import GuildModuleSettings
from bot.database.repositories.guild_repo import GuildRepository
from bot.database.schemas.security import SecuritySettings


@pytest.mark.asyncio
class TestSecurityConfigCog:
    @pytest.fixture
    def cog(self, mock_bot: MagicMock) -> SecurityConfigCog:
        return SecurityConfigCog(mock_bot)

    async def test_status_disabled(
        self, cog: SecurityConfigCog, mock_interaction: MagicMock, mocker: MagicMock
    ) -> None:
        """Test status command when security is disabled."""
        mocker.patch.object(GuildRepository, "get_module_settings", return_value=None)

        await cog.status.callback.__wrapped__(cog, mock_interaction)  # type: ignore

        mock_interaction.response.defer.assert_awaited_once()
        mock_interaction.followup.send.assert_awaited_once()
        embed = mock_interaction.followup.send.call_args[1]["embed"]
        assert "Disabled" in embed.description

    async def test_status_enabled(
        self, cog: SecurityConfigCog, mock_interaction: MagicMock, mocker: MagicMock
    ) -> None:
        """Test status command when security is enabled."""
        settings = SecuritySettings(enabled=True)
        settings.anti_nuke.enabled = True

        db_settings = GuildModuleSettings(
            guild_id=mock_interaction.guild.id,
            module_name="security",
            enabled=True,
            config=settings.model_dump(),
        )

        mocker.patch.object(GuildRepository, "get_module_settings", return_value=db_settings)

        await cog.status.callback.__wrapped__(cog, mock_interaction)  # type: ignore

        mock_interaction.response.defer.assert_awaited_once()
        mock_interaction.followup.send.assert_awaited_once()
        embed = mock_interaction.followup.send.call_args[1]["embed"]
        assert "Overview" in embed.description
        assert len(embed.fields) > 0

    async def test_snapshot_creation(
        self, cog: SecurityConfigCog, mock_interaction: MagicMock, mocker: MagicMock
    ) -> None:
        """Test creating a snapshot via command."""
        from bot.services.security.snapshot_service import SnapshotService

        mocker.patch.object(SnapshotService, "save_snapshot", new_callable=AsyncMock)

        await cog.snapshot.callback.__wrapped__(cog, mock_interaction, name="Test Backup")  # type: ignore

        SnapshotService.save_snapshot.assert_awaited_once()
        mock_interaction.followup.send.assert_awaited_once()
        embed = mock_interaction.followup.send.call_args[1]["embed"]
        assert "successfully created" in embed.description
