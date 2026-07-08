"""Security listener cog for monitoring gateway events."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from bot.database.repositories.guild_repo import GuildRepository
from bot.database.schemas.security import SecuritySettings
from bot.services.security.audit_service import AuditService
from bot.services.security.security_service import SecurityService
from bot.utils.logger import get_logger

if TYPE_CHECKING:
    from bot.core.bot import ManagementBot

logger = get_logger(__name__)


class SecurityListenerCog(commands.Cog):
    """Listens to Discord gateway events to detect security incidents."""

    def __init__(self, bot: ManagementBot) -> None:
        self.bot = bot
        self.audit_service = AuditService()
        self.security_service = SecurityService(bot.redis_service, set(bot.settings.bot_owner_ids))

    async def _handle_security_event(
        self,
        guild: discord.Guild,
        action_type: str,
        audit_action: discord.AuditLogAction,
        target_id: int | None = None,
    ) -> None:
        """Centralized handler for processing security events."""
        if not guild.me.guild_permissions.view_audit_log:
            return

        async with self.bot.db.session() as session:
            settings_db = await GuildRepository.get_module_settings(session, guild.id, "security")
            if not settings_db or not settings_db.enabled:
                return

            settings = SecuritySettings.from_dict(settings_db.config)

            # Fetch the audit log entry to identify the executor
            audit_entry = await self.audit_service.find_recent_action(
                guild=guild, action=audit_action, target_id=target_id, time_window_seconds=10
            )

            if not audit_entry or not audit_entry.user:
                return

            executor = guild.get_member(audit_entry.user.id)
            if not executor:
                return

            await self.security_service.handle_action(
                session=session,
                guild=guild,
                settings=settings,
                action_type=action_type,
                executor=executor,
                target_id=target_id,
                audit_entry=audit_entry,
            )

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel) -> None:
        """Handle channel creation events."""
        await self._handle_security_event(
            channel.guild, "channel_create", discord.AuditLogAction.channel_create, channel.id
        )

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        """Handle channel deletion events."""
        await self._handle_security_event(
            channel.guild, "channel_delete", discord.AuditLogAction.channel_delete, channel.id
        )

    @commands.Cog.listener()
    async def on_guild_channel_update(
        self, _before: discord.abc.GuildChannel, after: discord.abc.GuildChannel
    ) -> None:
        """Handle channel update events."""
        await self._handle_security_event(
            after.guild, "channel_update", discord.AuditLogAction.channel_update, after.id
        )

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role) -> None:
        """Handle role creation events."""
        await self._handle_security_event(
            role.guild, "role_create", discord.AuditLogAction.role_create, role.id
        )

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role) -> None:
        """Handle role deletion events."""
        await self._handle_security_event(
            role.guild, "role_delete", discord.AuditLogAction.role_delete, role.id
        )

    @commands.Cog.listener()
    async def on_guild_role_update(self, _before: discord.Role, after: discord.Role) -> None:
        """Handle role update events."""
        await self._handle_security_event(
            after.guild, "role_update", discord.AuditLogAction.role_update, after.id
        )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Handle member join events for Anti-Raid."""
        if member.bot:
            # Bot add event
            await self._handle_security_event(
                member.guild, "anti_raid_bot_add", discord.AuditLogAction.bot_add, member.id
            )
            return

        async with self.bot.db.session() as session:
            settings_db = await GuildRepository.get_module_settings(
                session, member.guild.id, "security"
            )
            if not settings_db or not settings_db.enabled:
                return

            settings = SecuritySettings.from_dict(settings_db.config)

            # For mass joins, the executor is conceptually the guild itself tracking joins over time
            # So we pass the guild owner as a placeholder executor to the velocity check,
            # though it doesn't matter for global guild thresholds
            exceeded = await self.security_service.raid_service.add_action_and_check(
                guild_id=member.guild.id,
                action_type="anti_raid_mass_join",
                rule=settings.anti_raid.mass_join,
                target_id=None,  # Global counter
            )

            if exceeded:
                # Trigger raid lockdown
                # For raid defense, punishment usually means banning the recently joined members
                # or enabling verification
                pass  # Implementation specific to Raid protocol
