"""Service for managing Hybrid Dashboard RBAC."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.dashboard import DashboardMember
from dashboard.shared.permissions.enums import DashboardRole


class RBACService:
    """Manages permissions and access rights for dashboard members."""

    @staticmethod
    async def get_member_role(
        session: AsyncSession, guild_id: int, discord_user_id: int
    ) -> DashboardMember | None:
        """Fetch the explicit dashboard role for a user in a specific guild."""
        stmt = select(DashboardMember).where(
            DashboardMember.guild_id == guild_id, DashboardMember.discord_user_id == discord_user_id
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def has_permission(
        session: AsyncSession, guild_id: int, discord_user_id: int, permission_name: str
    ) -> bool:
        """Check if a user has a specific granular permission for a guild."""
        member = await RBACService.get_member_role(session, guild_id, discord_user_id)
        if not member:
            return False

        if member.role in (DashboardRole.OWNER, DashboardRole.ADMIN):
            return True

        if member.role == DashboardRole.CUSTOM:
            return member.permissions.get(permission_name, False)

        # Hardcoded defaults for standard roles
        if member.role == DashboardRole.MODERATOR:
            return permission_name in [
                "manage_moderation",
                "manage_automod",
                "manage_logs",
                "view_analytics",
                "manage_tickets",
            ]

        if member.role == DashboardRole.VIEWER:
            return permission_name in ["view_analytics"]

        return False
