"""API endpoints for Verification Dashboard configuration."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.repositories.verification_repo import VerificationRepository
from dashboard.backend.core.database import get_db
from dashboard.backend.core.security import get_current_user
from dashboard.backend.services.rbac_service import RBACService
from dashboard.shared.schemas.verification import (
    VerificationSettingsResponse,
    VerificationSettingsUpdate,
)

router = APIRouter()


@router.get("/{guild_id}", response_model=VerificationSettingsResponse)
async def get_verification_settings(
    guild_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Any:
    """Fetch verification settings for the dashboard."""
    has_perm = await RBACService.has_permission(
        session,
        guild_id,
        current_user["id"],
        "manage_verification",
        discord_access_token=current_user.get("access_token"),
    )
    if not has_perm:
        raise HTTPException(status_code=403, detail="Forbidden")

    settings = await VerificationRepository.get_settings(session, guild_id)
    if not settings:
        # Return defaults
        return VerificationSettingsResponse(
            guild_id=str(guild_id),
            enabled=False,
            verification_type="button",
            timeout_minutes=15,
            max_attempts=3,
            risk_threshold_high=70,
            language="en-US",
            delete_failed_messages=True,
            kick_on_timeout=False,
        )

    return VerificationSettingsResponse(
        guild_id=str(guild_id),
        enabled=settings.enabled,
        verification_type=settings.verification_type,
        quarantine_role_id=(
            str(settings.quarantine_role_id) if settings.quarantine_role_id else None
        ),
        verified_role_id=str(settings.verified_role_id) if settings.verified_role_id else None,
        temporary_role_id=str(settings.temporary_role_id) if settings.temporary_role_id else None,
        verification_channel_id=(
            str(settings.verification_channel_id) if settings.verification_channel_id else None
        ),
        log_channel_id=str(settings.log_channel_id) if settings.log_channel_id else None,
        timeout_minutes=settings.timeout_minutes,
        max_attempts=settings.max_attempts,
        risk_threshold_high=settings.risk_threshold_high,
        language=settings.language,
        delete_failed_messages=settings.delete_failed_messages,
        kick_on_timeout=settings.kick_on_timeout,
    )


@router.put("/{guild_id}", response_model=VerificationSettingsResponse)
async def update_verification_settings(
    guild_id: int,
    payload: VerificationSettingsUpdate,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Any:
    """Update verification configuration."""
    has_perm = await RBACService.has_permission(
        session,
        guild_id,
        current_user["id"],
        "manage_verification",
        discord_access_token=current_user.get("access_token"),
    )
    if not has_perm:
        raise HTTPException(status_code=403, detail="Forbidden")

    update_data = payload.dict(exclude_unset=True)

    # Convert string IDs back to ints for DB
    for key in [
        "quarantine_role_id",
        "verified_role_id",
        "temporary_role_id",
        "verification_channel_id",
        "log_channel_id",
    ]:
        if key in update_data and update_data[key] is not None:
            try:
                update_data[key] = int(update_data[key])
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid ID for {key}") from None

    await VerificationRepository.upsert_settings(session, guild_id, **update_data)

    # In a full app, also log to DashboardAuditLog

    return await get_verification_settings(guild_id, current_user, session)
