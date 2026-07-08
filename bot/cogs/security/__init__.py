"""Security and Anti-Nuke cogs."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot.core.bot import ManagementBot


async def setup(bot: ManagementBot) -> None:
    """Load the security cogs."""
    from .security_config import SecurityConfigCog
    from .security_listener import SecurityListenerCog
    from .tasks import SecurityTasksCog

    await bot.add_cog(SecurityListenerCog(bot))
    await bot.add_cog(SecurityConfigCog(bot))
    await bot.add_cog(SecurityTasksCog(bot))
