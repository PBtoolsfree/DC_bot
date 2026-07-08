"""Background tasks for Ticket Automations (SLA, Retention, Archiving)."""

import asyncio
import datetime
import logging

from discord.ext import commands, tasks
from sqlalchemy import select, delete

from bot.database.core import db
from bot.database.models.tickets import Ticket, TicketCategory, TicketMessage
from bot.services.tickets.ticket_service import TicketService
from bot.services.logging.streaming_service import StreamingService

logger = logging.getLogger(__name__)


class TicketAutomationsTask(commands.Cog):
    """Monitors SLAs and performs auto-archive/retention cleanup."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.sla_monitor.start()
        self.retention_cleanup.start()

    def cog_unload(self) -> None:
        self.sla_monitor.cancel()
        self.retention_cleanup.cancel()

    @tasks.loop(minutes=15)
    async def sla_monitor(self) -> None:
        """Alerts staff if a ticket has breached its SLA response time."""
        now = datetime.datetime.now(datetime.timezone.utc)
        
        try:
            async with db.session() as session:
                # Find open tickets waiting for staff
                stmt = (
                    select(Ticket, TicketCategory)
                    .join(TicketCategory)
                    .where(Ticket.status.in_(["open", "waiting_staff"]))
                )
                result = await session.execute(stmt)
                
                for ticket, category in result.all():
                    elapsed = (now - ticket.created_at).total_seconds() / 3600
                    if elapsed > category.sla_response_hours:
                        # SLA Breached
                        guild = self.bot.get_guild(ticket.guild_id)
                        if guild and ticket.channel_id:
                            channel = guild.get_channel(ticket.channel_id)
                            if channel:
                                await channel.send( # type: ignore
                                    f"⚠️ **SLA BREACH**! This ticket has been waiting for more than {category.sla_response_hours} hours."
                                )
                                
                        # Log Event
                        await StreamingService.broadcast(
                            guild_id=ticket.guild_id,
                            event_type="SLA_BREACH",
                            payload={"ticket_id": ticket.id}
                        )
                        
        except Exception as e:
            logger.error("sla_monitor_failed", exc_info=e)

    @tasks.loop(hours=24)
    async def retention_cleanup(self) -> None:
        """Purges raw TicketMessages for tickets that have been archived for >30 days."""
        now = datetime.datetime.now(datetime.timezone.utc)
        retention_limit = now - datetime.timedelta(days=30)
        
        try:
            async with db.session() as session:
                # Find tickets archived older than 30 days
                stmt = select(Ticket.id).where(
                    Ticket.status.in_(["archived", "deleted"]),
                    Ticket.archived_at < retention_limit
                )
                result = await session.execute(stmt)
                expired_ticket_ids = result.scalars().all()
                
                if expired_ticket_ids:
                    del_stmt = delete(TicketMessage).where(TicketMessage.ticket_id.in_(expired_ticket_ids))
                    await session.execute(del_stmt)
                    await session.commit()
                    logger.info(f"Purged raw messages for {len(expired_ticket_ids)} archived tickets.")
                    
        except Exception as e:
            logger.error("retention_cleanup_failed", exc_info=e)

    @sla_monitor.before_loop
    @retention_cleanup.before_loop
    async def before_tasks(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TicketAutomationsTask(bot))
