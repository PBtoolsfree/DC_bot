"""Abstract Base Class for XP Providers."""

from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
import discord


class XPProvider(ABC):
    """Base interface for calculating and granting XP."""

    @abstractmethod
    async def process_event(self, session: AsyncSession, event_data: dict) -> int:
        """Calculates and grants XP. Returns the amount granted."""
        pass
