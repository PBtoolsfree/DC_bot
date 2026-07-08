"""Listeners for advanced/complex events (Threads, Webhooks, etc)."""

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


class AdvancedLogsCog(commands.Cog):
    """Handles logging for threads, webhooks, and invites."""

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
    async def on_thread_create(self, thread: discord.Thread) -> None:
        settings = await self._get_settings(thread.guild.id)
        if not settings:
            return

        embed = EmbedBuilder.log(
            action="Thread Created",
            executor=thread.owner,
            channel=thread.parent,
            color=discord.Color.green(),
        )
        embed.add_field(name="Name", value=thread.name, inline=True)

        async with self.bot.db.session() as session:
            await self.logging_service.emit_log(
                session=session,
                guild=thread.guild,
                settings=settings,
                action_type="thread_create",
                severity=1,
                executor=thread.owner,
                target_id=thread.id,
                channel=thread.parent,
                after={"name": thread.name},
                embed=embed,
            )
