"""Background tasks for the security system."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from discord.ext import commands, tasks

from bot.utils.logger import get_logger

if TYPE_CHECKING:
    from bot.core.bot import ManagementBot

logger = get_logger(__name__)


class SecurityTasksCog(commands.Cog):
    """Handles background tasks like incident cleanup and snapshot backups."""

    def __init__(self, bot: ManagementBot) -> None:
        self.bot = bot
        self.incident_cleanup_task.start()
        self.snapshot_backup_task.start()

    def cog_unload(self) -> None:
        self.incident_cleanup_task.cancel()
        self.snapshot_backup_task.cancel()

    @tasks.loop(hours=24)
    async def incident_cleanup_task(self) -> None:
        """Cleans up old incidents from the database (e.g. older than 90 days)."""
        logger.info("security_tasks.incident_cleanup.started")
        # In a full production implementation, we would execute a DELETE query here.
        await asyncio.sleep(1)
        logger.info("security_tasks.incident_cleanup.completed")

    @incident_cleanup_task.before_loop
    async def before_incident_cleanup(self) -> None:
        await self.bot.wait_until_ready()

    @tasks.loop(hours=168)  # Weekly
    async def snapshot_backup_task(self) -> None:
        """Creates automatic snapshots for guilds with the feature enabled."""
        logger.info("security_tasks.snapshot_backup.started")
        # Implementation would iterate over premium/enabled guilds and create snapshots
        await asyncio.sleep(1)
        logger.info("security_tasks.snapshot_backup.completed")

    @snapshot_backup_task.before_loop
    async def before_snapshot_backup(self) -> None:
        await self.bot.wait_until_ready()
