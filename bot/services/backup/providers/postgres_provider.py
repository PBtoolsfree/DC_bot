"""PostgreSQL Storage Provider for Backups."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.backup import ServerBackup
from bot.services.backup.providers.base import BackupStorageProvider


class PostgresStorageProvider(BackupStorageProvider):
    """Stores the backup payload directly in the PostgreSQL JSON column."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_backup(self, backup_id: int, payload: dict) -> str:
        """The payload is already stored in the ServerBackup.payload column. We just return a pg URI."""
        return f"pg://server_backups/{backup_id}"

    async def load_backup(self, identifier: str) -> dict:
        """Loads from the ServerBackup table."""
        backup_id = int(identifier.split("/")[-1])
        stmt = select(ServerBackup).where(ServerBackup.id == backup_id)
        result = await self.session.execute(stmt)
        backup = result.scalar_one_or_none()

        if not backup:
            raise ValueError(f"Backup {backup_id} not found.")

        return backup.payload
