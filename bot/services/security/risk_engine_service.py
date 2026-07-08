"""Risk Engine for evaluating overall server security health."""

from __future__ import annotations

import discord

from bot.database.schemas.security import SecuritySettings


class RiskEngineService:
    """Evaluates and calculates risk scores for the server."""

    @staticmethod
    def calculate_health_score(guild: discord.Guild, settings: SecuritySettings) -> int:
        """Calculate a security health score out of 100.

        Evaluates server configuration, enabled rules, and dangerous permissions.
        """
        score = 100

        # Penalty: Security system disabled
        if not settings.enabled:
            return 0

        # Check Anti-Nuke modules
        if not settings.anti_nuke.enabled:
            score -= 30
        else:
            # Check individual crucial rules
            if not settings.anti_nuke.channel_delete.enabled:
                score -= 5
            if not settings.anti_nuke.role_delete.enabled:
                score -= 5
            if not settings.anti_nuke.member_ban.enabled:
                score -= 10

        # Check Anti-Raid modules
        if not settings.anti_raid.enabled:
            score -= 20
        else:
            if not settings.anti_raid.mass_join.enabled:
                score -= 10
            if not settings.anti_raid.invite_spam.enabled:
                score -= 5

        # Check Discord Server features
        if "COMMUNITY" not in guild.features:
            score -= 5  # Missing community features

        if guild.verification_level == discord.VerificationLevel.none:
            score -= 10  # No verification required
        elif guild.verification_level == discord.VerificationLevel.low:
            score -= 5

        if guild.explicit_content_filter != discord.ContentFilter.all_members:
            score -= 5

        # Analyze roles with dangerous permissions (excluding bots and admins)
        dangerous_perms = [
            "administrator",
            "manage_guild",
            "manage_roles",
            "manage_channels",
            "ban_members",
        ]
        risky_roles_count = 0

        for role in guild.roles:
            if role.is_default() or role.managed:
                continue

            has_dangerous = any(getattr(role.permissions, perm, False) for perm in dangerous_perms)
            if has_dangerous:
                risky_roles_count += 1

        # Deduct points for excessive amounts of administrative roles
        if risky_roles_count > 5:
            score -= (risky_roles_count - 5) * 2

        return max(0, min(100, score))
