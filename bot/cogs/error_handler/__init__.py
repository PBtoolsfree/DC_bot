"""Error handler cog — global error handling for slash commands."""

from __future__ import annotations

from bot.cogs.error_handler.error_handler import ErrorHandler


async def setup(bot: object) -> None:
    """Load the ErrorHandler cog."""
    from bot.core.bot import ManagementBot

    assert isinstance(bot, ManagementBot)
    await bot.add_cog(ErrorHandler(bot))
