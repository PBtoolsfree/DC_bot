"""XP Service."""

import discord
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.xp import UserXP, XPReward
from bot.services.logging.streaming_service import StreamingService
from bot.services.xp.providers.message_provider import MessageXPProvider


class XPService:
    """Orchestrates XP Providers and handles Level Ups."""

    def __init__(self) -> None:
        self.message_provider = MessageXPProvider()

    def _calculate_level(self, total_xp: int) -> int:
        """Standard curve: 5 * (lvl ^ 2) + 50 * lvl + 100 xp per level roughly, or simple linear.
        Using simple linear/quadratic mix for demo."""
        # Level 1 = 100 XP, Level 2 = 255 XP, Level 3 = 475 XP
        level = 0
        while total_xp >= (5 * (level**2) + 50 * level + 100):
            total_xp -= 5 * (level**2) + 50 * level + 100
            level += 1
        return level

    async def handle_message(self, session: AsyncSession, message: discord.Message) -> None:
        """Passes the message to the MessageXPProvider."""

        event_data = {
            "guild_id": message.guild.id,
            "user_id": message.author.id,
            "channel_id": message.channel.id,
        }

        xp_gained = await self.message_provider.process_event(session, event_data)

        if xp_gained > 0:
            # Check for level up
            await self._check_level_up(session, message.guild, message.author)
            await StreamingService.broadcast(
                guild_id=message.guild.id,
                event_type="XP_GAINED",
                payload={
                    "user_id": str(message.author.id),
                    "amount": xp_gained,
                    "source": "message",
                },
            )

    async def _check_level_up(
        self, session: AsyncSession, guild: discord.Guild, member: discord.Member
    ) -> None:
        stmt = select(UserXP).where(UserXP.guild_id == guild.id, UserXP.user_id == member.id)
        user_xp = (await session.execute(stmt)).scalar_one_or_none()

        if not user_xp:
            return

        new_level = self._calculate_level(user_xp.xp)
        if new_level > user_xp.level:
            user_xp.level = new_level

            # Announce
            await StreamingService.broadcast(
                guild_id=guild.id,
                event_type="LEVEL_UP",
                payload={"user_id": str(member.id), "new_level": new_level},
            )

            # Apply Rewards
            stmt_rew = select(XPReward).where(
                XPReward.guild_id == guild.id, XPReward.level == new_level
            )
            rewards = (await session.execute(stmt_rew)).scalars().all()

            roles_to_add = []
            for rew in rewards:
                r = guild.get_role(rew.role_id)
                if r:
                    roles_to_add.append(r)

            if roles_to_add:
                try:
                    await member.add_roles(*roles_to_add, reason=f"Level {new_level} Reward")
                except discord.HTTPException:
                    pass
