"""Autorole Service."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import discord

from bot.database.models.welcome import AutoRoleSettings
from bot.services.logging.streaming_service import StreamingService


class AutoRoleService:
    """Handles automatically assigning roles upon join."""

    @staticmethod
    async def process_instant_roles(session: AsyncSession, member: discord.Member) -> None:
        """Assigns roles that have 0 delay."""
        stmt = select(AutoRoleSettings).where(AutoRoleSettings.guild_id == member.guild.id, AutoRoleSettings.delay_seconds == 0)
        result = await session.execute(stmt)
        configs = result.scalars().all()
        
        roles_to_add = []
        for config in configs:
            # Check target
            if config.target == "human" and member.bot:
                continue
            if config.target == "bot" and not member.bot:
                continue
                
            # Verification dependency is handled in Module 7 hooks (if verified -> apply delayed autorole)
            if config.requires_verification:
                continue # Skip for now, Mod 7 will trigger us later
                
            role = member.guild.get_role(config.role_id)
            if role:
                roles_to_add.append(role)
                
        if roles_to_add:
            try:
                await member.add_roles(*roles_to_add, reason="Autorole Instant")
                
                for role in roles_to_add:
                    await StreamingService.broadcast(
                        guild_id=member.guild.id,
                        event_type="ROLE_GRANTED",
                        payload={"user_id": str(member.id), "role_id": str(role.id), "reason": "Autorole"}
                    )
            except discord.HTTPException:
                pass
