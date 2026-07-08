"""Message XP Provider."""

import random
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.xp import UserXP, XPSettings
from bot.services.xp.providers.base import XPProvider


class MessageXPProvider(XPProvider):
    """Calculates XP for sending text messages."""

    # Mock Redis cooldown cache
    _cooldowns: dict[str, float] = {}

    async def process_event(self, session: AsyncSession, event_data: dict) -> int:
        """Processes a discord.Message event payload."""
        guild_id = event_data["guild_id"]
        user_id = event_data["user_id"]
        channel_id = event_data["channel_id"]

        # Check settings
        stmt = select(XPSettings).where(XPSettings.guild_id == guild_id)
        result = await session.execute(stmt)
        settings = result.scalar_one_or_none()

        if not settings or not settings.enabled:
            return 0

        if channel_id in settings.ignored_channels:
            return 0

        # Check cooldown
        cache_key = f"xp_{guild_id}_{user_id}"
        last_xp_time = self._cooldowns.get(cache_key, 0)

        now = time.time()
        if now - last_xp_time < settings.message_cooldown_sec:
            return 0  # Still on cooldown

        # Grant XP
        xp_amount = random.randint(settings.message_xp_min, settings.message_xp_max)
        self._cooldowns[cache_key] = now

        # Update UserXP
        stmt2 = select(UserXP).where(UserXP.guild_id == guild_id, UserXP.user_id == user_id)
        result2 = await session.execute(stmt2)
        user_xp = result2.scalar_one_or_none()

        if not user_xp:
            user_xp = UserXP(guild_id=guild_id, user_id=user_id)
            session.add(user_xp)

        user_xp.xp += xp_amount
        user_xp.messages_sent += 1

        return xp_amount
