"""Spam detection service for AutoMod.

Handles rate limiting, message floods, duplicate detection,
caps filter, emoji spam, mention spam, and attachment spam.
Relies heavily on RedisService for cross-instance state and limits.
"""

from __future__ import annotations

import hashlib
import re
from typing import TYPE_CHECKING

import discord

from bot.utils.logger import get_logger

if TYPE_CHECKING:
    from bot.database.schemas.automod import AutoModSettings, RuleConfig
    from bot.services.redis_service import RedisService

logger = get_logger(__name__)


class SpamService:
    """Service for detecting various forms of spam using Redis sliding windows."""

    # Matches standard Unicode emojis
    EMOJI_REGEX = re.compile(r"[\U00010000-\U0010ffff]", flags=re.UNICODE)
    # Matches custom Discord emojis
    CUSTOM_EMOJI_REGEX = re.compile(r"<a?:[a-zA-Z0-9_]+:[0-9]+>")

    def __init__(self, redis: RedisService) -> None:
        self.redis = redis

    @classmethod
    def _check_ignored(cls, message: discord.Message, rule: RuleConfig) -> bool:
        """Check if the message author/channel is exempt from the rule."""
        if message.author.id in rule.ignored_users:
            return True
        if message.channel.id in rule.ignored_channels:
            return True
        if getattr(message.channel, "category_id", None) in rule.ignored_categories:
            return True

        if isinstance(message.author, discord.Member):
            author_roles = {role.id for role in message.author.roles}
            if any(role_id in rule.ignored_roles for role_id in author_roles):
                return True

        return False

    def _hash_content(self, content: str) -> str:
        """Create a consistent hash of message content for duplicate detection."""
        return hashlib.sha256(content.lower().strip().encode("utf-8")).hexdigest()

    async def check_message(
        self, message: discord.Message, settings: AutoModSettings
    ) -> str | None:
        """Evaluate a message against all spam filtering rules.

        Returns the name of the triggered rule (e.g., "spam_messages"),
        or None if no rules were violated.
        """
        content = message.content or ""
        guild_id = message.guild.id if message.guild else 0
        user_id = message.author.id

        # 1. Caps Filter
        if settings.spam_caps.enabled and not self._check_ignored(message, settings.spam_caps):
            # Only process messages longer than 10 chars
            alpha_chars = [c for c in content if c.isalpha()]
            if len(alpha_chars) > 10:
                caps_count = sum(1 for c in alpha_chars if c.isupper())
                ratio = caps_count / len(alpha_chars)
                # threshold is percentage (0-100)
                if ratio > (settings.spam_caps.threshold or 70) / 100.0:
                    return "spam_caps"

        # 2. Mention Spam (Single Message)
        if settings.spam_mentions.enabled and not self._check_ignored(
            message, settings.spam_mentions
        ):
            mention_count = len(message.raw_mentions) + len(message.raw_role_mentions)
            if mention_count > (settings.spam_mentions.threshold or 5):
                return "spam_mentions"

        # 3. Mass Mentions (Across Time Window)
        if settings.spam_mass_mentions.enabled and not self._check_ignored(
            message, settings.spam_mass_mentions
        ):
            mention_count = len(message.raw_mentions) + len(message.raw_role_mentions)
            if mention_count > 0:
                key = f"automod:mentions:{guild_id}:{user_id}"
                window = settings.spam_mass_mentions.cooldown_seconds or 10
                limit = settings.spam_mass_mentions.threshold or 10

                # Add mentions to bucket
                current = await self.redis.incr(key, amount=mention_count)
                if current == mention_count:
                    await self.redis.expire(key, window)

                if current > limit:
                    return "spam_mass_mentions"

        # 4. Emoji Spam
        if settings.spam_emojis.enabled and not self._check_ignored(message, settings.spam_emojis):
            unicode_emojis = len(self.EMOJI_REGEX.findall(content))
            custom_emojis = len(self.CUSTOM_EMOJI_REGEX.findall(content))
            total_emojis = unicode_emojis + custom_emojis

            if total_emojis > (settings.spam_emojis.threshold or 10):
                return "spam_emojis"

        # 5. Attachment/Media Spam
        if (
            settings.spam_attachments.enabled
            and not self._check_ignored(message, settings.spam_attachments)
            and len(message.attachments) > (settings.spam_attachments.threshold or 3)
        ):
            return "spam_attachments"

        # 6. Duplicate Messages (Rate limit on Content Hash)
        if (
            settings.spam_duplicates.enabled
            and content
            and not self._check_ignored(message, settings.spam_duplicates)
        ):
            content_hash = self._hash_content(content)
            key = f"automod:dupes:{guild_id}:{user_id}:{content_hash}"
            window = settings.spam_duplicates.cooldown_seconds or 60
            limit = settings.spam_duplicates.threshold or 3

            is_allowed = await self.redis.check_rate_limit(key, limit, window)
            if not is_allowed:
                return "spam_duplicates"

        # 7. Message Flood (Rate limit on User)
        if settings.spam_messages.enabled and not self._check_ignored(
            message, settings.spam_messages
        ):
            key = f"automod:flood:{guild_id}:{user_id}"
            window = settings.spam_messages.cooldown_seconds or 5
            limit = settings.spam_messages.threshold or 5

            is_allowed = await self.redis.check_rate_limit(key, limit, window)
            if not is_allowed:
                return "spam_messages"

        return None
