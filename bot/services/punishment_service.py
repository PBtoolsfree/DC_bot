"""Service for managing warnings and evaluating auto-punishments."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

import discord
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.member import ModActionType, Warning
from bot.database.repositories.guild_repo import GuildRepository
from bot.database.repositories.member_repo import MemberRepository
from bot.services.logging_service import LoggingService
from bot.utils.logger import get_logger

if TYPE_CHECKING:
    from bot.core.bot import ManagementBot
    from bot.services.moderation_service import ModerationService

logger = get_logger(__name__)


class PunishmentService:
    """Service handling Warnings and configurable Auto-Punishments."""

    def __init__(self, bot: ManagementBot, mod_service: ModerationService) -> None:
        """Initialize the punishment service.

        Args:
            bot: The bot instance.
            mod_service: Moderation service for executing auto-punishments.
        """
        self.bot = bot
        self.mod_service = mod_service
        self.logger_service = LoggingService(bot)

    async def add_warning(
        self,
        session: AsyncSession,
        guild: discord.Guild,
        target: discord.Member,
        moderator: discord.Member | discord.User,
        reason: str,
    ) -> tuple[Warning, str | None]:
        """Issue a warning to a member and evaluate auto-punishments.

        Args:
            session: Active database session.
            guild: The Discord guild.
            target: Target member.
            moderator: Issuing moderator.
            reason: Warning reason.

        Returns:
            A tuple of (The created Warning, String describing any auto-punishment taken).
        """
        # Ensure hierarchy checks out (ModerationService does this internally
        # for punishments, but we should do it for the warn itself too).
        self.mod_service._check_hierarchies(moderator, target)

        warning = await MemberRepository.add_warning(
            session, guild.id, target.id, moderator.id, reason
        )

        # Log the warning ModAction
        action = await MemberRepository.log_action(
            session,
            guild.id,
            target.id,
            moderator.id,
            ModActionType.WARN,
            reason,
        )

        await self.logger_service.log_action(session, guild, action, target, moderator)

        # Flush to ensure the warning is written to DB and readable by count
        await session.flush()

        # Evaluate auto-punishments
        active_warnings = await MemberRepository.get_warning_count(session, guild.id, target.id)

        punishment_msg = await self._evaluate_thresholds(
            session, guild, target, active_warnings, reason
        )

        return warning, punishment_msg

    async def _evaluate_thresholds(
        self,
        session: AsyncSession,
        guild: discord.Guild,
        target: discord.Member,
        warning_count: int,
        original_reason: str,
    ) -> str | None:
        """Check if the member reached a warning threshold and punish them.

        Args:
            session: Active database session.
            guild: The Discord guild.
            target: The target member.
            warning_count: Current number of active warnings.
            original_reason: The reason for the last warning.

        Returns:
            A string describing the punishment taken, or None if no threshold met.
        """
        settings = await GuildRepository.get_or_create_module_settings(
            session, guild.id, "moderation"
        )

        # Structure: {"warn_thresholds": {"3": {"action": "timeout", "duration": 3600}, "5": {"action": "kick"}}}
        thresholds = settings.config.get("warn_thresholds", {})
        count_str = str(warning_count)

        if count_str not in thresholds:
            return None

        punishment = thresholds[count_str]
        action = punishment.get("action")
        duration = punishment.get("duration", 3600)  # Default 1h timeout

        reason = (
            f"Auto-punishment (Reached {warning_count} warnings) - Last reason: {original_reason}"
        )
        bot_user = self.bot.user

        try:
            if action == "timeout":
                await self.mod_service.timeout_member(
                    session,
                    guild,
                    target,
                    bot_user,
                    timedelta(seconds=duration),
                    reason,
                    is_automated=True,
                )
                from bot.utils.time_parser import format_seconds

                return f"Member auto-timed out for {format_seconds(duration)}."

            if action == "kick":
                await self.mod_service.kick_member(
                    session, guild, target, bot_user, reason, is_automated=True
                )
                return "Member auto-kicked."

            if action == "ban":
                await self.mod_service.ban_member(
                    session, guild, target, bot_user, reason, is_automated=True
                )
                return "Member auto-banned."

        except Exception as e:
            logger.error(
                "punishment_service.execution_failed",
                guild_id=guild.id,
                user_id=target.id,
                action=action,
                error=str(e),
            )
            return f"Failed to execute auto-punishment '{action}': {e!s}"

        return None

    async def pardon_warning(
        self,
        session: AsyncSession,
        warning_id: int,
        moderator: discord.Member | discord.User,
    ) -> bool:
        """Pardon a specific warning.

        Args:
            session: Active database session.
            warning_id: The ID of the warning to pardon.
            moderator: The moderator performing the pardon.

        Returns:
            True if pardoned successfully, False if not found or already pardoned.
        """
        warning = await MemberRepository.pardon_warning(session, warning_id, moderator.id)
        return warning is not None

    async def clear_warnings(
        self,
        session: AsyncSession,
        guild: discord.Guild,
        target: discord.Member | discord.User,
        moderator: discord.Member | discord.User,
    ) -> int:
        """Clear all active warnings for a member.

        Args:
            session: Active database session.
            guild: The Discord guild.
            target: The target user.
            moderator: The moderator clearing warnings.

        Returns:
            The number of warnings cleared.
        """
        count = await MemberRepository.clear_warnings(session, guild.id, target.id, moderator.id)
        return count
