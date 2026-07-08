"""Service for managing security whitelists."""

from __future__ import annotations

import discord
from bot.database.schemas.security import WhitelistConfig


class WhitelistService:
    """Handles logic for determining if users/bots bypass security rules."""

    @staticmethod
    def is_exempt(
        member: discord.Member, 
        whitelist: WhitelistConfig,
        bot_owner_ids: set[int] | None = None
    ) -> bool:
        """Check if a member is fully exempt from security checks."""
        # Bot owners and server owner always exempt
        if bot_owner_ids and member.id in bot_owner_ids:
            return True
        if member.id == member.guild.owner_id:
            return True

        # Check explicit user whitelist
        if member.id in whitelist.users:
            return True

        # Check bot whitelist
        if member.bot and member.id in whitelist.bots:
            return True

        # Check role whitelist
        member_role_ids = {role.id for role in member.roles}
        if any(role_id in whitelist.roles for role_id in member_role_ids):
            return True

        return False
