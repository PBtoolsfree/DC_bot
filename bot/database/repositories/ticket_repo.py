"""Ticket Repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.tickets import Ticket, TicketCategory, TicketPanel


class TicketRepository:
    """Handles database persistence for the Ticket system."""

    @staticmethod
    async def get_ticket_by_channel(session: AsyncSession, channel_id: int) -> Ticket | None:
        stmt = select(Ticket).where(Ticket.channel_id == channel_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
        
    @staticmethod
    async def get_ticket_by_id(session: AsyncSession, ticket_id: int) -> Ticket | None:
        stmt = select(Ticket).where(Ticket.id == ticket_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_category(session: AsyncSession, category_id: int) -> TicketCategory | None:
        stmt = select(TicketCategory).where(TicketCategory.id == category_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
        
    @staticmethod
    async def get_panel(session: AsyncSession, panel_id: int) -> TicketPanel | None:
        stmt = select(TicketPanel).where(TicketPanel.id == panel_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
