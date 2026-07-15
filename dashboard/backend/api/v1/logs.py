"""API endpoints for dashboard logs view."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.logging.search_service import SearchService
from dashboard.backend.core.database import get_db
from dashboard.backend.core.security import get_current_user
from dashboard.backend.services.rbac_service import RBACService

router = APIRouter()


@router.get("/{guild_id}")
async def get_logs(
    guild_id: int,
    action_type: str | None = None,
    user_id: int | None = None,
    days: int = Query(7, ge=1, le=30),
    page: int = Query(1, ge=1),
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Search and paginate logs for the dashboard."""
    has_perm = await RBACService.has_permission(
        session,
        guild_id,
        current_user["id"],
        "manage_logs",
        discord_access_token=current_user.get("access_token"),
    )
    if not has_perm:
        raise HTTPException(status_code=403, detail="Forbidden")

    logs = await SearchService.search(
        session=session,
        guild_id=guild_id,
        action_type=action_type,
        user_id=user_id,
        days_ago=days,
        limit=50,
        page=page,
    )

    return {
        "page": page,
        "logs": [
            {
                "id": log.id,
                "action": log.action_type,
                "executor": str(log.executor_id) if log.executor_id else None,
                "target": str(log.target_id) if log.target_id else None,
                "before": log.before_data,
                "after": log.after_data,
                "timestamp": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
    }
