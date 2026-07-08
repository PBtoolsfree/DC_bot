"""Setup for AutoMod cogs."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot.core.bot import ManagementBot


async def setup(bot: "ManagementBot") -> None:
    """Load the automod cogs."""
    from .automod_config import AutoModConfigCog
    from .automod_listener import AutoModListenerCog
    from .tasks import AutoModTasksCog

    await bot.add_cog(AutoModListenerCog(bot))
    await bot.add_cog(AutoModConfigCog(bot))
    await bot.add_cog(AutoModTasksCog(bot))
