"""Abstract Base Class for Image Providers."""

from abc import ABC, abstractmethod

import discord


class ImageProvider(ABC):
    """Base interface for generating dynamic images."""

    @abstractmethod
    async def generate_welcome_card(
        self, member: discord.Member, background_url: str | None = None
    ) -> bytes:
        """Generates a welcome image."""

    @abstractmethod
    async def generate_rank_card(
        self, member: discord.Member, xp: int, level: int, rank: int
    ) -> bytes:
        """Generates an XP rank card."""
