"""Violation handling and escalation service for AutoMod.

When a rule is triggered, this service determines the correct
punishments to apply, calculates escalations based on history,
and executes the actions via ModerationService.
"""

from __future__ import annotations

import contextlib
from datetime import timedelta
from typing import TYPE_CHECKING

import discord

from bot.database.models.member import ModActionType
from bot.database.repositories.member_repo import MemberRepository
from bot.database.schemas.automod import AutoModAction, AutoModSettings, RuleAction, RuleConfig
from bot.services.moderation_service import ModerationService
from bot.utils.logger import get_logger

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from bot.core.bot import ManagementBot

logger = get_logger(__name__)


class ViolationService:
    """Service for handling AutoMod violations and executing punishments."""

    def __init__(self, bot: ManagementBot) -> None:
        self.bot = bot
        self.mod_service = ModerationService(bot)

    async def _escalate_actions(
        self,
        session: AsyncSession,
        guild_id: int,
        user_id: int,
        settings: AutoModSettings,
        default_actions: list[RuleAction],
    ) -> list[RuleAction]:
        """Check user history and escalate actions if necessary."""
        if not settings.escalation_rules:
            return default_actions

        # We need the most strict escalation rule that applies.
        # Find the maximum time window we need to query for
        max_window = max(rule.time_window_seconds for rule in settings.escalation_rules)

        # Get violation count in that window
        recent_violations = await MemberRepository.get_action_count(
            session, guild_id, user_id, seconds_ago=max_window, is_automated=True
        )

        if recent_violations <= 1:
            return default_actions

        # Sort escalation rules by violation count descending to apply the highest tier
        sorted_escalations = sorted(
            settings.escalation_rules, key=lambda r: r.violation_count, reverse=True
        )

        for rule in sorted_escalations:
            # If the user has enough recent violations, apply this escalation
            # We recalculate for the specific rule's time window if it's smaller
            if rule.time_window_seconds < max_window:
                count_in_window = await MemberRepository.get_action_count(
                    session,
                    guild_id,
                    user_id,
                    seconds_ago=rule.time_window_seconds,
                    is_automated=True,
                )
                if count_in_window >= rule.violation_count:
                    logger.info(
                        "automod_escalated",
                        user_id=user_id,
                        count=count_in_window,
                        rule=rule.violation_count,
                    )
                    return rule.actions
            elif recent_violations >= rule.violation_count:
                logger.info(
                    "automod_escalated",
                    user_id=user_id,
                    count=recent_violations,
                    rule=rule.violation_count,
                )
                return rule.actions

        return default_actions

    async def handle_violation(
        self,
        session: AsyncSession,
        message: discord.Message,
        rule_name: str,
        settings: AutoModSettings,
    ) -> None:
        """Execute punishments for a triggered rule."""
        if not message.guild or not isinstance(message.author, discord.Member):
            return

        guild = message.guild
        target = message.author
        bot_user = guild.me

        # Get the rule configuration
        rule_config: RuleConfig = getattr(settings, rule_name)
        if not rule_config.actions:
            # No actions configured, just return
            return

        # Calculate Escalation
        actions_to_execute = await self._escalate_actions(
            session, guild.id, target.id, settings, rule_config.actions
        )

        reason = f"AutoMod violation: {rule_name}"

        for action in actions_to_execute:
            try:
                if action.type == AutoModAction.DELETE:
                    # Ignore if message is already deleted
                    with contextlib.suppress(discord.NotFound):
                        await message.delete()

                elif action.type == AutoModAction.WARN:
                    # We log it manually to maintain context of 'is_automated'
                    mod_action = await MemberRepository.log_action(
                        session=session,
                        guild_id=guild.id,
                        user_id=target.id,
                        moderator_id=bot_user.id,
                        action_type=ModActionType.AUTO_WARN,
                        reason=reason,
                        is_automated=True,
                    )
                    await self.mod_service.logger_service.log_action(
                        session, guild, mod_action, target, bot_user
                    )

                    if action.message:
                        with contextlib.suppress(discord.Forbidden):
                            await target.send(f"⚠️ **Warning in {guild.name}**: {action.message}")

                elif action.type == AutoModAction.TIMEOUT:
                    duration = timedelta(seconds=action.duration_seconds or 3600)
                    await self.mod_service.timeout_member(
                        session, guild, target, bot_user, duration, reason, is_automated=True
                    )

                elif action.type == AutoModAction.KICK:
                    await self.mod_service.kick_member(
                        session, guild, target, bot_user, reason, is_automated=True
                    )

                elif action.type == AutoModAction.BAN:
                    await self.mod_service.ban_member(
                        session, guild, target, bot_user, reason, is_automated=True
                    )

                elif action.type == AutoModAction.SOFTBAN:
                    await self.mod_service.softban_member(session, guild, target, bot_user, reason)

                elif action.type == AutoModAction.LOCK_CHANNEL:
                    if isinstance(message.channel, (discord.TextChannel, discord.VoiceChannel)):
                        await self.mod_service.lock_channel(
                            session, message.channel, bot_user, reason
                        )

                elif action.type == AutoModAction.SLOWMODE:
                    if isinstance(
                        message.channel, (discord.TextChannel, discord.VoiceChannel, discord.Thread)
                    ):
                        await self.mod_service.set_slowmode(
                            session,
                            message.channel,
                            bot_user,
                            action.duration_seconds or 10,
                            reason,
                        )

                elif action.type == AutoModAction.DM_USER:
                    with contextlib.suppress(discord.Forbidden):
                        await target.send(action.message or f"You violated a rule in {guild.name}.")

                elif action.type == AutoModAction.NOTIFY_STAFF:
                    # This relies on the LoggingService to send a specialized alert
                    # For now, we'll log it as a standard note
                    mod_action = await MemberRepository.log_action(
                        session=session,
                        guild_id=guild.id,
                        user_id=target.id,
                        moderator_id=bot_user.id,
                        action_type=ModActionType.NOTE,
                        reason=f"STAFF ALERT: {reason}",
                        is_automated=True,
                    )
                    await self.mod_service.logger_service.log_action(
                        session, guild, mod_action, target, bot_user
                    )

            except Exception as e:
                logger.error(
                    "automod_action_failed", action=action.type, user_id=target.id, error=str(e)
                )
