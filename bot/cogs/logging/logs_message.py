"""Listeners for message-related events."""

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


class MessageLogsCog(commands.Cog):
    """Handles logging for message deletions, edits, and pins."""

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
    async def on_message_delete(self, message: discord.Message) -> None:
        if not message.guild or message.author.bot:
            return

        settings = await self._get_settings(message.guild.id)
        if not settings:
            return

        # Attempt to find who deleted it (could be the author themselves, or a mod)
        executor = message.author
        audit_user = await self.audit_service.get_executor_for_action(
            message.guild, discord.AuditLogAction.message_delete, message.author.id, 5
        )
        if audit_user:
            executor = audit_user

        embed = EmbedBuilder.log(
            action="Message Deleted",
            target=message.author,
            executor=executor,
            channel=message.channel,
            color=discord.Color.red(),
        )

        content = message.content or "[No Content]"
        if len(content) > 1024:
            content = content[:1021] + "..."

        embed.add_field(name="Content", value=content, inline=False)

        if message.attachments:
            urls = "\n".join([att.url for att in message.attachments])
            embed.add_field(name="Attachments", value=urls[:1024], inline=False)

        async with self.bot.db.session() as session:
            await self.logging_service.emit_log(
                session=session,
                guild=message.guild,
                settings=settings,
                action_type="message_delete",
                severity=1,
                executor=executor,
                target_id=message.id,
                channel=message.channel,
                before={
                    "content": message.content,
                    "attachments": [a.url for a in message.attachments],
                },
                embed=embed,
            )

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        if not before.guild or before.author.bot or before.content == after.content:
            return

        settings = await self._get_settings(before.guild.id)
        if not settings:
            return

        embed = EmbedBuilder.log(
            action="Message Edited",
            target=before.author,
            executor=before.author,
            channel=before.channel,
            color=discord.Color.orange(),
        )

        b_content = before.content or "[No Content]"
        a_content = after.content or "[No Content]"

        embed.add_field(name="Before", value=b_content[:1024], inline=False)
        embed.add_field(name="After", value=a_content[:1024], inline=False)
        embed.add_field(
            name="Jump To Message", value=f"[Click Here]({after.jump_url})", inline=False
        )

        async with self.bot.db.session() as session:
            await self.logging_service.emit_log(
                session=session,
                guild=before.guild,
                settings=settings,
                action_type="message_edit",
                severity=1,
                executor=before.author,
                target_id=before.id,
                channel=before.channel,
                before={"content": before.content},
                after={"content": after.content},
                metadata={"jump_url": after.jump_url},
                embed=embed,
            )
