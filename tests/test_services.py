"""Tests for moderation and punishment services."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.member import ModActionType, Warning
from bot.database.repositories.guild_repo import GuildRepository
from bot.database.repositories.member_repo import MemberRepository
from bot.services.history_service import HistoryService
from bot.services.moderation_service import BotHierarchyError, HierarchyError, ModerationError, ModerationService
from bot.services.punishment_service import PunishmentService


@pytest.fixture
def mod_service(mock_guild: MagicMock) -> ModerationService:
    """Fixture for ModerationService."""
    bot = MagicMock()
    bot.user = MagicMock()
    bot.user.id = 999
    bot.user.display_avatar.url = "http://avatar.test"
    return ModerationService(bot)


@pytest.fixture
def punishment_service(mod_service: ModerationService) -> PunishmentService:
    """Fixture for PunishmentService."""
    return PunishmentService(mod_service.bot, mod_service)


class TestModerationService:
    """Tests for ModerationService."""

    @pytest.mark.asyncio
    async def test_kick_member_success(
        self,
        db_session: AsyncSession,
        mod_service: ModerationService,
        mock_guild: MagicMock,
        mock_member: MagicMock,
        mock_admin_member: MagicMock,
    ) -> None:
        """Should kick member and log action."""
        mock_guild.kick = AsyncMock()
        
        await mod_service.kick_member(
            db_session, mock_guild, mock_member, mock_admin_member, "Rule violation"
        )
        await db_session.flush()

        mock_guild.kick.assert_called_once_with(
            mock_member, reason=f"By {mock_admin_member}: Rule violation"
        )

        actions = await MemberRepository.get_actions(db_session, mock_guild.id)
        assert len(actions) == 1
        assert actions[0].action_type == "kick"
        assert actions[0].reason == "Rule violation"

    @patch("bot.services.moderation_service.check_hierarchy", return_value=False)
    @pytest.mark.asyncio
    async def test_hierarchy_error(
        self,
        mock_check_hierarchy: MagicMock,
        db_session: AsyncSession,
        mod_service: ModerationService,
        mock_guild: MagicMock,
        mock_member: MagicMock,
        mock_admin_member: MagicMock,
    ) -> None:
        """Should raise HierarchyError if moderator outranked."""
        with pytest.raises(HierarchyError):
            await mod_service.kick_member(
                db_session, mock_guild, mock_admin_member, mock_member, "Nice try"
            )

    @patch("bot.services.moderation_service.check_hierarchy", return_value=True)
    @patch("bot.services.moderation_service.check_bot_hierarchy", return_value=False)
    @pytest.mark.asyncio
    async def test_bot_hierarchy_error(
        self,
        mock_check_bot: MagicMock,
        mock_check: MagicMock,
        db_session: AsyncSession,
        mod_service: ModerationService,
        mock_guild: MagicMock,
        mock_member: MagicMock,
        mock_admin_member: MagicMock,
    ) -> None:
        """Should raise BotHierarchyError if bot outranked."""
        with pytest.raises(BotHierarchyError):
            await mod_service.kick_member(
                db_session, mock_guild, mock_admin_member, mock_admin_member, "Test"
            )

    @pytest.mark.asyncio
    async def test_ban_member(
        self,
        db_session: AsyncSession,
        mod_service: ModerationService,
        mock_guild: MagicMock,
        mock_member: MagicMock,
        mock_admin_member: MagicMock,
    ) -> None:
        """Should ban member and log action."""
        mock_guild.ban = AsyncMock()
        
        await mod_service.ban_member(
            db_session, mock_guild, mock_member, mock_admin_member, "Spam", 7
        )
        await db_session.flush()

        mock_guild.ban.assert_called_once_with(
            mock_member, reason=f"By {mock_admin_member}: Spam", delete_message_days=7
        )
        
        actions = await MemberRepository.get_actions(db_session, mock_guild.id)
        assert len(actions) == 1
        assert actions[0].action_type == "ban"
        assert "Deleted 7 days" in str(actions[0].details)

    @pytest.mark.asyncio
    async def test_softban_member(
        self,
        db_session: AsyncSession,
        mod_service: ModerationService,
        mock_guild: MagicMock,
        mock_member: MagicMock,
        mock_admin_member: MagicMock,
    ) -> None:
        """Should ban then unban member and log action."""
        mock_guild.ban = AsyncMock()
        mock_guild.unban = AsyncMock()
        
        await mod_service.softban_member(
            db_session, mock_guild, mock_member, mock_admin_member, "Cleanup", 1
        )
        await db_session.flush()

        mock_guild.ban.assert_called_once()
        mock_guild.unban.assert_called_once()
        
        actions = await MemberRepository.get_actions(db_session, mock_guild.id)
        assert len(actions) == 1
        assert actions[0].action_type == "softban"

    @pytest.mark.asyncio
    async def test_timeout_member(
        self,
        db_session: AsyncSession,
        mod_service: ModerationService,
        mock_guild: MagicMock,
        mock_member: MagicMock,
        mock_admin_member: MagicMock,
    ) -> None:
        """Should timeout member and log action."""
        mock_member.timeout = AsyncMock()
        duration = timedelta(hours=2)
        
        await mod_service.timeout_member(
            db_session, mock_guild, mock_member, mock_admin_member, duration, "Spam"
        )
        await db_session.flush()

        mock_member.timeout.assert_called_once_with(
            duration, reason=f"By {mock_admin_member}: Spam"
        )
        
        actions = await MemberRepository.get_actions(db_session, mock_guild.id)
        assert len(actions) == 1
        assert actions[0].action_type == "timeout"
        assert actions[0].duration_seconds == 7200

    @pytest.mark.asyncio
    async def test_timeout_exceeds_limit(
        self,
        db_session: AsyncSession,
        mod_service: ModerationService,
        mock_guild: MagicMock,
        mock_member: MagicMock,
        mock_admin_member: MagicMock,
    ) -> None:
        """Should raise ModerationError if timeout exceeds 28 days."""
        duration = timedelta(days=30)
        
        with pytest.raises(ModerationError, match="cannot exceed 28 days"):
            await mod_service.timeout_member(
                db_session, mock_guild, mock_member, mock_admin_member, duration, "Test"
            )

    @pytest.mark.asyncio
    async def test_purge_messages(
        self,
        db_session: AsyncSession,
        mod_service: ModerationService,
        mock_guild: MagicMock,
        mock_admin_member: MagicMock,
    ) -> None:
        """Should purge messages and log action."""
        channel = MagicMock()
        channel.guild = mock_guild
        channel.name = "general"
        
        # Mock purge returning a list of 5 deleted messages
        messages = [MagicMock() for _ in range(5)]
        channel.purge = AsyncMock(return_value=messages)
        
        deleted = await mod_service.purge_messages(
            db_session, channel, mock_admin_member, 10, "Cleanup"
        )
        await db_session.flush()

        assert deleted == 5
        channel.purge.assert_called_once()
        
        actions = await MemberRepository.get_actions(db_session, mock_guild.id)
        assert len(actions) == 1
        assert actions[0].action_type == "purge"
        assert "Purged 5 messages" in str(actions[0].details)

    @pytest.mark.asyncio
    async def test_purge_regex_error(
        self,
        db_session: AsyncSession,
        mod_service: ModerationService,
        mock_guild: MagicMock,
        mock_admin_member: MagicMock,
    ) -> None:
        """Should raise ModerationError on invalid regex."""
        channel = MagicMock()
        
        with pytest.raises(ModerationError, match="Invalid regex"):
            await mod_service.purge_messages(
                db_session, channel, mock_admin_member, 10, "Test", regex_pattern="["
            )

    @pytest.mark.asyncio
    async def test_lock_channel(
        self,
        db_session: AsyncSession,
        mod_service: ModerationService,
        mock_guild: MagicMock,
        mock_admin_member: MagicMock,
    ) -> None:
        """Should lock channel and log action."""
        channel = MagicMock()
        mock_guild.default_role = MagicMock()
        channel.guild = mock_guild
        channel.name = "general"
        channel.overwrites_for = MagicMock(return_value=discord.PermissionOverwrite())
        channel.set_permissions = AsyncMock()
        
        await mod_service.lock_channel(
            db_session, channel, mock_admin_member, "Raid"
        )
        await db_session.flush()

        channel.set_permissions.assert_called_once()
        
        # Verify send_messages was set to False
        args, kwargs = channel.set_permissions.call_args
        assert kwargs["overwrite"].send_messages is False
        
        actions = await MemberRepository.get_actions(db_session, mock_guild.id)
        assert len(actions) == 1
        assert actions[0].action_type == "lockdown"


class TestPunishmentService:
    """Tests for PunishmentService."""

    @pytest.mark.asyncio
    async def test_add_warning_no_punishment(
        self,
        db_session: AsyncSession,
        punishment_service: PunishmentService,
        mock_guild: MagicMock,
        mock_member: MagicMock,
        mock_admin_member: MagicMock,
    ) -> None:
        """Should add warning and return None for punishment_msg."""
        warn, msg = await punishment_service.add_warning(
            db_session, mock_guild, mock_member, mock_admin_member, "First offense"
        )
        await db_session.flush()

        assert warn.id is not None
        assert msg is None
        
        warnings = await MemberRepository.get_warnings(db_session, mock_guild.id, mock_member.id)
        assert len(warnings) == 1
        assert warnings[0].reason == "First offense"
        
        actions = await MemberRepository.get_actions(db_session, mock_guild.id)
        assert len(actions) == 1
        assert actions[0].action_type == "warn"

    @pytest.mark.asyncio
    async def test_add_warning_with_auto_punishment(
        self,
        db_session: AsyncSession,
        punishment_service: PunishmentService,
        mock_guild: MagicMock,
        mock_member: MagicMock,
        mock_admin_member: MagicMock,
    ) -> None:
        """Should trigger auto punishment when threshold met."""
        # Setup thresholds: 2 warnings = timeout
        await GuildRepository.get_or_create_config(db_session, mock_guild.id)
        await GuildRepository.get_or_create_module_settings(
            db_session, mock_guild.id, "moderation",
            {"warn_thresholds": {"2": {"action": "timeout", "duration": 3600}}}
        )
        await db_session.flush()

        punishment_service.mod_service.timeout_member = AsyncMock()

        # Warning 1
        _, msg1 = await punishment_service.add_warning(
            db_session, mock_guild, mock_member, mock_admin_member, "First"
        )
        await db_session.flush()
        assert msg1 is None
        
        # Warning 2 - Should trigger timeout
        _, msg2 = await punishment_service.add_warning(
            db_session, mock_guild, mock_member, mock_admin_member, "Second"
        )
        
        assert msg2 is not None
        assert "auto-timed out" in msg2
        punishment_service.mod_service.timeout_member.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_warnings(
        self,
        db_session: AsyncSession,
        punishment_service: PunishmentService,
        mock_guild: MagicMock,
        mock_member: MagicMock,
        mock_admin_member: MagicMock,
    ) -> None:
        """Should clear all active warnings."""
        # Add 3 warnings
        for i in range(3):
            await punishment_service.add_warning(
                db_session, mock_guild, mock_member, mock_admin_member, f"Warn {i}"
            )
        await db_session.flush()
        
        count = await punishment_service.clear_warnings(
            db_session, mock_guild, mock_member, mock_admin_member
        )
        await db_session.flush()
        
        assert count == 3
        
        warnings = await MemberRepository.get_warnings(db_session, mock_guild.id, mock_member.id)
        assert len(warnings) == 0


class TestHistoryService:
    """Tests for HistoryService."""

    @pytest.mark.asyncio
    async def test_get_user_history_embeds_empty(
        self,
        db_session: AsyncSession,
        mock_guild: MagicMock,
        mock_member: MagicMock,
    ) -> None:
        """Should return a single info embed when history is empty."""
        embeds = await HistoryService.get_user_history_embeds(
            db_session, mock_guild, mock_member
        )
        
        assert len(embeds) == 1
        assert "No moderation history found" in str(embeds[0].description)

    @pytest.mark.asyncio
    async def test_get_user_history_embeds_pagination(
        self,
        db_session: AsyncSession,
        punishment_service: PunishmentService,
        mock_guild: MagicMock,
        mock_member: MagicMock,
        mock_admin_member: MagicMock,
    ) -> None:
        """Should paginate history correctly (5 items per page)."""
        # Create 12 warnings (which will log 12 mod actions)
        for i in range(12):
            await punishment_service.add_warning(
                db_session, mock_guild, mock_member, mock_admin_member, f"Warn {i}"
            )
        await db_session.flush()
        
        embeds = await HistoryService.get_user_history_embeds(
            db_session, mock_guild, mock_member
        )
        
        assert len(embeds) == 3 # 12 items / 5 per page = 3 pages
        assert "Page 1/3" in str(embeds[0].footer.text)
        assert len(embeds[0].fields) == 5
        assert len(embeds[1].fields) == 5
        assert len(embeds[2].fields) == 2
