"""Service for managing Hybrid Dashboard RBAC."""

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.dashboard import DashboardMember
from bot.utils.logger import get_logger
from dashboard.shared.permissions.enums import DashboardRole

logger = get_logger(__name__)


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
    async def _check_discord_guild_permissions(
        discord_access_token: str, guild_id: int
    ) -> dict | None:
        """Check user's Discord permissions for a guild via the Discord API.

        Returns the guild dict if the user has admin/manage_server/owner perms,
        otherwise returns None.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    "https://discord.com/api/v10/users/@me/guilds",
                    headers={"Authorization": f"Bearer {discord_access_token}"},
                )
                if res.status_code != 200:
                    logger.warning(
                        "rbac.discord_api_failed",
                        status_code=res.status_code,
                    )
                    return None

                guilds = res.json()
                for g in guilds:
                    if str(g["id"]) == str(guild_id):
                        perms = int(g.get("permissions", "0"))
                        is_owner = g.get("owner", False)
                        has_admin = (perms & 0x8) == 0x8
                        has_manage_server = (perms & 0x20) == 0x20

                        if is_owner or has_admin or has_manage_server:
                            return g
                        return None

                return None
        except Exception as e:
            logger.error("rbac.discord_check_error", error=str(e))
            return None

    @staticmethod
    async def _auto_provision_member(
        session: AsyncSession,
        guild_id: int,
        discord_user_id: int,
        guild_data: dict,
    ) -> DashboardMember:
        """Auto-create a DashboardMember record for a guild owner/admin.

        This is called when a user with Discord guild admin permissions
        accesses the dashboard but doesn't have an explicit DashboardMember
        record yet.
        """
        is_owner = guild_data.get("owner", False)
        role = DashboardRole.OWNER if is_owner else DashboardRole.ADMIN

        member = DashboardMember(
            guild_id=guild_id,
            discord_user_id=discord_user_id,
            role=role,
            permissions={},
            created_by=discord_user_id,
        )
        session.add(member)
        await session.commit()
        await session.refresh(member)

        logger.info(
            "rbac.auto_provisioned",
            guild_id=guild_id,
            user_id=discord_user_id,
            role=role,
        )

        return member

    @staticmethod
    async def has_permission(
        session: AsyncSession,
        guild_id: int,
        discord_user_id: int,
        permission_name: str,
        discord_access_token: str | None = None,
    ) -> bool:
        """Check if a user has a specific granular permission for a guild.

        If no DashboardMember record exists, this will attempt to verify
        the user's Discord guild permissions and auto-provision them.
        """
        member = await RBACService.get_member_role(session, guild_id, discord_user_id)

        # If no explicit dashboard member record, try Discord API fallback
        if not member and discord_access_token:
            guild_data = await RBACService._check_discord_guild_permissions(
                discord_access_token, guild_id
            )
            if guild_data:
                member = await RBACService._auto_provision_member(
                    session, guild_id, discord_user_id, guild_data
                )

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
