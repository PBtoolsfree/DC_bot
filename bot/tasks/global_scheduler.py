"""Unified Global Scheduler Engine."""

import datetime
import logging
from discord.ext import commands, tasks
from sqlalchemy import select

from bot.database.core import db
from bot.database.models.welcome import AutoRoleSettings
from bot.services.xp.voice_service import VoiceSessionService
from bot.services.xp.providers.voice_provider import VoiceXPProvider
from bot.services.backup.backup_service import BackupService

logger = logging.getLogger(__name__)


class GlobalSchedulerTask(commands.Cog):
    """Unified engine for Voice XP, Delayed Roles, Auto Backup, and Cleanups."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.voice_provider = VoiceXPProvider()
        
        self.engine.start()

    def cog_unload(self) -> None:
        self.engine.cancel()

    @tasks.loop(minutes=5)
    async def engine(self) -> None:
        """Runs all sub-routines sequentially to prevent concurrent DB locks."""
        
        try:
            # 1. Voice XP Periodic Commit
            await self._commit_voice_xp()
            
            # 2. Delayed Roles
            await self._process_delayed_roles()
            
            # 3. Nightly Auto Backup Check (runs every 5 mins but only executes if conditions met)
            await self._check_auto_backups()
            
        except Exception as e:
            logger.error("global_scheduler_failed", exc_info=e)

    async def _commit_voice_xp(self) -> None:
        """Commits XP for users still sitting in voice channels."""
        async with db.session() as session:
            for user_id in list(VoiceSessionService._active_sessions.keys()):
                # Get minutes so far
                minutes = await VoiceSessionService.get_active_minutes(user_id)
                if minutes > 0:
                    member = None
                    # Find which guild they are in... (simplified for skeleton)
                    for g in self.bot.guilds:
                        member = g.get_member(user_id)
                        if member and member.voice:
                            break
                            
                    if member:
                        await self.voice_provider.process_event(
                            session, 
                            {"guild_id": member.guild.id, "user_id": user_id, "minutes": minutes}
                        )
                        await session.commit()
                        await VoiceSessionService.reset_session(user_id)

    async def _process_delayed_roles(self) -> None:
        """Check for users who passed their autorole delay period."""
        # A real implementation would query a pending_roles table.
        # This is the architectural hook for it.
        pass

    async def _check_auto_backups(self) -> None:
        """Trigger backups for premium guilds."""
        # Typically checked against a configuration timestamp
        pass

    @engine.before_loop
    async def before_engine(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GlobalSchedulerTask(bot))
