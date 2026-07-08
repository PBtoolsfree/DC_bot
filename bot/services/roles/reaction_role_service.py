"""Reaction Role Service."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import discord

from bot.database.models.roles import ReactionRoleGroup, ReactionRoleItem
from bot.services.logging.streaming_service import StreamingService


class ReactionRoleService:
    """Handles logic, exclusivity, and limits for reaction/button roles."""

    @staticmethod
    async def toggle_role(session: AsyncSession, member: discord.Member, group_id: int, role_id: int) -> tuple[bool, str]:
        """Toggles a role based on the group constraints."""
        
        stmt = select(ReactionRoleGroup).where(ReactionRoleGroup.id == group_id)
        group = (await session.execute(stmt)).scalar_one_or_none()
        
        if not group:
            return False, "Configuration not found."
            
        role = member.guild.get_role(role_id)
        if not role:
            return False, "Role no longer exists in the server."
            
        # 1. Check requirements
        if group.required_roles:
            user_role_ids = [r.id for r in member.roles]
            has_req = any(req in user_role_ids for req in group.required_roles)
            if not has_req:
                return False, "You do not have the required role to use this."
                
        # 2. Check blacklists
        if group.blacklisted_roles:
            user_role_ids = [r.id for r in member.roles]
            has_blacklisted = any(blk in user_role_ids for blk in group.blacklisted_roles)
            if has_blacklisted:
                return False, "You have a blacklisted role preventing this."
                
        # Is the user trying to remove it?
        if role in member.roles:
            # Check minimums
            if group.min_roles > 0:
                # Need to check how many roles from this group the user has
                stmt_items = select(ReactionRoleItem.role_id).where(ReactionRoleItem.group_id == group_id)
                group_role_ids = (await session.execute(stmt_items)).scalars().all()
                user_group_roles_count = sum(1 for r in member.roles if r.id in group_role_ids)
                
                if user_group_roles_count <= group.min_roles:
                    return False, f"You must have at least {group.min_roles} role(s) from this group."
                    
            await member.remove_roles(role, reason="Reaction Role toggle")
            await StreamingService.broadcast(
                guild_id=member.guild.id,
                event_type="ROLE_REMOVED",
                payload={"user_id": str(member.id), "role_id": str(role.id)}
            )
            return True, f"Removed {role.name}."
            
        else:
            # Check maximums
            stmt_items = select(ReactionRoleItem.role_id).where(ReactionRoleItem.group_id == group_id)
            group_role_ids = (await session.execute(stmt_items)).scalars().all()
            
            user_group_roles = [r for r in member.roles if r.id in group_role_ids]
            
            if group.max_roles > 0 and len(user_group_roles) >= group.max_roles:
                # If it's a single choice (max=1) and they select another, we might want to swap it.
                # For this implementation, we just block them.
                if group.max_roles == 1:
                    # Auto swap
                    await member.remove_roles(*user_group_roles, reason="Reaction Role swap")
                else:
                    return False, f"You can only have up to {group.max_roles} role(s) from this group."
                    
            await member.add_roles(role, reason="Reaction Role toggle")
            await StreamingService.broadcast(
                guild_id=member.guild.id,
                event_type="ROLE_GRANTED",
                payload={"user_id": str(member.id), "role_id": str(role.id)}
            )
            return True, f"Added {role.name}."
