"""Welcome & Autorole APIs."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.repositories.enterprise_repo import EnterpriseRepository
from dashboard.backend.core.database import get_db
from dashboard.backend.core.security import get_current_user
from dashboard.backend.services.rbac_service import RBACService
from dashboard.shared.schemas.modules.welcome import WelcomeSettingsSchema

router = APIRouter()


@router.get("/{guild_id}/settings")
async def get_welcome_settings(
    guild_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> WelcomeSettingsSchema | dict:
    has_perm = await RBACService.has_permission(
        session,
        guild_id,
        current_user["id"],
        "manage_welcome",
        discord_access_token=current_user.get("access_token"),
    )
    if not has_perm:
        raise HTTPException(status_code=403, detail="Forbidden")

    settings = await EnterpriseRepository.get_welcome_settings(session, guild_id)
    if not settings:
        return {}

    return WelcomeSettingsSchema(
        guild_id=str(settings.guild_id),
        welcome_enabled=settings.welcome_enabled,
        welcome_channel_id=(
            str(settings.welcome_channel_id) if settings.welcome_channel_id else None
        ),
        welcome_message=settings.welcome_message,
        welcome_image_url=settings.welcome_image_url,
        goodbye_enabled=settings.goodbye_enabled,
        goodbye_channel_id=(
            str(settings.goodbye_channel_id) if settings.goodbye_channel_id else None
        ),
        goodbye_message=settings.goodbye_message,
    )
