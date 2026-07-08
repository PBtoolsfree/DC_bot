"""Enterprise Logging and Audit Cogs."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot.core.bot import ManagementBot


async def setup(bot: ManagementBot) -> None:
    """Load the logging cogs."""
    from .logs_message import MessageLogsCog
    from .logs_member import MemberLogsCog
    from .logs_server import ServerLogsCog
    from .logs_voice import VoiceLogsCog
    from .logs_advanced import AdvancedLogsCog
    from .logs_config import LoggingConfigCog
    from .tasks import LoggingTasksCog

    await bot.add_cog(MessageLogsCog(bot))
    await bot.add_cog(MemberLogsCog(bot))
    await bot.add_cog(ServerLogsCog(bot))
    await bot.add_cog(VoiceLogsCog(bot))
    await bot.add_cog(AdvancedLogsCog(bot))
    await bot.add_cog(LoggingConfigCog(bot))
    await bot.add_cog(LoggingTasksCog(bot))
