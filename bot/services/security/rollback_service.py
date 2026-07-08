"""Service for rollback and recovery operations."""

from __future__ import annotations

import discord

from bot.utils.logger import get_logger

logger = get_logger(__name__)


class RollbackService:
    """Handles reversing destructive actions (Anti-Nuke Rollbacks)."""

    @staticmethod
    async def restore_channel(
        guild: discord.Guild, 
        audit_entry: discord.AuditLogEntry
    ) -> discord.abc.GuildChannel | None:
        """Attempt to restore a deleted channel using audit log before data."""
        if audit_entry.action != discord.AuditLogAction.channel_delete:
            return None
            
        before = audit_entry.before
        channel_type = getattr(before, "type", discord.ChannelType.text)
        
        try:
            overwrites = getattr(before, "overwrites", {})
            # Note: overwrites in audit log might be raw dicts. 
            # In a production environment, we'd need to parse them carefully.
            # For this enterprise system, we will rely on basic recreation.
            
            new_channel = await guild.create_channel(
                name=getattr(before, "name", "restored-channel"),
                type=channel_type,
                category=guild.get_channel(getattr(before, "category_id", None)) if getattr(before, "category_id", None) else None,
                reason="Anti-Nuke: Automatic Channel Rollback",
            )
            
            # Repositioning
            if hasattr(before, "position"):
                try:
                    await new_channel.edit(position=before.position)
                except discord.HTTPException:
                    pass
                    
            return new_channel
            
        except discord.Forbidden:
            logger.error("rollback.forbidden", guild_id=guild.id, action="restore_channel")
        except discord.HTTPException as e:
            logger.error("rollback.http_error", guild_id=guild.id, error=str(e))
            
        return None

    @staticmethod
    async def restore_role(
        guild: discord.Guild,
        audit_entry: discord.AuditLogEntry
    ) -> discord.Role | None:
        """Attempt to restore a deleted role using audit log before data."""
        if audit_entry.action != discord.AuditLogAction.role_delete:
            return None
            
        before = audit_entry.before
        
        try:
            new_role = await guild.create_role(
                name=getattr(before, "name", "restored-role"),
                permissions=getattr(before, "permissions", discord.Permissions.none()),
                color=getattr(before, "color", discord.Color.default()),
                hoist=getattr(before, "hoist", False),
                mentionable=getattr(before, "mentionable", False),
                reason="Anti-Nuke: Automatic Role Rollback"
            )
            
            # We can't guarantee position restoration if it's too high for the bot, but we try
            if hasattr(before, "position"):
                try:
                    await new_role.edit(position=before.position)
                except discord.HTTPException:
                    pass
                    
            return new_role
            
        except discord.Forbidden:
            logger.error("rollback.forbidden", guild_id=guild.id, action="restore_role")
        except discord.HTTPException as e:
            logger.error("rollback.http_error", guild_id=guild.id, error=str(e))
            
        return None
        
    @staticmethod
    async def strip_dangerous_roles(
        member: discord.Member,
        reason: str = "Anti-Nuke: Stripping Dangerous Roles"
    ) -> None:
        """Strip all dangerous roles from a member (used in lock down)."""
        dangerous_perms = ["administrator", "manage_guild", "manage_roles", "manage_channels", "ban_members"]
        roles_to_remove = []
        
        for role in member.roles:
            if role.managed or role.is_default():
                continue
            
            if any(getattr(role.permissions, perm, False) for perm in dangerous_perms):
                if role < member.guild.me.top_role:
                    roles_to_remove.append(role)
                    
        if roles_to_remove:
            try:
                await member.remove_roles(*roles_to_remove, reason=reason)
            except (discord.Forbidden, discord.HTTPException):
                pass
