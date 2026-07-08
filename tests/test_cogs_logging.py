"""Unit tests for Logging cogs and commands."""

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from bot.cogs.logging.logs_config import LoggingConfigCog
from bot.services.logging.search_service import SearchService


@pytest.mark.asyncio
class TestLoggingConfigCog:
    @pytest.fixture
    def cog(self, mock_bot: MagicMock) -> LoggingConfigCog:
        return LoggingConfigCog(mock_bot)

    async def test_search_logs_empty(
        self, 
        cog: LoggingConfigCog, 
        mock_interaction: MagicMock, 
        mocker: MagicMock
    ) -> None:
        """Test search command with no results."""
        mocker.patch.object(SearchService, "search", return_value=[])
        
        await cog.search_logs.callback.__wrapped__(cog, mock_interaction) # type: ignore
        
        mock_interaction.response.defer.assert_awaited_once()
        mock_interaction.followup.send.assert_awaited_once()
        embed = mock_interaction.followup.send.call_args[1]["embed"]
        assert "No logs found" in embed.title or "No logs found" in embed.description

    async def test_search_logs_results(
        self, 
        cog: LoggingConfigCog, 
        mock_interaction: MagicMock, 
        mocker: MagicMock
    ) -> None:
        """Test search command with results."""
        from bot.database.models.logging import ActionLog
        import datetime
        
        log = ActionLog(
            action_type="message_delete", 
            executor_id=123, 
            created_at=datetime.datetime.now(datetime.timezone.utc)
        )
        mocker.patch.object(SearchService, "search", return_value=[log])
        
        await cog.search_logs.callback.__wrapped__(cog, mock_interaction) # type: ignore
        
        mock_interaction.followup.send.assert_awaited_once()
        embed = mock_interaction.followup.send.call_args[1]["embed"]
        assert "Search Results" in embed.title
        assert len(embed.fields) == 1
        assert "message_delete" in embed.fields[0].value

    async def test_export_logs(
        self, 
        cog: LoggingConfigCog, 
        mock_interaction: MagicMock, 
        mocker: MagicMock
    ) -> None:
        """Test export logs command."""
        from bot.database.models.logging import ActionLog
        import datetime
        
        log = ActionLog(
            action_type="message_delete", 
            executor_id=123, 
            created_at=datetime.datetime.now(datetime.timezone.utc)
        )
        mocker.patch.object(SearchService, "search", return_value=[log])
        
        await cog.export_logs.callback.__wrapped__(cog, mock_interaction, format="json") # type: ignore
        
        mock_interaction.followup.send.assert_awaited_once()
        kwargs = mock_interaction.followup.send.call_args[1]
        assert "Exported 1 logs" in kwargs["content"]
        assert isinstance(kwargs["file"], discord.File)
        assert kwargs["file"].filename.endswith(".json")
