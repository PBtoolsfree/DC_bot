"""Service for tracking mass actions and detecting raids."""

from __future__ import annotations

import time

from bot.database.schemas.security import AntiNukeRule, AntiRaidRule
from bot.services.redis_service import RedisService


class RaidDetectionService:
    """Tracks action velocity to detect raids and nukes."""

    def __init__(self, redis: RedisService) -> None:
        self.redis = redis

    def _get_key(self, guild_id: int, action_type: str, target_id: int | None = None) -> str:
        """Generate a Redis key for tracking."""
        base = f"security:velocity:{guild_id}:{action_type}"
        if target_id:
            base += f":{target_id}"
        return base

    async def add_action_and_check(
        self,
        guild_id: int,
        action_type: str,
        rule: AntiRaidRule | AntiNukeRule,
        target_id: int | None = None,
    ) -> bool:
        """Add an action to the tracker and return True if it exceeds the threshold.

        Args:
            guild_id: The ID of the guild.
            action_type: The type of action (e.g., 'member_join', 'channel_delete').
            rule: The configuration rule containing threshold and time window.
            target_id: Optional ID of the user performing the action (for Anti-Nuke).

        Returns:
            True if the threshold is exceeded, False otherwise.
        """
        if not rule.enabled or rule.threshold <= 0:
            return False

        key = self._get_key(guild_id, action_type, target_id)
        current_time = int(time.time())
        window_start = current_time - rule.time_window_seconds

        # Remove old entries and add the new one
        await self.redis.zremrangebyscore(key, 0, window_start)

        # Add new action with timestamp as both score and value (or unique ID)
        # Using a slight microsecond offset or just current_time if we don't care about exact uniqueness
        # Actually, ZADD needs unique members. We can use `<timestamp>:<increment>`
        # For simplicity in this implementation, we will use an incrementing counter or random string.
        import uuid

        member_val = f"{current_time}:{uuid.uuid4().hex[:8]}"
        await self.redis.zadd(key, {member_val: current_time})

        # Set expiration so we don't leak memory
        await self.redis.expire(key, rule.time_window_seconds * 2)

        # Count remaining entries
        count = await self.redis.zcard(key)

        return count >= rule.threshold
