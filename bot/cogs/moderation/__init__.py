"""Moderation Cog — Discord interface for moderation commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

from bot.cogs.moderation.moderation import ModerationCog

if TYPE_CHECKING:
    from bot.core.bot import ManagementBot


async def setup(bot: ManagementBot) -> None:
    """Load the ModerationCog."""
    await bot.add_cog(ModerationCog(bot))
