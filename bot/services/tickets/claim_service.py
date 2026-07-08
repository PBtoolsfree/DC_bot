"""Claim Service."""

import discord
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.tickets import Ticket
from bot.services.tickets.ticket_service import TicketService
from bot.services.logging.streaming_service import StreamingService


class ClaimService:
    """Handles claiming and transferring ownership of tickets among staff."""

    @staticmethod
    async def claim_ticket(session: AsyncSession, ticket: Ticket, staff_member: discord.Member) -> bool:
        """Staff claims an open ticket."""
        if ticket.claimed_by_id:
            return False # Already claimed
            
        ticket.claimed_by_id = staff_member.id
        
        # Transition state machine
        await TicketService.change_status(session, ticket, "claimed", staff_member.id)
        
        await StreamingService.broadcast(
            guild_id=ticket.guild_id,
            event_type="TICKET_CLAIMED",
            payload={
                "ticket_id": ticket.id,
                "staff_id": str(staff_member.id)
            }
        )
        return True

    @staticmethod
    async def transfer_ticket(session: AsyncSession, ticket: Ticket, new_staff: discord.Member, current_staff: discord.Member) -> bool:
        """Transfer a claimed ticket to another staff member."""
        if ticket.claimed_by_id != current_staff.id:
            return False # Not yours to transfer
            
        ticket.claimed_by_id = new_staff.id
        await session.flush()
        
        await StreamingService.broadcast(
            guild_id=ticket.guild_id,
            event_type="TICKET_TRANSFERRED",
            payload={
                "ticket_id": ticket.id,
                "old_staff_id": str(current_staff.id),
                "new_staff_id": str(new_staff.id)
            }
        )
        return True
