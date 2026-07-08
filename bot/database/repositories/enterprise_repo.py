"""Repositories for Modules 9-12."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.backup import ServerBackup
from bot.database.models.welcome import WelcomeSettings
from bot.database.models.xp import UserXP, XPSettings


class EnterpriseRepository:
    """Consolidated repo fetching for Modules 9-12."""

    @staticmethod
    async def get_backup(session: AsyncSession, backup_id: int) -> ServerBackup | None:
        stmt = select(ServerBackup).where(ServerBackup.id == backup_id)
        return (await session.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def get_welcome_settings(session: AsyncSession, guild_id: int) -> WelcomeSettings | None:
        stmt = select(WelcomeSettings).where(WelcomeSettings.guild_id == guild_id)
        return (await session.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def get_xp_settings(session: AsyncSession, guild_id: int) -> XPSettings | None:
        stmt = select(XPSettings).where(XPSettings.guild_id == guild_id)
        return (await session.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def get_top_xp(session: AsyncSession, guild_id: int, limit: int = 10) -> list[UserXP]:
        stmt = (
            select(UserXP)
            .where(UserXP.guild_id == guild_id)
            .order_by(UserXP.xp.desc())
            .limit(limit)
        )
        return list((await session.execute(stmt)).scalars().all())
