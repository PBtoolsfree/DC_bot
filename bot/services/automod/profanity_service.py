"""Profanity and content filtering service for AutoMod.

Handles detection of bad words, regex patterns, Zalgo text,
invisible characters, and Unicode abuse.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, ClassVar

import discord

from bot.utils.logger import get_logger

if TYPE_CHECKING:
    from bot.database.schemas.automod import AutoModSettings, RuleConfig

logger = get_logger(__name__)


class ProfanityService:
    """Service for content filtering and profanity detection."""

    # Common leetspeak replacements
    LEET_MAP: ClassVar[dict[str, str]] = {
        "0": "o",
        "1": "i",
        "3": "e",
        "4": "a",
        "5": "s",
        "7": "t",
        "8": "b",
        "@": "a",
        "$": "s",
        "!": "i",
        "()": "o",
    }

    # Matches Zalgo combining characters
    ZALGO_REGEX = re.compile(r"[\u0300-\u036F\u0483-\u0489\u1DC0-\u1DFF\u20D0-\u20FF\uFE20-\uFE2F]")

    # Matches zero-width and invisible characters
    INVISIBLE_REGEX = re.compile(
        r"[\u200B-\u200F\u202A-\u202E\u2060-\u206F\uFEFF\u2800\u3164\uFFA0]"
    )

    @classmethod
    def _normalize_text(cls, text: str) -> str:
        """Normalize text by converting to lowercase, removing spaces, and translating leetspeak."""
        # 1. Lowercase
        text = text.lower()
        # 2. Translate leetspeak
        for leet, normal in cls.LEET_MAP.items():
            text = text.replace(leet, normal)
        # 3. Strip whitespace and punctuation
        return re.sub(r"[\W_]+", "", text)

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

    async def check_message(
        self, message: discord.Message, settings: AutoModSettings
    ) -> str | None:
        """Evaluate a message against all content filtering rules.

        Returns the name of the triggered rule (e.g., "words_profanity", "abuse_zalgo"),
        or None if no rules were violated.
        """
        content = message.content
        if not content:
            return None

        # 1. Zalgo Check
        if (
            settings.abuse_zalgo.enabled
            and not self._check_ignored(message, settings.abuse_zalgo)
            and len(self.ZALGO_REGEX.findall(content)) > (settings.abuse_zalgo.threshold or 5)
        ):
            return "abuse_zalgo"

        # 2. Invisible Character Check
        if (
            settings.abuse_invisible.enabled
            and not self._check_ignored(message, settings.abuse_invisible)
            and self.INVISIBLE_REGEX.search(content)
        ):
            return "abuse_invisible"

        # 3. Unicode Abuse (Non-ASCII characters beyond a threshold)
        if settings.abuse_unicode.enabled and not self._check_ignored(
            message, settings.abuse_unicode
        ):
            ascii_count = sum(1 for char in content if ord(char) < 128)
            ratio = ascii_count / len(content) if content else 1
            if ratio < (settings.abuse_unicode.threshold or 50) / 100.0:  # threshold is percentage
                return "abuse_unicode"

        # 4. Regex Filter
        if settings.words_regex.enabled and not self._check_ignored(message, settings.words_regex):
            for pattern in settings.words_regex.blacklist:
                try:
                    if re.search(pattern, content, re.IGNORECASE):
                        return "words_regex"
                except re.error as e:
                    logger.warning("invalid_automod_regex", pattern=pattern, error=str(e))

        # 5. Profanity & Custom Words
        normalized_content = self._normalize_text(content)

        if settings.words_profanity.enabled and not self._check_ignored(
            message, settings.words_profanity
        ):
            # Check whitelist first
            if any(word in normalized_content for word in settings.words_profanity.whitelist):
                pass
            elif any(word in normalized_content for word in settings.words_profanity.blacklist):
                return "words_profanity"

        if settings.words_custom.enabled and not self._check_ignored(
            message, settings.words_custom
        ):
            if any(word in normalized_content for word in settings.words_custom.whitelist):
                pass
            elif any(word in normalized_content for word in settings.words_custom.blacklist):
                return "words_custom"

        return None
