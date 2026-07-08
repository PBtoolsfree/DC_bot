"""Verification Repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models.verification import VerificationSettings


class VerificationRepository:
    """Handles database persistence for the Verification system."""

    @staticmethod
    async def get_settings(session: AsyncSession, guild_id: int) -> VerificationSettings | None:
        """Fetch verification settings for a guild."""
        stmt = select(VerificationSettings).where(VerificationSettings.guild_id == guild_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def upsert_settings(
        session: AsyncSession, 
        guild_id: int, 
        **kwargs
    ) -> VerificationSettings:
        """Update or create verification settings."""
        settings = await VerificationRepository.get_settings(session, guild_id)
        if not settings:
            settings = VerificationSettings(guild_id=guild_id)
            session.add(settings)
            
        for key, value in kwargs.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
                
        await session.flush()
        return settings
