"""Discord event listeners for AutoMod.

Listens to on_message, on_message_edit, and on_member_join events
and dispatches them to the AutoModerationService.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

from bot.services.automod.automod_service import AutoModerationService
from bot.services.redis_service import RedisService
from bot.utils.logger import get_logger

if TYPE_CHECKING:
    import discord

    from bot.core.bot import ManagementBot

logger = get_logger(__name__)


class AutoModListenerCog(commands.Cog):
    """Cog handling event listening for AutoMod."""

    def __init__(self, bot: ManagementBot) -> None:
        self.bot = bot
        # In a real DI setup, redis would be injected
        # We instantiate a local redis wrapper that shares connection state
        self.redis = RedisService()
        self.automod_service = AutoModerationService(bot, self.redis)

    async def cog_load(self) -> None:
        """Connect to Redis when the cog is loaded."""
        await self.redis.connect()

    async def cog_unload(self) -> None:
        """Close Redis connection when unloaded."""
        await self.redis.close()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Process incoming messages for spam, profanity, and links."""
        if message.author.bot or not message.guild:
            return

        # Bot admins bypass all automod logic to prevent accidental locks
        if message.author.id in self.bot.settings.bot_owner_ids:
            return

        async with self.bot.db.session() as session:
            # We don't await the result if we just want it to drop
            # but we need to ensure the message wasn't flagged before executing command
            await self.automod_service.process_message(session, message)

            # If the message was deleted or blocked by automod, we should technically
            # stop processing commands for it (though discord.py processes commands separately).
            # Usually handled by a global check, but discord.py's flow doesn't easily stop
            # on_message from triggering commands unless we override process_commands.

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        """Process edited messages for profanity and links."""
        if after.author.bot or not after.guild:
            return

        if after.author.id in self.bot.settings.bot_owner_ids:
            return

        if before.content == after.content:
            return

        async with self.bot.db.session() as session:
            await self.automod_service.process_message(session, after)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Process member joins for username filters (future expansion)."""
        # Module 3 specifically mentions Username Filters
        # This can be implemented in ProfanityService and triggered here.
