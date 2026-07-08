"""Abstract Base Class for Transcript Providers."""

from abc import ABC, abstractmethod
from pathlib import Path

from bot.database.models.tickets import Ticket, TicketMessage


class TranscriptProvider(ABC):
    """Base interface for all Transcript format providers."""

    @property
    @abstractmethod
    def extension(self) -> str:
        """The file extension (e.g., .html, .pdf)."""

    @abstractmethod
    async def generate(self, ticket: Ticket, messages: list[TicketMessage]) -> Path | bytes:
        """
        Generate the transcript.
        Returns either a Path to a temporary file or raw bytes.
        """
