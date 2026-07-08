"""Transcript Service."""

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.tickets import Ticket, TicketMessage, TicketTranscript
from bot.services.tickets.providers.html_provider import HTMLTranscriptProvider
from bot.services.tickets.providers.json_provider import JSONTranscriptProvider
from bot.services.tickets.providers.markdown_provider import MarkdownTranscriptProvider
from bot.services.tickets.providers.pdf_provider import PDFTranscriptProvider


class TranscriptService:
    """Orchestrates generating and saving transcripts."""

    def __init__(self) -> None:
        self.providers = {
            "html": HTMLTranscriptProvider(),
            "pdf": PDFTranscriptProvider(),
            "markdown": MarkdownTranscriptProvider(),
            "json": JSONTranscriptProvider(),
        }

        self.export_dir = Path("data/transcripts")
        self.export_dir.mkdir(parents=True, exist_ok=True)

    async def generate_transcript(
        self, session: AsyncSession, ticket: Ticket, format_type: str = "html"
    ) -> TicketTranscript | None:
        """Fetch all messages for the ticket, generate the transcript, and store metadata."""

        provider = self.providers.get(format_type.lower())
        if not provider:
            provider = self.providers["html"]

        # 1. Fetch messages
        stmt = (
            select(TicketMessage)
            .where(TicketMessage.ticket_id == ticket.id)
            .order_by(TicketMessage.timestamp)
        )
        result = await session.execute(stmt)
        messages = list(result.scalars().all())

        if not messages:
            return None  # No messages to transcribe

        # 2. Generate raw bytes
        data = await provider.generate(ticket, messages)

        # 3. Save to disk (In production, this could be AWS S3 upload)
        # We'll mock it by saving to local disk
        import datetime as dt

        now_str = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d%H%M%S")
        filename = f"ticket_{ticket.id}_{now_str}{provider.extension}"
        filepath = self.export_dir / filename

        import aiofiles

        async with aiofiles.open(filepath, "wb") as f:
            await f.write(data)

        # 4. Save metadata in DB
        transcript = TicketTranscript(
            ticket_id=ticket.id,
            format=provider.extension.replace(".", ""),
            url=str(filepath.absolute()),
        )
        session.add(transcript)
        await session.flush()

        return transcript
