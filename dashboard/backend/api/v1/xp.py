"""Leveling & XP APIs."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.repositories.enterprise_repo import EnterpriseRepository
from dashboard.backend.core.database import get_db
from dashboard.backend.core.security import get_current_user
from dashboard.backend.services.rbac_service import RBACService
from dashboard.shared.schemas.modules.xp import XPSettingsSchema

router = APIRouter()


@router.get("/{guild_id}/settings")
async def get_xp_settings(
    guild_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> XPSettingsSchema | dict:
    has_perm = await RBACService.has_permission(
        session,
        guild_id,
        current_user["id"],
        "manage_xp",
        discord_access_token=current_user.get("access_token"),
    )
    if not has_perm:
        raise HTTPException(status_code=403, detail="Forbidden")

    settings = await EnterpriseRepository.get_xp_settings(session, guild_id)
    if not settings:
        return {}

    return XPSettingsSchema(
        enabled=settings.enabled,
        message_xp_min=settings.message_xp_min,
        message_xp_max=settings.message_xp_max,
        message_cooldown_sec=settings.message_cooldown_sec,
        voice_xp_per_minute=settings.voice_xp_per_minute,
        ignored_channels=[str(c) for c in settings.ignored_channels],
    )


@router.get("/{guild_id}/leaderboard")
async def get_xp_leaderboard(
    guild_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    has_perm = await RBACService.has_permission(
        session,
        guild_id,
        current_user["id"],
        "view_analytics",
        discord_access_token=current_user.get("access_token"),
    )
    if not has_perm:
        raise HTTPException(status_code=403, detail="Forbidden")

    top_xp = await EnterpriseRepository.get_top_xp(session, guild_id, limit=10)
    return [
        {
            "user_id": str(xp.user_id),
            "level": xp.level,
            "xp": xp.xp,
            "messages_sent": xp.messages_sent,
            "voice_minutes": xp.voice_minutes,
        }
        for xp in top_xp
    ]
