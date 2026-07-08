"""Link and URL filtering service for AutoMod.

Handles Discord invite detection, external link blocking,
whitelists/blacklists, and scam domain detection.
"""

from __future__ import annotations

import re
from typing import ClassVar
from urllib.parse import urlparse

import discord

from bot.database.schemas.automod import AutoModSettings, RuleConfig
from bot.utils.logger import get_logger

logger = get_logger(__name__)


class LinkService:
    """Service for parsing and filtering URLs and Discord Invites."""

    # Extracts URLs from text
    URL_REGEX = re.compile(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    )
    
    # Matches any Discord invite link
    INVITE_REGEX = re.compile(
        r"(?:https?://)?(?:www\.)?(?:discord\.(?:gg|io|me|li)|discord(?:app)?\.com/invite)/([a-zA-Z0-9-]+)"
    )

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

    @classmethod
    def _extract_domains(cls, content: str) -> set[str]:
        """Extract unique domains from a message content."""
        domains = set()
        urls = cls.URL_REGEX.findall(content)
        for url in urls:
            try:
                parsed = urlparse(url)
                if parsed.netloc:
                    domain = parsed.netloc.lower()
                    if domain.startswith("www."):
                        domain = domain[4:]
                    domains.add(domain)
            except Exception:
                pass
        return domains

    async def check_message(self, message: discord.Message, settings: AutoModSettings) -> str | None:
        """Evaluate a message against all link filtering rules.
        
        Returns the name of the triggered rule (e.g., "links_invites"),
        or None if no rules were violated.
        """
        content = message.content
        if not content:
            return None

        # 1. Discord Invites
        if settings.links_invites.enabled and not self._check_ignored(message, settings.links_invites):
            invites = self.INVITE_REGEX.findall(content)
            if invites:
                # Check whitelist (guild IDs or invite codes)
                for invite in invites:
                    if invite not in settings.links_invites.whitelist:
                        return "links_invites"

        # 2. Scam/Phishing Detection
        domains = self._extract_domains(content)
        if not domains:
            return None

        if settings.links_scam.enabled and not self._check_ignored(message, settings.links_scam):
            for domain in domains:
                if domain in settings.links_scam.blacklist:
                    return "links_scam"

        if settings.links_phishing.enabled and not self._check_ignored(message, settings.links_phishing):
            for domain in domains:
                if domain in settings.links_phishing.blacklist:
                    return "links_phishing"
                    
        if settings.links_fake_giveaways.enabled and not self._check_ignored(message, settings.links_fake_giveaways):
            for domain in domains:
                if domain in settings.links_fake_giveaways.blacklist:
                    return "links_fake_giveaways"

        # 3. External Links General
        if settings.links_external.enabled and not self._check_ignored(message, settings.links_external):
            for domain in domains:
                # If whitelist is populated, ONLY those are allowed
                if settings.links_external.whitelist:
                    if domain not in settings.links_external.whitelist:
                        return "links_external"
                # Check blacklist
                if domain in settings.links_external.blacklist:
                    return "links_external"
                # If it's enabled and no whitelist/blacklist is defined, it might block ALL links
                if not settings.links_external.whitelist and not settings.links_external.blacklist:
                    return "links_external"

        return None
