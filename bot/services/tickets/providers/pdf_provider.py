"""PDF Transcript Provider using WeasyPrint."""

import logging

from bot.database.models.tickets import Ticket, TicketMessage
from bot.services.tickets.providers.base import TranscriptProvider
from bot.services.tickets.providers.html_provider import HTMLTranscriptProvider

logger = logging.getLogger(__name__)


class PDFTranscriptProvider(TranscriptProvider):
    """Generates a PDF transcript by rendering HTML first and converting."""

    def __init__(self) -> None:
        self.html_provider = HTMLTranscriptProvider()

    @property
    def extension(self) -> str:
        return ".pdf"

    async def generate(self, ticket: Ticket, messages: list[TicketMessage]) -> bytes:
        """Generate PDF using WeasyPrint."""

        # 1. Generate HTML
        html_bytes = await self.html_provider.generate(ticket, messages)

        try:
            from weasyprint import HTML

            # 2. Convert HTML to PDF
            return HTML(string=html_bytes.decode("utf-8")).write_pdf()
        except Exception as e:
            logger.error("pdf_generation_failed", exc_info=e)
            # Fallback to HTML bytes as approved in the mega-prompt
            return html_bytes
