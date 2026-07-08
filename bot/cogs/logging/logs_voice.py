"""Listeners for voice-related events."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from bot.database.repositories.guild_repo import GuildRepository
from bot.database.schemas.logging import LoggingSettings
from bot.services.logging.audit_service import AuditLogService
from bot.services.logging.logging_service import LoggingService
from bot.utils.embed_builder import EmbedBuilder

if TYPE_CHECKING:
    from bot.core.bot import ManagementBot


class VoiceLogsCog(commands.Cog):
    """Handles logging for voice states (joins, leaves, moves, mutes)."""

    def __init__(self, bot: ManagementBot) -> None:
        self.bot = bot
        self.logging_service = LoggingService(bot)
        self.audit_service = AuditLogService()

    async def _get_settings(self, guild_id: int) -> LoggingSettings | None:
        async with self.bot.db.session() as session:
            db_settings = await GuildRepository.get_module_settings(session, guild_id, "logging")
            if not db_settings or not db_settings.enabled:
                return None
            return LoggingSettings.from_dict(db_settings.config)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ) -> None:
        settings = await self._get_settings(member.guild.id)
        if not settings:
            return

        # Voice Join
        if not before.channel and after.channel:
            embed = EmbedBuilder.log(
                action="Voice Joined",
                target=member,
                channel=after.channel,
                color=discord.Color.green(),
            )
            async with self.bot.db.session() as session:
                await self.logging_service.emit_log(
                    session=session,
                    guild=member.guild,
                    settings=settings,
                    action_type="voice_join",
                    severity=1,
                    executor=member,
                    target_id=member.id,
                    channel=after.channel,
                    after={"channel": after.channel.id},
                    embed=embed,
                )

        # Voice Leave
        elif before.channel and not after.channel:
            embed = EmbedBuilder.log(
                action="Voice Left",
                target=member,
                channel=before.channel,
                color=discord.Color.dark_grey(),
            )
            async with self.bot.db.session() as session:
                await self.logging_service.emit_log(
                    session=session,
                    guild=member.guild,
                    settings=settings,
                    action_type="voice_leave",
                    severity=1,
                    executor=member,
                    target_id=member.id,
                    channel=before.channel,
                    before={"channel": before.channel.id},
                    embed=embed,
                )

        # Voice Move
        elif before.channel and after.channel and before.channel != after.channel:
            embed = EmbedBuilder.log(
                action="Voice Moved", target=member, color=discord.Color.blue()
            )
            embed.add_field(name="From", value=before.channel.mention, inline=True)
            embed.add_field(name="To", value=after.channel.mention, inline=True)

            async with self.bot.db.session() as session:
                await self.logging_service.emit_log(
                    session=session,
                    guild=member.guild,
                    settings=settings,
                    action_type="voice_move",
                    severity=1,
                    executor=member,
                    target_id=member.id,
                    channel=after.channel,
                    before={"channel": before.channel.id},
                    after={"channel": after.channel.id},
                    embed=embed,
                )
