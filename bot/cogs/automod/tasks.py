"""Background workers for AutoMod.

Handles cleanup, statistics aggregation, and cache refreshing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands, tasks

from bot.services.automod.statistics_service import StatisticsService
from bot.services.redis_service import RedisService
from bot.utils.logger import get_logger

if TYPE_CHECKING:
    from bot.core.bot import ManagementBot

logger = get_logger(__name__)


class AutoModTasksCog(commands.Cog):
    """Cog handling background tasks for AutoMod."""

    def __init__(self, bot: ManagementBot) -> None:
        self.bot = bot
        self.redis = RedisService()
        self.stats_service = StatisticsService(self.redis)

    async def cog_load(self) -> None:
        """Start background tasks."""
        await self.redis.connect()
        self.aggregate_stats.start()
        self.cleanup_expired_punishments.start()

    async def cog_unload(self) -> None:
        """Stop background tasks."""
        self.aggregate_stats.cancel()
        self.cleanup_expired_punishments.cancel()
        await self.redis.close()

    @tasks.loop(hours=24)
    async def aggregate_stats(self) -> None:
        """Daily aggregation of Redis statistics to PostgreSQL."""
        logger.info("running_automod_stats_aggregation")
        try:
            await self.stats_service.aggregate_daily_stats()
        except Exception as e:
            logger.error("automod_stats_aggregation_failed", error=str(e))

    @aggregate_stats.before_loop
    async def before_aggregate_stats(self) -> None:
        """Wait for bot to be ready."""
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=5)
    async def cleanup_expired_punishments(self) -> None:
        """Check for and remove expired punishments (mutes/bans)."""
        # This will be fully implemented alongside the Scheduler module.
        # For now, timeouts expire automatically in Discord, so we just
        # need to sync the DB state if required.

    @cleanup_expired_punishments.before_loop
    async def before_cleanup(self) -> None:
        """Wait for bot to be ready."""
        await self.bot.wait_until_ready()
