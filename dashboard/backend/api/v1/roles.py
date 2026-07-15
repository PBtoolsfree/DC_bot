"""Reaction Roles APIs."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.roles import ReactionRoleGroup, ReactionRoleItem
from dashboard.backend.core.database import get_db
from dashboard.backend.core.security import get_current_user
from dashboard.backend.services.rbac_service import RBACService
from dashboard.shared.schemas.modules.roles import ReactionRoleGroupSchema, ReactionRoleItemSchema

router = APIRouter()


@router.get("/{guild_id}/groups")
async def list_role_groups(
    guild_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[ReactionRoleGroupSchema]:
    """Fetch all reaction role groups for a guild."""
    has_perm = await RBACService.has_permission(
        session,
        guild_id,
        current_user["id"],
        "manage_roles",
        discord_access_token=current_user.get("access_token"),
    )
    if not has_perm:
        raise HTTPException(status_code=403, detail="Forbidden")

    stmt = select(ReactionRoleGroup).where(ReactionRoleGroup.guild_id == guild_id)
    groups = (await session.execute(stmt)).scalars().all()

    result = []
    for g in groups:
        # Fetch items
        stmt_i = select(ReactionRoleItem).where(ReactionRoleItem.group_id == g.id)
        items = (await session.execute(stmt_i)).scalars().all()

        item_schemas = [
            ReactionRoleItemSchema(id=i.id, role_id=str(i.role_id), emoji=i.emoji, label=i.label)
            for i in items
        ]

        result.append(
            ReactionRoleGroupSchema(
                id=g.id,
                name=g.name,
                min_roles=g.min_roles,
                max_roles=g.max_roles,
                required_roles=[str(r) for r in g.required_roles],
                blacklisted_roles=[str(r) for r in g.blacklisted_roles],
                items=item_schemas,
            )
        )

    return result
