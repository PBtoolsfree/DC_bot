"""Repository for action log data."""

from __future__ import annotations

import datetime
from typing import Any, Sequence

from sqlalchemy import select, desc, or_, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.logging import ActionLog


class LogRepository:
    """Handles database operations for logging models."""

    @staticmethod
    async def create_log(
        session: AsyncSession,
        guild_id: int,
        action_type: str,
        severity: int = 1,
        executor_id: int | None = None,
        target_id: int | None = None,
        channel_id: int | None = None,
        before_data: dict[str, Any] | None = None,
        after_data: dict[str, Any] | None = None,
        metadata_json: dict[str, Any] | None = None,
        correlation_id: str | None = None,
        is_immutable: bool = False,
    ) -> ActionLog:
        """Create a new action log entry."""
        log_entry = ActionLog(
            guild_id=guild_id,
            action_type=action_type,
            severity=severity,
            executor_id=executor_id,
            target_id=target_id,
            channel_id=channel_id,
            before_data=before_data,
            after_data=after_data,
            metadata_json=metadata_json or {},
            correlation_id=correlation_id,
            is_immutable=is_immutable,
        )
        session.add(log_entry)
        await session.flush()
        return log_entry

    @staticmethod
    async def search_logs(
        session: AsyncSession,
        guild_id: int,
        user_id: int | None = None,
        action_type: str | None = None,
        channel_id: int | None = None,
        start_date: datetime.datetime | None = None,
        end_date: datetime.datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[ActionLog]:
        """Search and paginate logs based on criteria."""
        stmt = select(ActionLog).where(ActionLog.guild_id == guild_id)

        if user_id:
            stmt = stmt.where(
                or_(
                    ActionLog.executor_id == user_id,
                    ActionLog.target_id == user_id
                )
            )
            
        if action_type:
            stmt = stmt.where(ActionLog.action_type == action_type)
            
        if channel_id:
            stmt = stmt.where(ActionLog.channel_id == channel_id)
            
        if start_date:
            stmt = stmt.where(ActionLog.created_at >= start_date)
            
        if end_date:
            stmt = stmt.where(ActionLog.created_at <= end_date)

        stmt = stmt.order_by(desc(ActionLog.created_at)).limit(limit).offset(offset)
        result = await session.execute(stmt)
        return result.scalars().all()
        
    @staticmethod
    async def cleanup_old_logs(
        session: AsyncSession,
        retention_days: int
    ) -> int:
        """Delete logs older than the retention period, ignoring immutable logs.
        Returns the number of deleted rows.
        """
        cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=retention_days)
        
        stmt = delete(ActionLog).where(
            ActionLog.created_at < cutoff_date,
            ActionLog.is_immutable == False
        )
        
        result = await session.execute(stmt)
        return result.rowcount
