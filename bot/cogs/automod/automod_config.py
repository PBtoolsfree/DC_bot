"""AutoMod configuration commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from bot.database.repositories.guild_repo import GuildRepository
from bot.database.schemas.automod import AutoModSettings
from bot.utils.embed_builder import EmbedBuilder
from bot.utils.permissions import PermissionLevel, require_permission

if TYPE_CHECKING:
    from bot.core.bot import ManagementBot


class AutoModConfigCog(commands.GroupCog, name="automod"):
    """Cog for AutoMod configuration commands."""

    def __init__(self, bot: ManagementBot) -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(name="status", description="View the current AutoMod status.")
    @require_permission(PermissionLevel.ADMIN)
    async def status(self, interaction: discord.Interaction) -> None:
        """View the current AutoMod status."""
        assert interaction.guild is not None
        
        await interaction.response.defer(ephemeral=True)

        async with self.bot.db.session() as session:
            settings_db = await GuildRepository.get_module_settings(
                session, interaction.guild.id, "automod"
            )

        if not settings_db or not settings_db.enabled:
            embed = EmbedBuilder.error(
                description="AutoMod is currently **Disabled**.",
                title="AutoMod Status"
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        settings = AutoModSettings.from_dict(settings_db.config)
        
        # Build status overview
        spam_status = "✅ Enabled" if settings.spam_messages.enabled else "❌ Disabled"
        links_status = "✅ Enabled" if settings.links_external.enabled else "❌ Disabled"
        words_status = "✅ Enabled" if settings.words_profanity.enabled else "❌ Disabled"

        embed = EmbedBuilder.info(
            description="AutoMod is currently **Enabled**.",
            title="AutoMod Status"
        )
        embed.add_field(name="Spam Filter", value=spam_status, inline=True)
        embed.add_field(name="Link Filter", value=links_status, inline=True)
        embed.add_field(name="Profanity Filter", value=words_status, inline=True)

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="toggle", description="Enable or disable the entire AutoMod system.")
    @require_permission(PermissionLevel.SERVER_OWNER)
    @app_commands.choices(state=[
        app_commands.Choice(name="Enable", value="enable"),
        app_commands.Choice(name="Disable", value="disable"),
    ])
    async def toggle(
        self, 
        interaction: discord.Interaction, 
        state: app_commands.Choice[str]
    ) -> None:
        """Enable or disable AutoMod globally for the server."""
        assert interaction.guild is not None
        
        await interaction.response.defer(ephemeral=True)
        
        enabled = state.value == "enable"

        async with self.bot.db.session() as session:
            # We initialize a default AutoModSettings if it doesn't exist
            default_config = AutoModSettings().model_dump()
            
            await GuildRepository.get_or_create_module_settings(
                session, interaction.guild.id, "automod", default_config
            )
            
            await GuildRepository.update_module_settings(
                session, interaction.guild.id, "automod", enabled=enabled
            )

        # We should ideally clear the redis cache here to apply instantly
        # but the cache TTL is 5 minutes, which is acceptable for now.
        
        status_msg = "enabled" if enabled else "disabled"
        embed = EmbedBuilder.success(
            description=f"AutoMod has been successfully **{status_msg}**.",
            title="AutoMod Toggled"
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
