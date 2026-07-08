"""Bot entry point — initializes and runs the management bot.

Usage:
    python -m bot
    python bot/main.py
"""

from __future__ import annotations

import asyncio
import signal
import sys

from bot.config import get_settings
from bot.core.bot import ManagementBot
from bot.utils.logger import get_logger, setup_logging


async def main() -> None:
    """Initialize and run the Discord Management Bot.

    This function:
    1. Loads and validates configuration from .env
    2. Sets up structured logging
    3. Creates the bot instance with all subsystems
    4. Registers OS signal handlers for graceful shutdown
    5. Starts the bot and blocks until shutdown
    """
    # Load configuration (fails fast if required vars are missing)
    settings = get_settings()

    # Configure structured logging
    setup_logging(level=settings.log_level, log_format=settings.log_format)
    logger = get_logger(__name__)

    logger.info(
        "bot.starting",
        environment=settings.environment,
        debug=settings.debug,
        log_level=settings.log_level,
    )

    # Create bot instance
    bot = ManagementBot(settings=settings)

    # Register signal handlers for graceful shutdown (Unix only)
    if sys.platform != "win32":
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(bot.close()))

    # Start the bot
    try:
        async with bot:
            await bot.start(settings.discord_token)
    except KeyboardInterrupt:
        logger.info("bot.interrupted")
    except Exception:
        logger.exception("bot.fatal_error")
        sys.exit(1)
    finally:
        if not bot.is_closed():
            await bot.close()
        logger.info("bot.stopped")


if __name__ == "__main__":
    asyncio.run(main())
