"""Background tasks for the Logging system."""

from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands, tasks

from bot.services.logging.retention_service import RetentionService
from bot.utils.logger import get_logger

if TYPE_CHECKING:
    from bot.core.bot import ManagementBot

logger = get_logger(__name__)


class LoggingTasksCog(commands.Cog):
    """Handles background tasks like log retention cleanup."""

    def __init__(self, bot: ManagementBot) -> None:
        self.bot = bot
        self.log_cleanup_task.start()

    def cog_unload(self) -> None:
        self.log_cleanup_task.cancel()

    @tasks.loop(hours=24)
    async def log_cleanup_task(self) -> None:
        """Cleans up logs older than the guild's retention policy."""
        logger.info("logging_tasks.cleanup.started")

        # In a real enterprise system, we would iterate over all guilds or
        # use a global retention policy for the free tier.
        # Here we demonstrate a global 30 day purge for simplicity.

        async with self.bot.db.session() as session:
            await RetentionService.cleanup_expired_logs(session, 30)
            await session.commit()

        logger.info("logging_tasks.cleanup.completed")

    @log_cleanup_task.before_loop
    async def before_cleanup(self) -> None:
        await self.bot.wait_until_ready()
