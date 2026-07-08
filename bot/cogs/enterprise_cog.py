"""Cog for Backup, Welcome, Reaction Roles, and XP (Modules 9-12)."""

import discord
from discord.ext import commands

from bot.database.core import db
from bot.services.welcome.autorole_service import AutoRoleService
from bot.services.welcome.welcome_service import WelcomeService
from bot.services.xp.voice_service import VoiceSessionService
from bot.services.xp.xp_service import XPService


class EnterpriseCog(commands.Cog):
    """Consolidated Event Listeners for Modules 9-12."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.welcome_service = WelcomeService()
        self.xp_service = XPService()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Handles Welcome and Instant Autoroles."""
        async with db.session() as session:
            await self.welcome_service.handle_member_join(session, member)
            await AutoRoleService.process_instant_roles(session, member)
            await session.commit()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Handles XP generation."""
        if message.author.bot or not message.guild:
            return

        async with db.session() as session:
            await self.xp_service.handle_message(session, message)
            await session.commit()

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ) -> None:
        """Tracks Voice XP sessions."""
        if member.bot:
            return

        # Left voice or muted
        if before.channel and (not after.channel or after.self_mute or after.server_mute):
            minutes = await VoiceSessionService.leave_voice(member.id)
            if minutes > 0:
                async with db.session() as session:
                    from bot.services.xp.providers.voice_provider import VoiceXPProvider

                    provider = VoiceXPProvider()
                    await provider.process_event(
                        session,
                        {"guild_id": member.guild.id, "user_id": member.id, "minutes": minutes},
                    )
                    await session.commit()

        # Joined voice and not muted
        elif after.channel and not before.channel and not after.self_mute and not after.server_mute:
            await VoiceSessionService.join_voice(member.id)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(EnterpriseCog(bot))
