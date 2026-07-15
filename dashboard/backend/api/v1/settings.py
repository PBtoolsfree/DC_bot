"""API endpoints for module settings."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.repositories.guild_repo import GuildRepository
from dashboard.backend.core.database import get_db
from dashboard.backend.core.security import get_current_user
from dashboard.backend.services.rbac_service import RBACService

router = APIRouter()


@router.get("/{guild_id}/{module_name}")
async def get_settings(
    guild_id: int,
    module_name: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Fetch configuration for a specific module."""
    # RBAC check (simplified: must have specific permission for that module)
    perm_name = f"manage_{module_name}" if module_name != "automod" else "manage_automod"
    has_perm = await RBACService.has_permission(
        session,
        guild_id,
        current_user["id"],
        perm_name,
        discord_access_token=current_user.get("access_token"),
    )
    if not has_perm:
        raise HTTPException(status_code=403, detail="Forbidden")

    settings = await GuildRepository.get_module_settings(session, guild_id, module_name)
    if not settings:
        return {"enabled": False, "config": {}}

    return {"enabled": settings.enabled, "config": settings.config}


@router.put("/{guild_id}/{module_name}")
async def update_settings(
    guild_id: int,
    module_name: str,
    payload: dict[str, Any],
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update configuration for a specific module."""
    perm_name = f"manage_{module_name}" if module_name != "automod" else "manage_automod"
    has_perm = await RBACService.has_permission(
        session,
        guild_id,
        current_user["id"],
        perm_name,
        discord_access_token=current_user.get("access_token"),
    )
    if not has_perm:
        raise HTTPException(status_code=403, detail="Forbidden")

    enabled = payload.get("enabled", False)
    config = payload.get("config", {})

    await GuildRepository.upsert_module_settings(session, guild_id, module_name, enabled, config)

    # Audit log creation should happen here in a real implementation
    # e.g., AuditService.log_dashboard_action(...)

    return {"status": "success"}
