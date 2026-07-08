"""Audit log monitoring service."""

from __future__ import annotations

from typing import TYPE_CHECKING
import asyncio

import discord

from bot.utils.logger import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


class AuditService:
    """Monitors and retrieves audit log entries for incidents."""

    def __init__(self) -> None:
        # Cache of recently processed audit logs to prevent duplicate processing
        self._processed_logs: set[int] = set()
        self._lock = asyncio.Lock()

    async def find_recent_action(
        self,
        guild: discord.Guild,
        action: discord.AuditLogAction,
        target_id: int | None = None,
        limit: int = 5,
        time_window_seconds: int = 15,
    ) -> discord.AuditLogEntry | None:
        """Find the most recent audit log entry for a specific action and target."""
        if not guild.me.guild_permissions.view_audit_log:
            return None

        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)

        try:
            async for entry in guild.audit_logs(action=action, limit=limit):
                if target_id and getattr(entry.target, "id", None) != target_id:
                    continue
                    
                # Ensure the log is recent
                time_diff = (now - entry.created_at).total_seconds()
                if time_diff > time_window_seconds:
                    continue

                async with self._lock:
                    if entry.id in self._processed_logs:
                        continue
                    self._processed_logs.add(entry.id)

                return entry
        except discord.Forbidden:
            logger.warning("audit_service.forbidden", guild_id=guild.id)
        except discord.HTTPException as e:
            logger.error("audit_service.http_error", error=str(e), guild_id=guild.id)
            
        return None

    async def clear_cache(self) -> None:
        """Clear the processed logs cache to prevent memory leaks."""
        async with self._lock:
            self._processed_logs.clear()
