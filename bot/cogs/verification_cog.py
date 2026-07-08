"""Verification Cog."""

import discord
from discord.ext import commands

from bot.database.core import db
from bot.database.repositories.verification_repo import VerificationRepository
from bot.services.verification.verification_service import VerificationService
from bot.ui.verification_views import VerificationView
from bot.utils.localization import locales


class VerificationCog(commands.Cog):
    """Cog for the Verification system."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.service = VerificationService()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Trigger quarantine if enabled."""
        async with db.session() as session:
            settings = await VerificationRepository.get_settings(session, member.guild.id)
            if not settings or not settings.enabled:
                return
                
            # If quarantine is enabled, assign the role immediately
            if settings.quarantine_role_id:
                role = member.guild.get_role(settings.quarantine_role_id)
                if role:
                    try:
                        await member.add_roles(role, reason="Quarantine on Join")
                    except discord.HTTPException:
                        pass
                        
            # If auto-verify is configured instead of button, we can initiate it here
            # For Button, the user must click the button in the channel

    @discord.app_commands.command(name="verify_setup", description="Deploy the verification panel.")
    @discord.app_commands.default_permissions(administrator=True)
    async def verify_setup(self, interaction: discord.Interaction) -> None:
        """Deploy the verification embed and button."""
        await interaction.response.defer(ephemeral=True)
        
        async with db.session() as session:
            settings = await VerificationRepository.get_settings(session, interaction.guild_id)
            if not settings or not settings.enabled:
                await interaction.followup.send("Please enable Verification in the Dashboard first.")
                return
                
        embed = discord.Embed(
            title=locales.get_string(settings.language, "verification", "BUTTON_VERIFICATION_TITLE", fallback="Server Verification"),
            description=locales.get_string(settings.language, "verification", "BUTTON_VERIFICATION_DESC", fallback="Click the button below to verify."),
            color=discord.Color.blue()
        )
        
        view = VerificationView(language=settings.language)
        await interaction.channel.send(embed=embed, view=view)
        await interaction.followup.send("Verification panel deployed.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VerificationCog(bot))
