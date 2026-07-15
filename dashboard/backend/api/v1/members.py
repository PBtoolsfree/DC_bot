"""API endpoints for Dashboard Members (RBAC)."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.dashboard import DashboardMember
from dashboard.backend.core.database import get_db
from dashboard.backend.core.security import get_current_user
from dashboard.backend.services.rbac_service import RBACService
from dashboard.shared.permissions.enums import DashboardRole

router = APIRouter()


@router.get("/{guild_id}/members")
async def list_members(
    guild_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List all users who have explicit dashboard access to this guild."""
    # 1. Verify caller has permission to view members
    is_admin = await RBACService.has_permission(
        session,
        guild_id,
        current_user["id"],
        "manage_dashboard_roles",
        discord_access_token=current_user.get("access_token"),
    )
    if not is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")

    stmt = select(DashboardMember).where(DashboardMember.guild_id == guild_id)
    result = await session.execute(stmt)
    members = result.scalars().all()

    return [
        {
            "id": m.id,
            "discord_user_id": str(m.discord_user_id),
            "role": m.role,
            "permissions": m.permissions,
        }
        for m in members
    ]


@router.post("/{guild_id}/members")
async def add_member(
    guild_id: int,
    discord_user_id: str,
    role: DashboardRole,
    permissions: dict[str, bool] | None = None,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Grant dashboard access to a Discord user."""
    is_admin = await RBACService.has_permission(
        session,
        guild_id,
        current_user["id"],
        "manage_dashboard_roles",
        discord_access_token=current_user.get("access_token"),
    )
    if not is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        user_id_int = int(discord_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid discord_user_id") from None

    # Check if exists
    existing = await RBACService.get_member_role(session, guild_id, user_id_int)
    if existing:
        existing.role = role
        if role == DashboardRole.CUSTOM and permissions:
            existing.permissions = permissions
    else:
        member = DashboardMember(
            guild_id=guild_id,
            discord_user_id=user_id_int,
            role=role,
            permissions=permissions or {},
            created_by=current_user["id"],
        )
        session.add(member)

    await session.commit()
    return {"status": "success"}
