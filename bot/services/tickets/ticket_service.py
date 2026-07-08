"""Core Ticket Orchestrator."""

import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import discord

from bot.database.models.tickets import Ticket, TicketCategory, TicketMessage
from bot.services.tickets.relay_service import RelayService
from bot.services.tickets.assignment_service import AssignmentService
# Assume StreamingService from Logging
from bot.services.logging.streaming_service import StreamingService


class TicketService:
    """Orchestrates ticket creation, updates, and closure."""

    @staticmethod
    async def open_ticket(
        session: AsyncSession, 
        guild: discord.Guild, 
        owner: discord.Member, 
        category: TicketCategory,
        is_anonymous: bool = False
    ) -> Ticket:
        """Creates a ticket record and provisions a Discord channel if not relay mode."""
        
        # 1. State Machine check
        # We could check if they exceeded max tickets open...
        
        # 2. Assignment
        assigned_to = await AssignmentService.assign_least_loaded(session, guild, None, category) # type: ignore
        
        # 3. Create Record
        ticket = Ticket(
            guild_id=guild.id,
            owner_id=owner.id,
            category_id=category.id,
            status="open",
            claimed_by_id=assigned_to,
            is_anonymous=is_anonymous
        )
        session.add(ticket)
        await session.flush()
        
        # 4. Create Discord Channel
        # If it's an anonymous ticket, we use Relay Mode, but we still need a channel for staff
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False)
        }
        
        for role_id in category.support_team_roles:
            r = guild.get_role(role_id)
            if r:
                overwrites[r] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                
        # If not anonymous, the user gets access to the channel directly
        if not is_anonymous:
            overwrites[owner] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
        cat_obj = guild.get_channel(category.category_channel_id) if category.category_channel_id else None
        
        # Replace {id} placeholder
        name = category.naming_template.replace("{id}", f"{ticket.id:04d}")
        
        channel = await guild.create_text_channel(
            name=name,
            category=cat_obj, # type: ignore
            overwrites=overwrites,
            reason=f"Ticket {ticket.id} created by {owner.id}"
        )
        
        ticket.channel_id = channel.id
        await session.flush()
        
        # 5. Relay Mapping
        if is_anonymous:
            await RelayService.establish_relay(owner.id, channel.id)
            
        # 6. Broadcast Event
        await StreamingService.broadcast(
            guild_id=guild.id,
            event_type="TICKET_CREATED",
            payload={
                "ticket_id": ticket.id,
                "owner_id": str(owner.id),
                "is_anonymous": is_anonymous
            }
        )
        
        return ticket

    @staticmethod
    async def log_message(session: AsyncSession, ticket_id: int, message: discord.Message) -> None:
        """Stores a raw message for hybrid transcript storage."""
        attachments = [att.url for att in message.attachments]
        
        t_msg = TicketMessage(
            ticket_id=ticket_id,
            message_id=message.id,
            author_id=message.author.id,
            author_name=message.author.name,
            content=message.content,
            attachments=attachments
        )
        session.add(t_msg)
        await session.flush()

    @staticmethod
    async def change_status(session: AsyncSession, ticket: Ticket, new_status: str, operator_id: int) -> bool:
        """Validate state machine transition and update."""
        valid_transitions = {
            "open": ["claimed", "closed", "deleted"],
            "claimed": ["in_progress", "waiting_user", "closed"],
            "in_progress": ["resolved", "waiting_user", "waiting_staff"],
            "waiting_user": ["in_progress", "resolved", "closed", "archived"], # e.g. auto close
            "waiting_staff": ["in_progress", "resolved"],
            "resolved": ["closed", "open"], # reopen
            "closed": ["archived", "deleted", "open"],
            "archived": ["deleted"],
        }
        
        if new_status not in valid_transitions.get(ticket.status, []):
            return False # Invalid transition
            
        ticket.status = new_status
        if new_status == "closed":
            ticket.closed_at = datetime.datetime.now(datetime.timezone.utc)
            
        if new_status == "archived":
            ticket.archived_at = datetime.datetime.now(datetime.timezone.utc)
            
        await session.flush()
        
        await StreamingService.broadcast(
            guild_id=ticket.guild_id,
            event_type="TICKET_STATUS_CHANGED",
            payload={
                "ticket_id": ticket.id,
                "old_status": ticket.status,
                "new_status": new_status,
                "operator_id": str(operator_id)
            }
        )
        return True
