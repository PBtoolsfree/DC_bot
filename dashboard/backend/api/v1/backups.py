"""Backup & Restore APIs."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.backup import ServerBackup
from dashboard.backend.core.database import get_db
from dashboard.backend.core.security import get_current_user
from dashboard.backend.services.rbac_service import RBACService
from dashboard.shared.schemas.modules.backup import BackupResponse

router = APIRouter()


@router.get("/{guild_id}")
async def list_backups(
    guild_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[BackupResponse]:
    """List all backups for a guild."""
    has_perm = await RBACService.has_permission(
        session, guild_id, current_user["id"], "manage_backups",
        discord_access_token=current_user.get("access_token"),
    )
    if not has_perm:
        raise HTTPException(status_code=403, detail="Forbidden")

    stmt = (
        select(ServerBackup)
        .where(ServerBackup.guild_id == guild_id)
        .order_by(ServerBackup.created_at.desc())
    )
    backups = (await session.execute(stmt)).scalars().all()

    return [
        BackupResponse(
            id=b.id,
            guild_id=str(b.guild_id),
            creator_id=str(b.creator_id),
            name=b.name,
            description=b.description,
            created_at=b.created_at,
        )
        for b in backups
    ]
