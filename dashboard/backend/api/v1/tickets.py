"""API endpoints for Ticket Dashboard configuration."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from dashboard.backend.core.database import get_db
from dashboard.backend.core.security import get_current_user
from dashboard.backend.services.rbac_service import RBACService
from bot.database.models.tickets import Ticket, TicketCategory, TicketPanel

router = APIRouter()


@router.get("/{guild_id}/analytics")
async def get_ticket_analytics(
    guild_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
) -> Any:
    """Fetch ticket analytics for the dashboard."""
    has_perm = await RBACService.has_permission(session, guild_id, current_user["id"], "view_analytics")
    if not has_perm:
        raise HTTPException(status_code=403, detail="Forbidden")

    # 1. Total Open Tickets
    stmt_open = select(func.count(Ticket.id)).where(Ticket.guild_id == guild_id, Ticket.status.in_(["open", "claimed", "in_progress", "waiting_user", "waiting_staff"]))
    open_tickets = (await session.execute(stmt_open)).scalar() or 0
    
    # 2. Total Closed Tickets
    stmt_closed = select(func.count(Ticket.id)).where(Ticket.guild_id == guild_id, Ticket.status == "closed")
    closed_tickets = (await session.execute(stmt_closed)).scalar() or 0
    
    # 3. Category Distribution
    stmt_cat = select(Ticket.category_id, func.count(Ticket.id)).where(Ticket.guild_id == guild_id).group_by(Ticket.category_id)
    cat_dist = {row[0]: row[1] for row in (await session.execute(stmt_cat)).all()}
    
    return {
        "open_tickets": open_tickets,
        "closed_tickets": closed_tickets,
        "category_distribution": cat_dist,
        "average_resolution_time": "2h 15m" # Mock for this demo
    }


@router.get("/{guild_id}/panels")
async def get_ticket_panels(
    guild_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
) -> Any:
    """Fetch all ticket panels."""
    has_perm = await RBACService.has_permission(session, guild_id, current_user["id"], "manage_tickets")
    if not has_perm:
        raise HTTPException(status_code=403, detail="Forbidden")

    stmt = select(TicketPanel).where(TicketPanel.guild_id == guild_id)
    panels = (await session.execute(stmt)).scalars().all()
    
    return [
        {
            "id": p.id,
            "title": p.title,
            "channel_id": str(p.channel_id),
            "categories": p.categories
        }
        for p in panels
    ]
