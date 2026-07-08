"""JSON Transcript Provider."""

import json
from typing import Any

from bot.database.models.tickets import Ticket, TicketMessage
from bot.services.tickets.providers.base import TranscriptProvider


class JSONTranscriptProvider(TranscriptProvider):
    """Generates a raw JSON payload of the ticket and messages."""

    @property
    def extension(self) -> str:
        return ".json"

    async def generate(self, ticket: Ticket, messages: list[TicketMessage]) -> bytes:
        """Generate JSON structure."""
        
        data: dict[str, Any] = {
            "ticket": {
                "id": ticket.id,
                "guild_id": ticket.guild_id,
                "channel_id": ticket.channel_id,
                "owner_id": ticket.owner_id,
                "created_at": ticket.created_at.isoformat(),
                "closed_at": ticket.closed_at.isoformat() if ticket.closed_at else None,
                "status": ticket.status
            },
            "messages": [
                {
                    "message_id": m.message_id,
                    "author_id": m.author_id,
                    "author_name": m.author_name,
                    "content": m.content,
                    "attachments": m.attachments,
                    "timestamp": m.timestamp.isoformat()
                }
                for m in messages
            ]
        }
        
        return json.dumps(data, indent=2).encode("utf-8")
