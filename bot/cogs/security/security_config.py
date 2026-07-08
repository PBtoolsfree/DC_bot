"""Security configuration cog for slash commands."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from bot.core.bot import ManagementBot
from bot.database.repositories.guild_repo import GuildRepository
from bot.database.schemas.security import SecuritySettings
from bot.services.security.risk_engine_service import RiskEngineService
from bot.services.security.snapshot_service import SnapshotService
from bot.utils.embed_builder import EmbedBuilder
from bot.utils.permissions import PermissionLevel, require_permission


@app_commands.default_permissions(administrator=True)
class SecurityConfigCog(commands.GroupCog, group_name="security"):
    """Configure the Security and Anti-Nuke system."""

    def __init__(self, bot: ManagementBot) -> None:
        self.bot = bot

    @app_commands.command(
        name="status", description="View the current security status and health score"
    )
    @require_permission(PermissionLevel.ADMIN)
    async def status(self, interaction: discord.Interaction) -> None:
        """View the security system status."""
        if not interaction.guild:
            return

        await interaction.response.defer(ephemeral=True)

        async with self.bot.db.session() as session:
            settings_db = await GuildRepository.get_module_settings(
                session, interaction.guild.id, "security"
            )

        if not settings_db or not settings_db.enabled:
            embed = EmbedBuilder.error(
                description="The Security System is currently **Disabled**.",
                title="Security Status",
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        settings = SecuritySettings.from_dict(settings_db.config)

        # Calculate Risk Score
        health_score = RiskEngineService.calculate_health_score(interaction.guild, settings)

        if health_score >= 80:
            color = discord.Color.green()
            health_desc = "Excellent"
        elif health_score >= 50:
            color = discord.Color.gold()
            health_desc = "Moderate Risk"
        else:
            color = discord.Color.red()
            health_desc = "Critical Risk"

        embed = discord.Embed(
            title="🛡️ Security Dashboard",
            description="Overview of the current active security modules.",
            color=color,
        )

        embed.add_field(
            name="Health Score", value=f"**{health_score}/100** ({health_desc})", inline=False
        )

        anti_nuke_status = "✅ Enabled" if settings.anti_nuke.enabled else "❌ Disabled"
        anti_raid_status = "✅ Enabled" if settings.anti_raid.enabled else "❌ Disabled"
        sim_status = "✅ Active" if settings.simulation_mode.enabled else "❌ Inactive"

        embed.add_field(name="Anti-Nuke", value=anti_nuke_status, inline=True)
        embed.add_field(name="Anti-Raid", value=anti_raid_status, inline=True)
        embed.add_field(name="Simulation Mode", value=sim_status, inline=True)

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(
        name="snapshot", description="Create a manual backup snapshot of the server"
    )
    @require_permission(PermissionLevel.ADMIN)
    async def snapshot(self, interaction: discord.Interaction, name: str | None = None) -> None:
        """Create a server snapshot."""
        if not interaction.guild:
            return

        await interaction.response.defer(ephemeral=True)

        try:
            async with self.bot.db.session() as session:
                await SnapshotService.save_snapshot(
                    session=session,
                    guild=interaction.guild,
                    created_by=interaction.user,
                    name=name,
                    is_auto=False,
                )

            embed = EmbedBuilder.success(
                description="Server snapshot has been successfully created and stored.",
                title="Snapshot Created",
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            embed = EmbedBuilder.error(
                description=f"Failed to create snapshot: {e!s}", title="Snapshot Failed"
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
