"""Service for polling and caching Discord Audit Logs."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import discord

from bot.utils.logger import get_logger

logger = get_logger(__name__)


class AuditLogService:
    """Monitors and retrieves audit log entries to attribute actions."""

    def __init__(self) -> None:
        self._processed_logs: set[int] = set()
        self._lock = asyncio.Lock()

    async def get_executor_for_action(
        self,
        guild: discord.Guild,
        action: discord.AuditLogAction,
        target_id: int | None = None,
        time_window_seconds: int = 15,
    ) -> discord.Member | discord.User | None:
        """Find the user who performed an action by polling the audit log."""
        if not guild.me.guild_permissions.view_audit_log:
            return None

        now = datetime.now(timezone.utc)

        try:
            async for entry in guild.audit_logs(action=action, limit=10):
                if target_id and getattr(entry.target, "id", None) != target_id:
                    continue
                    
                time_diff = (now - entry.created_at).total_seconds()
                if time_diff > time_window_seconds:
                    continue

                async with self._lock:
                    if entry.id in self._processed_logs:
                        continue
                    self._processed_logs.add(entry.id)

                return entry.user
        except discord.Forbidden:
            pass
        except discord.HTTPException as e:
            logger.error("audit_log.http_error", error=str(e), guild_id=guild.id)
            
        return None

    async def clear_cache(self) -> None:
        """Clear the processed logs cache to prevent memory leaks."""
        async with self._lock:
            self._processed_logs.clear()
