"""Service for managing moderation actions and hierarchy checks."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Literal

import discord

from bot.database.models.member import ModActionType
from bot.database.repositories.member_repo import MemberRepository
from bot.services.logging_service import LoggingService
from bot.utils.logger import get_logger
from bot.utils.permissions import check_bot_hierarchy, check_hierarchy

if TYPE_CHECKING:
    from datetime import timedelta

    from sqlalchemy.ext.asyncio import AsyncSession

    from bot.core.bot import ManagementBot

logger = get_logger(__name__)


class ModerationError(Exception):
    """Base exception for moderation logic errors."""


class HierarchyError(ModerationError):
    """Raised when a hierarchy check fails."""


class BotHierarchyError(ModerationError):
    """Raised when the bot lacks hierarchy to moderate a member."""


class ModerationService:
    """Service handling Discord moderation actions.

    Enforces hierarchy, performs the Discord API call, logs to DB,
    and dispatches to the LoggingService.
    """

    def __init__(self, bot: ManagementBot) -> None:
        """Initialize the moderation service.

        Args:
            bot: The bot instance.
        """
        self.bot = bot
        self.logger_service = LoggingService(bot)

    def _check_hierarchies(
        self,
        moderator: discord.Member,
        target: discord.Member,
    ) -> None:
        """Validate both user and bot hierarchy against the target.

        Raises:
            HierarchyError: If moderator cannot target the member.
            BotHierarchyError: If bot cannot target the member.
        """
        # User vs Target
        if not check_hierarchy(moderator, target):
            raise HierarchyError(
                f"You cannot moderate {target.mention} because their highest role "
                f"is equal to or higher than yours."
            )

        # Bot vs Target
        if not check_bot_hierarchy(moderator.guild.me, target):
            raise BotHierarchyError(
                f"I cannot moderate {target.mention} because their highest role "
                f"is equal to or higher than mine."
            )

    async def kick_member(
        self,
        session: AsyncSession,
        guild: discord.Guild,
        target: discord.Member,
        moderator: discord.Member | discord.User,
        reason: str,
        is_automated: bool = False,
    ) -> None:
        """Kick a member from the guild."""
        if hasattr(moderator, "top_role") and hasattr(target, "top_role"):
            self._check_hierarchies(moderator, target)

        await guild.kick(target, reason=f"By {moderator}: {reason}")

        action = await MemberRepository.log_action(
            session=session,
            guild_id=guild.id,
            user_id=target.id,
            moderator_id=moderator.id,
            action_type=ModActionType.KICK,
            reason=reason,
            is_automated=is_automated,
        )

        await self.logger_service.log_action(session, guild, action, target, moderator)

    async def ban_member(
        self,
        session: AsyncSession,
        guild: discord.Guild,
        target: discord.Member | discord.User,
        moderator: discord.Member | discord.User,
        reason: str,
        delete_message_days: Literal[0, 1, 2, 3, 4, 5, 6, 7] = 0,
        is_automated: bool = False,
    ) -> None:
        """Ban a member or user from the guild."""
        if hasattr(moderator, "top_role") and hasattr(target, "top_role"):
            self._check_hierarchies(moderator, target)

        await guild.ban(
            target,
            reason=f"By {moderator}: {reason}",
            delete_message_days=delete_message_days,
        )

        action = await MemberRepository.log_action(
            session=session,
            guild_id=guild.id,
            user_id=target.id,
            moderator_id=moderator.id,
            action_type=ModActionType.BAN,
            reason=reason,
            details=(
                f"Deleted {delete_message_days} days of messages"
                if delete_message_days > 0
                else None
            ),
            is_automated=is_automated,
        )

        await self.logger_service.log_action(session, guild, action, target, moderator)

    async def unban_member(
        self,
        session: AsyncSession,
        guild: discord.Guild,
        user: discord.User,
        moderator: discord.Member | discord.User,
        reason: str,
    ) -> None:
        """Unban a user from the guild."""
        await guild.unban(user, reason=f"By {moderator}: {reason}")

        action = await MemberRepository.log_action(
            session=session,
            guild_id=guild.id,
            user_id=user.id,
            moderator_id=moderator.id,
            action_type=ModActionType.UNBAN,
            reason=reason,
        )

        await self.logger_service.log_action(session, guild, action, user, moderator)

    async def softban_member(
        self,
        session: AsyncSession,
        guild: discord.Guild,
        target: discord.Member,
        moderator: discord.Member | discord.User,
        reason: str,
        delete_message_days: Literal[0, 1, 2, 3, 4, 5, 6, 7] = 1,
    ) -> None:
        """Ban and immediately unban a member to clear their messages."""
        if hasattr(moderator, "top_role") and hasattr(target, "top_role"):
            self._check_hierarchies(moderator, target)

        await guild.ban(
            target,
            reason=f"Softban by {moderator}: {reason}",
            delete_message_days=delete_message_days,
        )
        await guild.unban(target, reason="Softban release")

        action = await MemberRepository.log_action(
            session=session,
            guild_id=guild.id,
            user_id=target.id,
            moderator_id=moderator.id,
            action_type=ModActionType.SOFTBAN,
            reason=reason,
            details=f"Deleted {delete_message_days} days of messages",
        )

        await self.logger_service.log_action(session, guild, action, target, moderator)

    async def timeout_member(
        self,
        session: AsyncSession,
        guild: discord.Guild,
        target: discord.Member,
        moderator: discord.Member | discord.User,
        duration: timedelta,
        reason: str,
        is_automated: bool = False,
    ) -> None:
        """Timeout a member using Discord's native timeout feature."""
        if hasattr(moderator, "top_role") and hasattr(target, "top_role"):
            self._check_hierarchies(moderator, target)

        # Discord limits timeouts to 28 days
        if duration.total_seconds() > 2419200:
            raise ModerationError("Timeout duration cannot exceed 28 days.")

        await target.timeout(duration, reason=f"By {moderator}: {reason}")

        action = await MemberRepository.log_action(
            session=session,
            guild_id=guild.id,
            user_id=target.id,
            moderator_id=moderator.id,
            action_type=ModActionType.TIMEOUT if not is_automated else ModActionType.AUTO_TIMEOUT,
            reason=reason,
            duration_seconds=int(duration.total_seconds()),
            is_automated=is_automated,
        )

        await self.logger_service.log_action(session, guild, action, target, moderator)

    async def untimeout_member(
        self,
        session: AsyncSession,
        guild: discord.Guild,
        target: discord.Member,
        moderator: discord.Member | discord.User,
        reason: str,
    ) -> None:
        """Remove a member's timeout."""
        if hasattr(moderator, "top_role") and hasattr(target, "top_role"):
            self._check_hierarchies(moderator, target)

        if not target.is_timed_out():
            raise ModerationError("Member is not timed out.")

        await target.timeout(None, reason=f"By {moderator}: {reason}")

        action = await MemberRepository.log_action(
            session=session,
            guild_id=guild.id,
            user_id=target.id,
            moderator_id=moderator.id,
            action_type=ModActionType.UNTIMEOUT,
            reason=reason,
        )

        await self.logger_service.log_action(session, guild, action, target, moderator)

    async def set_nickname(
        self,
        session: AsyncSession,
        guild: discord.Guild,
        target: discord.Member,
        moderator: discord.Member | discord.User,
        nickname: str | None,
        reason: str,
    ) -> None:
        """Change a member's nickname."""
        if isinstance(moderator, discord.Member):
            self._check_hierarchies(moderator, target)

        old_nick = target.display_name
        await target.edit(nick=nickname, reason=f"By {moderator}: {reason}")
        new_nick = nickname if nickname else target.name

        action = await MemberRepository.log_action(
            session=session,
            guild_id=guild.id,
            user_id=target.id,
            moderator_id=moderator.id,
            action_type=ModActionType.NOTE,  # Use note for nick changes
            reason=reason,
            details=f"Nickname changed from '{old_nick}' to '{new_nick}'",
        )

        await self.logger_service.log_action(session, guild, action, target, moderator)

    async def purge_messages(
        self,
        session: AsyncSession,
        channel: discord.TextChannel | discord.Thread | discord.VoiceChannel,
        moderator: discord.Member | discord.User,
        amount: int,
        reason: str,
        target_user: discord.User | discord.Member | None = None,
        contains_text: str | None = None,
        regex_pattern: str | None = None,
        bots_only: bool = False,
        humans_only: bool = False,
        has_attachments: bool = False,
        has_embeds: bool = False,
        has_links: bool = False,
        is_pinned: bool | None = None,
    ) -> int:
        """Bulk delete messages with complex filtering.

        Discord limits bulk delete to messages < 14 days old. We enforce this.
        """
        if amount > 1000:
            raise ModerationError("Cannot purge more than 1000 messages at once.")

        compiled_regex = None
        if regex_pattern:
            try:
                compiled_regex = re.compile(regex_pattern, re.IGNORECASE)
            except re.error as e:
                raise ModerationError(f"Invalid regex pattern: {e}") from None

        def check(m: discord.Message) -> bool:
            # Pinned status
            if is_pinned is not None and m.pinned != is_pinned:
                return False
            # User match
            if target_user and m.author.id != target_user.id:
                return False
            # Bots / Humans
            if bots_only and not m.author.bot:
                return False
            if humans_only and m.author.bot:
                return False
            # Text contains
            if contains_text and contains_text.lower() not in m.content.lower():
                return False
            # Regex match
            if compiled_regex and not compiled_regex.search(m.content):
                return False
            # Attachments
            if has_attachments and not m.attachments:
                return False
            # Embeds
            if has_embeds and not m.embeds:
                return False
            # Links
            return not (has_links and "http" not in m.content.lower())

        deleted = await channel.purge(
            limit=amount,
            check=check,
            bulk=True,
            reason=f"Purge by {moderator}: {reason}",
        )

        deleted_count = len(deleted)
        if deleted_count > 0:
            action = await MemberRepository.log_action(
                session=session,
                guild_id=channel.guild.id,
                user_id=moderator.id,  # Target is the moderator themselves for purges
                moderator_id=moderator.id,
                action_type=ModActionType.PURGE,
                reason=reason,
                details=f"Purged {deleted_count} messages in #{channel.name}",
            )

            await self.logger_service.log_action(
                session, channel.guild, action, f"#{channel.name}", moderator
            )

        return deleted_count

    async def set_slowmode(
        self,
        session: AsyncSession,
        channel: discord.TextChannel | discord.Thread | discord.VoiceChannel,
        moderator: discord.Member | discord.User,
        duration_seconds: int,
        reason: str,
    ) -> None:
        """Set slowmode for a channel."""
        if duration_seconds > 21600:
            raise ModerationError("Slowmode cannot exceed 6 hours.")

        await channel.edit(slowmode_delay=duration_seconds, reason=f"By {moderator}: {reason}")

        action = await MemberRepository.log_action(
            session=session,
            guild_id=channel.guild.id,
            user_id=moderator.id,
            moderator_id=moderator.id,
            action_type=ModActionType.SLOWMODE,
            reason=reason,
            duration_seconds=duration_seconds,
            details=f"Applied in #{channel.name}",
        )

        await self.logger_service.log_action(
            session, channel.guild, action, f"#{channel.name}", moderator
        )

    async def lock_channel(
        self,
        session: AsyncSession,
        channel: discord.TextChannel | discord.VoiceChannel,
        moderator: discord.Member | discord.User,
        reason: str,
    ) -> None:
        """Lock a channel by revoking send_messages for @everyone."""
        guild = channel.guild
        everyone_role = guild.default_role

        overwrites = channel.overwrites_for(everyone_role)
        overwrites.send_messages = False

        await channel.set_permissions(
            everyone_role,
            overwrite=overwrites,
            reason=f"Lockdown by {moderator}: {reason}",
        )

        action = await MemberRepository.log_action(
            session=session,
            guild_id=guild.id,
            user_id=moderator.id,
            moderator_id=moderator.id,
            action_type=ModActionType.LOCKDOWN,
            reason=reason,
            details=f"Locked #{channel.name}",
        )

        await self.logger_service.log_action(session, guild, action, f"#{channel.name}", moderator)

    async def unlock_channel(
        self,
        session: AsyncSession,
        channel: discord.TextChannel | discord.VoiceChannel,
        moderator: discord.Member | discord.User,
        reason: str,
    ) -> None:
        """Unlock a channel by resetting send_messages for @everyone."""
        guild = channel.guild
        everyone_role = guild.default_role

        overwrites = channel.overwrites_for(everyone_role)
        overwrites.send_messages = None  # Reset to default

        await channel.set_permissions(
            everyone_role,
            overwrite=overwrites,
            reason=f"Unlock by {moderator}: {reason}",
        )

        action = await MemberRepository.log_action(
            session=session,
            guild_id=guild.id,
            user_id=moderator.id,
            moderator_id=moderator.id,
            action_type=ModActionType.UNLOCK,
            reason=reason,
            details=f"Unlocked #{channel.name}",
        )

        await self.logger_service.log_action(session, guild, action, f"#{channel.name}", moderator)
