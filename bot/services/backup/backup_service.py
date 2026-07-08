"""Backup Orchestrator Service."""

import logging

import discord
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.backup import ServerBackup
from bot.services.backup.providers.postgres_provider import PostgresStorageProvider
from bot.services.logging.streaming_service import StreamingService

logger = logging.getLogger(__name__)


class BackupService:
    """Handles creating JSON snapshots of the guild state."""

    @staticmethod
    async def create_backup(
        session: AsyncSession,
        guild: discord.Guild,
        creator_id: int,
        name: str,
        description: str | None = None,
    ) -> ServerBackup:
        """Serializes roles, channels, and categories."""

        payload = {
            "roles": [
                {
                    "id": r.id,
                    "name": r.name,
                    "color": r.color.value,
                    "permissions": r.permissions.value,
                    "position": r.position,
                }
                for r in guild.roles
                if not r.is_default() and not r.managed
            ],
            "categories": [
                {"id": c.id, "name": c.name, "position": c.position} for c in guild.categories
            ],
            "channels": [
                {
                    "id": c.id,
                    "name": c.name,
                    "type": str(c.type),
                    "category_id": c.category_id,
                    "position": c.position,
                }
                for c in guild.channels
            ],
        }

        backup = ServerBackup(
            guild_id=guild.id,
            creator_id=creator_id,
            name=name,
            description=description,
            payload=payload,
        )
        session.add(backup)
        await session.flush()

        # In production, we might also hand this to S3 via a provider,
        # but here we just use Postgres.
        provider = PostgresStorageProvider(session)
        await provider.save_backup(backup.id, payload)

        await StreamingService.broadcast(
            guild_id=guild.id,
            event_type="BACKUP_CREATED",
            payload={"backup_id": backup.id, "creator_id": str(creator_id)},
        )

        return backup
