"""API endpoints for Dashboard Analytics and charts."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.logging import ActionLog
from dashboard.backend.core.database import get_db
from dashboard.backend.core.security import get_current_user
from dashboard.backend.services.rbac_service import RBACService

router = APIRouter()


@router.get("/{guild_id}")
async def get_analytics(
    guild_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Fetch high-level analytics for the guild dashboard."""
    has_perm = await RBACService.has_permission(
        session, guild_id, current_user["id"], "view_analytics"
    )
    if not has_perm:
        raise HTTPException(status_code=403, detail="Forbidden")

    # Example: Count total events by severity in the last 30 days
    stmt = (
        select(ActionLog.severity, func.count(ActionLog.id))
        .where(ActionLog.guild_id == guild_id)
        .group_by(ActionLog.severity)
    )
    result = await session.execute(stmt)
    severity_counts = {str(sev): count for sev, count in result.all()}

    # In a full implementation, we'd also join against Warnings, Incidents, etc.

    return {
        "total_events": sum(severity_counts.values()),
        "severity_distribution": severity_counts,
        "recent_activity_score": severity_counts.get("3", 0) * 10 + severity_counts.get("2", 0) * 5,
    }
