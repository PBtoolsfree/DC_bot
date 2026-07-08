"""Unit tests for AutoMod Cogs."""

from unittest.mock import MagicMock

import pytest

from bot.cogs.automod.automod_config import AutoModConfigCog
from bot.database.models.guild import GuildModuleSettings
from bot.database.repositories.guild_repo import GuildRepository
from bot.database.schemas.automod import AutoModSettings


@pytest.mark.asyncio
class TestAutoModConfigCog:
    @pytest.fixture
    def cog(self, mock_bot: MagicMock) -> AutoModConfigCog:
        return AutoModConfigCog(mock_bot)

    async def test_status_disabled(
        self, cog: AutoModConfigCog, mock_interaction: MagicMock, mocker: MagicMock
    ) -> None:
        """Test status command when automod is disabled or config is missing."""
        mocker.patch.object(GuildRepository, "get_module_settings", return_value=None)

        await cog.status.callback.__wrapped__(cog, mock_interaction)  # type: ignore

        mock_interaction.response.defer.assert_awaited_once()
        mock_interaction.followup.send.assert_awaited_once()
        embed = mock_interaction.followup.send.call_args[1]["embed"]
        assert "Disabled" in embed.description

    async def test_status_enabled(
        self, cog: AutoModConfigCog, mock_interaction: MagicMock, mocker: MagicMock
    ) -> None:
        """Test status command when automod is enabled."""
        settings = AutoModSettings()
        settings.spam_messages.enabled = True

        db_settings = GuildModuleSettings(
            guild_id=mock_interaction.guild.id,
            module_name="automod",
            enabled=True,
            config=settings.model_dump(),
        )

        mocker.patch.object(GuildRepository, "get_module_settings", return_value=db_settings)

        await cog.status.callback.__wrapped__(cog, mock_interaction)  # type: ignore

        mock_interaction.response.defer.assert_awaited_once()
        mock_interaction.followup.send.assert_awaited_once()
        embed = mock_interaction.followup.send.call_args[1]["embed"]
        assert "Enabled" in embed.description
        assert len(embed.fields) > 0

    async def test_toggle_enable(
        self, cog: AutoModConfigCog, mock_interaction: MagicMock, mocker: MagicMock
    ) -> None:
        """Test toggle enable command."""
        mocker.patch.object(GuildRepository, "get_or_create_module_settings", return_value=None)
        mocker.patch.object(GuildRepository, "update_module_settings", return_value=None)

        from discord import app_commands

        await cog.toggle.callback.__wrapped__(cog, mock_interaction, app_commands.Choice(name="Enable", value="enable"))  # type: ignore

        GuildRepository.update_module_settings.assert_awaited_once_with(
            cog.bot.db.session.return_value.__aenter__.return_value,
            mock_interaction.guild.id,
            "automod",
            enabled=True,
        )

        mock_interaction.followup.send.assert_awaited_once()
        embed = mock_interaction.followup.send.call_args[1]["embed"]
        assert "enabled" in embed.description
