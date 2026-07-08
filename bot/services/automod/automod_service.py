"""Master AutoMod orchestrator service.

Coordinates spam, link, and profanity filtering.
Handles configuration fetching and triggering violations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.repositories.guild_repo import GuildRepository
from bot.database.schemas.automod import AutoModSettings
from bot.services.automod.link_service import LinkService
from bot.services.automod.profanity_service import ProfanityService
from bot.services.automod.spam_service import SpamService
from bot.services.automod.violation_service import ViolationService
from bot.services.redis_service import RedisService
from bot.utils.logger import get_logger

if TYPE_CHECKING:
    from bot.core.bot import ManagementBot

logger = get_logger(__name__)


class AutoModerationService:
    """Orchestrator for all auto-moderation logic."""

    def __init__(self, bot: ManagementBot, redis: RedisService) -> None:
        self.bot = bot
        self.redis = redis
        
        self.spam_service = SpamService(redis)
        self.link_service = LinkService()
        self.profanity_service = ProfanityService()
        self.violation_service = ViolationService(bot)

    async def _get_settings(self, session: AsyncSession, guild_id: int) -> AutoModSettings | None:
        """Fetch and parse AutoMod settings for a guild.
        
        Uses Redis to cache the parsed settings to avoid database hits on every message.
        """
        cache_key = f"cache:automod_config:{guild_id}"
        
        # 1. Check Redis Cache
        cached_data = await self.redis.get_json(cache_key)
        if cached_data is not None:
            if not cached_data.get("enabled", False):
                return None
            return AutoModSettings.from_dict(cached_data.get("config", {}))

        # 2. Fetch from Database
        db_settings = await GuildRepository.get_module_settings(session, guild_id, "automod")
        
        if not db_settings:
            # Cache the "not enabled" state for 60 seconds
            await self.redis.set_json(cache_key, {"enabled": False}, ex=60)
            return None

        # 3. Cache and Return
        await self.redis.set_json(
            cache_key, 
            {"enabled": db_settings.enabled, "config": db_settings.config}, 
            ex=300  # 5 minute cache TTL
        )

        if not db_settings.enabled:
            return None

        return AutoModSettings.from_dict(db_settings.config)

    async def process_message(self, session: AsyncSession, message: discord.Message) -> bool:
        """Process a message through all enabled AutoMod filters.
        
        Returns True if the message was processed and ALLOWED (or ignored),
        and False if a violation was triggered.
        """
        if message.author.bot or not message.guild:
            return True

        settings = await self._get_settings(session, message.guild.id)
        if not settings:
            return True

        # Process through filters in order of severity/speed
        
        # 1. Profanity & Content (Fastest, regex/string matching)
        violation_rule = await self.profanity_service.check_message(message, settings)
        
        # 2. Link Filtering (Parsing domains)
        if not violation_rule:
            violation_rule = await self.link_service.check_message(message, settings)
            
        # 3. Spam Detection (Requires Redis calls)
        if not violation_rule:
            violation_rule = await self.spam_service.check_message(message, settings)

        # Handle Violation
        if violation_rule:
            logger.info(
                "automod_violation_triggered",
                guild_id=message.guild.id,
                user_id=message.author.id,
                rule=violation_rule,
            )
            
            # Record stat in redis
            await self.redis.incr(f"stats:automod:violations:{message.guild.id}:{violation_rule}")
            
            await self.violation_service.handle_violation(
                session, message, violation_rule, settings
            )
            return False

        return True
