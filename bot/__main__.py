"""Allow running the bot package with `python -m bot`."""

from bot.main import main

import asyncio

asyncio.run(main())
