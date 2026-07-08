"""Service for searching logs."""

from __future__ import annotations

import datetime
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.logging import ActionLog
from bot.database.repositories.log_repo import LogRepository


class SearchService:
    """Provides high-level search and timeline features for action logs."""

    @staticmethod
    async def get_timeline(
        session: AsyncSession,
        guild_id: int,
        user_id: int | None = None,
        limit: int = 50
    ) -> Sequence[ActionLog]:
        """Fetch a chronological timeline for a specific user or the whole guild."""
        return await LogRepository.search_logs(
            session=session,
            guild_id=guild_id,
            user_id=user_id,
            limit=limit,
            offset=0
        )

    @staticmethod
    async def search(
        session: AsyncSession,
        guild_id: int,
        action_type: str | None = None,
        user_id: int | None = None,
        channel_id: int | None = None,
        days_ago: int | None = None,
        limit: int = 50,
        page: int = 1
    ) -> Sequence[ActionLog]:
        """Search with pagination and filters."""
        start_date = None
        if days_ago:
            start_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_ago)
            
        offset = (page - 1) * limit
        
        return await LogRepository.search_logs(
            session=session,
            guild_id=guild_id,
            user_id=user_id,
            action_type=action_type,
            channel_id=channel_id,
            start_date=start_date,
            limit=limit,
            offset=offset
        )
