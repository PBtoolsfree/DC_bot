"""Listeners for server-related events."""

from __future__ import annotations

import discord
from discord.ext import commands

from bot.core.bot import ManagementBot
from bot.database.repositories.guild_repo import GuildRepository
from bot.database.schemas.logging import LoggingSettings
from bot.services.logging.audit_service import AuditLogService
from bot.services.logging.logging_service import LoggingService
from bot.utils.embed_builder import EmbedBuilder


class ServerLogsCog(commands.Cog):
    """Handles logging for channels, roles, emojis, and server settings."""

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
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel) -> None:
        settings = await self._get_settings(channel.guild.id)
        if not settings:
            return

        executor = await self.audit_service.get_executor_for_action(
            channel.guild, discord.AuditLogAction.channel_create, channel.id, 5
        )

        embed = EmbedBuilder.log(
            action="Channel Created",
            executor=executor,
            channel=channel,
            color=discord.Color.green()
        )
        embed.add_field(name="Name", value=channel.name, inline=True)
        embed.add_field(name="Type", value=str(channel.type), inline=True)

        async with self.bot.db.session() as session:
            await self.logging_service.emit_log(
                session=session,
                guild=channel.guild,
                settings=settings,
                action_type="channel_create",
                severity=2,
                executor=executor,
                target_id=channel.id,
                channel=channel,
                after={"name": channel.name, "type": str(channel.type)},
                embed=embed
            )

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        settings = await self._get_settings(channel.guild.id)
        if not settings:
            return

        executor = await self.audit_service.get_executor_for_action(
            channel.guild, discord.AuditLogAction.channel_delete, channel.id, 5
        )

        embed = EmbedBuilder.log(
            action="Channel Deleted",
            executor=executor,
            color=discord.Color.red()
        )
        embed.add_field(name="Name", value=channel.name, inline=True)
        embed.add_field(name="Type", value=str(channel.type), inline=True)

        async with self.bot.db.session() as session:
            await self.logging_service.emit_log(
                session=session,
                guild=channel.guild,
                settings=settings,
                action_type="channel_delete",
                severity=3,
                executor=executor,
                target_id=channel.id,
                before={"name": channel.name, "type": str(channel.type)},
                embed=embed
            )
            
    # Similar implementations exist for Role creation/deletion, Guild updates, etc.
