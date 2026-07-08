"""Tests for the moderation cog."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.cogs.moderation.moderation import ModerationCog
from bot.services.moderation_service import BotHierarchyError, HierarchyError, ModerationError


@pytest.fixture
def moderation_cog(mock_guild: MagicMock) -> ModerationCog:
    """Fixture for ModerationCog."""
    bot = MagicMock()
    bot.user = MagicMock()
    bot.user.id = 999
    
    cog = ModerationCog(bot)
    # Mock services to isolate cog logic
    cog.mod_service = MagicMock()
    cog.punishment_service = MagicMock()
    cog.history_service = MagicMock()
    cog.logging_service = MagicMock()
    
    return cog


class TestModerationCog:
    """Tests for ModerationCog commands."""

    @pytest.mark.asyncio
    async def test_kick_command_success(
        self,
        moderation_cog: ModerationCog,
        mock_interaction: MagicMock,
        mock_member: MagicMock,
    ) -> None:
        """Should call kick service method and send success message."""
        mock_interaction.response.is_done = MagicMock(return_value=True)
        moderation_cog.mod_service.kick_member = AsyncMock()
        
        # We need a proper context manager for db.session
        mock_session = AsyncMock()
        moderation_cog.bot.db.session.return_value.__aenter__.return_value = mock_session
        
        await moderation_cog.kick.callback(
            moderation_cog, mock_interaction, mock_member, "Rule violation"
        )
        
        mock_interaction.response.defer.assert_called_once()
        moderation_cog.mod_service.kick_member.assert_called_once()
        mock_interaction.followup.send.assert_called_once()
        
        args, kwargs = mock_interaction.followup.send.call_args
        embed = kwargs["embed"]
        assert embed.title == "✅ Member Kicked"

    @pytest.mark.asyncio
    async def test_kick_command_hierarchy_error(
        self,
        moderation_cog: ModerationCog,
        mock_interaction: MagicMock,
        mock_member: MagicMock,
    ) -> None:
        """Should handle HierarchyError gracefully."""
        mock_interaction.response.is_done = MagicMock(return_value=True)
        moderation_cog.mod_service.kick_member = AsyncMock(
            side_effect=HierarchyError("Outranked")
        )
        
        mock_session = AsyncMock()
        moderation_cog.bot.db.session.return_value.__aenter__.return_value = mock_session
        
        await moderation_cog.kick.callback(
            moderation_cog, mock_interaction, mock_member, "Rule violation"
        )
        
        # Verify the error was caught and an error embed was sent
        args, kwargs = mock_interaction.followup.send.call_args
        embed = kwargs["embed"]
        assert embed.title == "❌ Moderation Failed"
        assert "Outranked" in embed.description

    @pytest.mark.asyncio
    async def test_warn_command_success(
        self,
        moderation_cog: ModerationCog,
        mock_interaction: MagicMock,
        mock_member: MagicMock,
    ) -> None:
        """Should call warn service and display punishment if any."""
        mock_warning = MagicMock()
        mock_warning.id = 42
        moderation_cog.punishment_service.add_warning = AsyncMock(
            return_value=(mock_warning, "User auto-timed out.")
        )
        
        mock_session = AsyncMock()
        moderation_cog.bot.db.session.return_value.__aenter__.return_value = mock_session
        
        await moderation_cog.warn.callback(
            moderation_cog, mock_interaction, mock_member, "Spam"
        )
        
        args, kwargs = mock_interaction.followup.send.call_args
        embed = kwargs["embed"]
        assert "Warning ID: `42`" in embed.description
        assert "Auto-Punishment Applied" in embed.description
        assert "User auto-timed out." in embed.description

    @pytest.mark.asyncio
    async def test_purge_command_success(
        self,
        moderation_cog: ModerationCog,
        mock_interaction: MagicMock,
    ) -> None:
        """Should call purge service and send success message."""
        # Set up a valid channel
        mock_interaction.channel = MagicMock(spec=discord.TextChannel)
        
        moderation_cog.mod_service.purge_messages = AsyncMock(return_value=15)
        
        mock_session = AsyncMock()
        moderation_cog.bot.db.session.return_value.__aenter__.return_value = mock_session
        
        await moderation_cog.purge.callback(
            moderation_cog, mock_interaction, amount=20, contains="test"
        )
        
        moderation_cog.mod_service.purge_messages.assert_called_once()
        args, kwargs = mock_interaction.followup.send.call_args
        embed = kwargs["embed"]
        assert "Successfully deleted 15 messages" in embed.description

    @pytest.mark.asyncio
    async def test_purge_command_invalid_channel(
        self,
        moderation_cog: ModerationCog,
        mock_interaction: MagicMock,
    ) -> None:
        """Should reject purge if not in a text-like channel (e.g. DM)."""
        mock_interaction.channel = MagicMock() # Not a TextChannel/Thread/VoiceChannel
        
        await moderation_cog.purge.callback(
            moderation_cog, mock_interaction, amount=10
        )
        
        args, kwargs = mock_interaction.followup.send.call_args
        embed = kwargs["embed"]
        assert "Cannot purge in this channel type" in embed.description

    @pytest.mark.asyncio
    async def test_purge_command_exclusive_filters(
        self,
        moderation_cog: ModerationCog,
        mock_interaction: MagicMock,
    ) -> None:
        """Should reject purge if both bots_only and humans_only are True."""
        await moderation_cog.purge.callback(
            moderation_cog, mock_interaction, amount=10, bots_only=True, humans_only=True
        )
        
        args, kwargs = mock_interaction.response.send_message.call_args
        embed = kwargs["embed"]
        assert "Cannot specify both bots_only and humans_only" in embed.description

    @pytest.mark.asyncio
    async def test_timeout_command_invalid_duration(
        self,
        moderation_cog: ModerationCog,
        mock_interaction: MagicMock,
        mock_member: MagicMock,
    ) -> None:
        """Should handle DurationParseError."""
        mock_interaction.response.is_done = MagicMock(return_value=True)
        # The parser throws error if invalid string is provided
        mock_session = AsyncMock()
        moderation_cog.bot.db.session.return_value.__aenter__.return_value = mock_session
        
        await moderation_cog.timeout.callback(
            moderation_cog, mock_interaction, mock_member, duration="invalid", reason="Test"
        )
        
        args, kwargs = mock_interaction.followup.send.call_args
        embed = kwargs["embed"]
        assert embed.title == "❌ Moderation Failed"
        assert "Could not parse duration" in embed.description
