"""Voice XP Provider."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.xp import UserXP, XPSettings
from bot.services.xp.providers.base import XPProvider


class VoiceXPProvider(XPProvider):
    """Calculates XP for spending time in voice channels."""

    async def process_event(self, session: AsyncSession, event_data: dict) -> int:
        """Processes a voice commit payload."""
        guild_id = event_data["guild_id"]
        user_id = event_data["user_id"]
        minutes = event_data["minutes"]

        if minutes <= 0:
            return 0

        # Check settings
        stmt = select(XPSettings).where(XPSettings.guild_id == guild_id)
        result = await session.execute(stmt)
        settings = result.scalar_one_or_none()

        if not settings or not settings.enabled:
            return 0

        xp_amount = settings.voice_xp_per_minute * minutes

        # Update UserXP
        stmt2 = select(UserXP).where(UserXP.guild_id == guild_id, UserXP.user_id == user_id)
        result2 = await session.execute(stmt2)
        user_xp = result2.scalar_one_or_none()

        if not user_xp:
            user_xp = UserXP(guild_id=guild_id, user_id=user_id)
            session.add(user_xp)

        user_xp.xp += xp_amount
        user_xp.voice_minutes += minutes

        return xp_amount
