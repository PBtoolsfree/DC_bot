"""Archive Service."""

import discord
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.tickets import Ticket, TicketMessage
from bot.services.tickets.ticket_service import TicketService
from bot.services.tickets.transcript_service import TranscriptService


class ArchiveService:
    """Manages archiving and deleting tickets, including Hybrid Message Storage."""

    @staticmethod
    async def archive_ticket(
        session: AsyncSession, guild: discord.Guild, ticket: Ticket, operator_id: int
    ) -> bool:
        """Closes the channel, generates transcripts, and purges raw messages."""
        if ticket.status in ["archived", "deleted"]:
            return False

        # 1. State transition
        success = await TicketService.change_status(session, ticket, "archived", operator_id)
        if not success:
            # Maybe it wasn't closed yet, force it through closed -> archived
            await TicketService.change_status(session, ticket, "closed", operator_id)
            await TicketService.change_status(session, ticket, "archived", operator_id)

        # 2. Generate Transcript
        t_service = TranscriptService()
        await t_service.generate_transcript(session, ticket, "html")
        await t_service.generate_transcript(session, ticket, "json")

        # 3. Purge Raw TicketMessages (Hybrid Storage)
        stmt = delete(TicketMessage).where(TicketMessage.ticket_id == ticket.id)
        await session.execute(stmt)

        # 4. Delete the Discord Channel
        if ticket.channel_id:
            channel = guild.get_channel(ticket.channel_id)
            if channel:
                try:
                    await channel.delete(reason="Ticket Archived")  # type: ignore
                except discord.HTTPException:
                    pass
            ticket.channel_id = None

        await session.flush()
        return True
