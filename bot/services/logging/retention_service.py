"""Service for log retention and cleanup."""

from __future__ import annotations

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.repositories.log_repo import LogRepository
from bot.utils.logger import get_logger

logger = get_logger(__name__)


class RetentionService:
    """Manages the lifecycle and cleanup of audit logs."""

    @staticmethod
    async def cleanup_expired_logs(session: AsyncSession, retention_days: int) -> int:
        """Purge logs older than the retention period.
        
        Returns the number of logs purged.
        """
        try:
            # We defer to the repository which executes a DELETE WHERE created_at < cutoff
            deleted_count = await LogRepository.cleanup_old_logs(session, retention_days)
            if deleted_count > 0:
                logger.info("logging.retention.purged", count=deleted_count)
            return deleted_count
        except Exception as e:
            logger.error("logging.retention.error", error=str(e))
            return 0
