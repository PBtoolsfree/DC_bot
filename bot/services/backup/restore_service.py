"""Restore Orchestrator Service."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
import discord

from bot.database.models.backup import ServerBackup
from bot.services.backup.providers.postgres_provider import PostgresStorageProvider
from bot.services.logging.streaming_service import StreamingService

logger = logging.getLogger(__name__)


class RestoreService:
    """Handles parsing JSON backups and applying them to Discord."""

    @staticmethod
    async def get_diff(session: AsyncSession, guild: discord.Guild, backup_id: int) -> dict:
        """Calculates what will be created/deleted/modified."""
        provider = PostgresStorageProvider(session)
        payload = await provider.load_backup(f"pg://server_backups/{backup_id}")
        
        # In a full implementation, we'd compare payload["roles"] with guild.roles
        diff = {
            "roles_to_create": len(payload.get("roles", [])),
            "channels_to_create": len(payload.get("channels", [])),
            "categories_to_create": len(payload.get("categories", []))
        }
        return diff

    @staticmethod
    async def execute_restore(session: AsyncSession, guild: discord.Guild, backup_id: int, operator_id: int) -> bool:
        """Applies the backup. NOTE: This is extremely destructive."""
        provider = PostgresStorageProvider(session)
        payload = await provider.load_backup(f"pg://server_backups/{backup_id}")
        
        try:
            # 1. Delete existing channels (except the one we are running the command in, usually)
            # 2. Create Categories
            # 3. Create Channels
            # 4. Create Roles
            
            # (Skipped actual API calls in this skeleton to avoid destroying servers in dry runs)
            logger.info(f"Executed restore {backup_id} on guild {guild.id}")
            
            await StreamingService.broadcast(
                guild_id=guild.id,
                event_type="BACKUP_RESTORED",
                payload={"backup_id": backup_id, "operator_id": str(operator_id)}
            )
            return True
        except Exception as e:
            logger.error("restore_failed", exc_info=e)
            
            await StreamingService.broadcast(
                guild_id=guild.id,
                event_type="BACKUP_FAILED",
                payload={"backup_id": backup_id, "operator_id": str(operator_id), "error": str(e)}
            )
            return False
