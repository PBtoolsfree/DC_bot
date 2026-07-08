"""Custom Bot subclass with lifecycle management.

Handles:
- Database initialization and teardown
- Redis connection management
- Dynamic cog loading from the cogs/ directory
- Structured logging integration
- Graceful shutdown
"""

from __future__ import annotations

import traceback
from pathlib import Path
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from bot.config import BotSettings
from bot.database.engine import DatabaseEngine
from bot.utils.logger import get_logger

if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = get_logger(__name__)


class ManagementBot(commands.Bot):
    """Production-grade Discord Management Bot.

    This is the central bot class that orchestrates all subsystems:
    database, Redis cache, cog modules, and the API bridge.

    Attributes:
        settings: Validated application configuration.
        db: Async database engine and session factory.
        redis: Async Redis client for caching and pub/sub.
        start_time: Timestamp when the bot connected to Discord.
    """

    def __init__(self, settings: BotSettings) -> None:
        """Initialize the bot with all required intents and configuration.

        Args:
            settings: Validated application settings from config.py.
        """
        # Configure intents — we need all privileged intents for management features
        intents = discord.Intents.all()

        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            help_command=None,
            case_insensitive=True,
            max_messages=10000,
            owner_ids=set(settings.bot_owner_ids) if settings.bot_owner_ids else None,
        )

        self.settings: BotSettings = settings
        self.db: DatabaseEngine = DatabaseEngine(settings)
        self.redis: Redis | None = None  # type: ignore[type-arg]
        self.start_time: float = 0.0

    async def setup_hook(self) -> None:
        """Called after the bot is logged in but before connecting to the gateway.

        This is the proper place for async initialization:
        - Initialize database and create tables
        - Connect to Redis
        - Load all cog extensions
        - Sync slash commands (dev guild only in development)
        """
        logger.info("bot.setup_hook.start", environment=self.settings.environment)

        # --- Database ---
        await self.db.initialize()
        logger.info("bot.database.connected")

        # --- Redis ---
        await self._connect_redis()

        # --- Load Cogs ---
        await self._load_all_cogs()

        # --- Sync Commands ---
        if self.settings.discord_dev_guild_id:
            guild = discord.Object(id=self.settings.discord_dev_guild_id)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            logger.info(
                "bot.commands.synced",
                guild_id=self.settings.discord_dev_guild_id,
                command_count=len(synced),
            )
        else:
            synced = await self.tree.sync()
            logger.info("bot.commands.synced.global", command_count=len(synced))

        logger.info("bot.setup_hook.complete")

    async def on_ready(self) -> None:
        """Fires when the bot has connected to Discord and is ready.

        NOTE: This can fire multiple times during the bot's lifetime
        (e.g., after a reconnect). Do NOT put heavy initialization here.
        """
        import time

        self.start_time = time.time()

        assert self.user is not None
        logger.info(
            "bot.ready",
            user=str(self.user),
            user_id=self.user.id,
            guild_count=len(self.guilds),
            shard_count=self.shard_count or 1,
        )

        # Set activity status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(self.guilds)} servers",
        )
        await self.change_presence(activity=activity, status=discord.Status.online)

    async def on_error(self, event_method: str, *args: object, **kwargs: object) -> None:
        """Global error handler for event listeners.

        Logs the full traceback with structured context.
        """
        logger.error(
            "bot.event.error",
            event=event_method,
            traceback=traceback.format_exc(),
        )

    async def close(self) -> None:
        """Graceful shutdown: close database, Redis, then disconnect from Discord."""
        logger.info("bot.shutdown.start")

        # Close Redis
        if self.redis is not None:
            await self.redis.close()
            logger.info("bot.redis.disconnected")

        # Close database
        await self.db.close()
        logger.info("bot.database.disconnected")

        # Close Discord connection
        await super().close()
        logger.info("bot.shutdown.complete")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _connect_redis(self) -> None:
        """Establish async Redis connection with connection pooling."""
        try:
            import redis.asyncio as aioredis

            self.redis = aioredis.from_url(
                self.settings.redis_url,
                max_connections=self.settings.redis_max_connections,
                decode_responses=True,
                health_check_interval=30,
            )
            # Verify connection
            await self.redis.ping()
            logger.info("bot.redis.connected", url=self.settings.redis_url)
        except Exception:
            logger.warning(
                "bot.redis.connection_failed",
                url=self.settings.redis_url,
                message="Redis is not available. Caching will be disabled.",
            )
            self.redis = None

    async def _load_all_cogs(self) -> None:
        """Dynamically discover and load all cog extensions from bot/cogs/.

        Each subdirectory in cogs/ is expected to be a Python package with
        an __init__.py that contains an async setup() function.

        Directory structure:
            bot/cogs/
                moderation/
                    __init__.py   <- must have async def setup(bot)
                    moderation.py
                automod/
                    __init__.py
                    automod.py
                ...
        """
        cogs_dir = Path(__file__).parent.parent / "cogs"

        if not cogs_dir.exists():
            logger.warning("bot.cogs.directory_missing", path=str(cogs_dir))
            return

        loaded = 0
        failed = 0

        for entry in sorted(cogs_dir.iterdir()):
            if not entry.is_dir():
                continue
            if entry.name.startswith("_"):
                continue

            # Check for __init__.py
            init_file = entry / "__init__.py"
            if not init_file.exists():
                continue

            extension_name = f"bot.cogs.{entry.name}"
            try:
                await self.load_extension(extension_name)
                loaded += 1
                logger.info("bot.cog.loaded", cog=entry.name)
            except Exception:
                failed += 1
                logger.error(
                    "bot.cog.load_failed",
                    cog=entry.name,
                    traceback=traceback.format_exc(),
                )

        logger.info("bot.cogs.load_complete", loaded=loaded, failed=failed)

    async def get_or_fetch_member(
        self, guild: discord.Guild, member_id: int
    ) -> discord.Member | None:
        """Get a member from cache or fetch from API.

        Args:
            guild: The guild to search in.
            member_id: The Discord user ID.

        Returns:
            The Member if found, None otherwise.
        """
        member = guild.get_member(member_id)
        if member is not None:
            return member
        try:
            return await guild.fetch_member(member_id)
        except discord.NotFound:
            return None

    async def get_or_fetch_user(self, user_id: int) -> discord.User | None:
        """Get a user from cache or fetch from API.

        Args:
            user_id: The Discord user ID.

        Returns:
            The User if found, None otherwise.
        """
        user = self.get_user(user_id)
        if user is not None:
            return user
        try:
            return await self.fetch_user(user_id)
        except discord.NotFound:
            return None

    @property
    def uptime_seconds(self) -> float:
        """Get the bot's uptime in seconds since on_ready."""
        import time

        if self.start_time == 0.0:
            return 0.0
        return time.time() - self.start_time
