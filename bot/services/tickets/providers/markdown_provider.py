"""Markdown Transcript Provider."""

from bot.database.models.tickets import Ticket, TicketMessage
from bot.services.tickets.providers.base import TranscriptProvider


class MarkdownTranscriptProvider(TranscriptProvider):
    """Generates a Markdown transcript."""

    @property
    def extension(self) -> str:
        return ".md"

    async def generate(self, ticket: Ticket, messages: list[TicketMessage]) -> bytes:
        """Generate Markdown structure."""

        lines = []
        lines.append(f"# Ticket Transcript: {ticket.id}")
        lines.append(f"**Owner ID**: {ticket.owner_id}")
        lines.append(f"**Created At**: {ticket.created_at}")
        lines.append(f"**Status**: {ticket.status}")
        lines.append("\n---\n")

        for m in messages:
            lines.append(f"### {m.author_name} ({m.author_id})")
            lines.append(f"*{m.timestamp}*")
            if m.content:
                lines.append(f"\n{m.content}\n")
            if m.attachments:
                lines.append("\n**Attachments:**")
                for att in m.attachments:
                    lines.append(f"- {att}")
            lines.append("\n---\n")

        return "\n".join(lines).encode("utf-8")
