"""Slash commands for the Logging module."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from bot.core.bot import ManagementBot
from bot.services.logging.search_service import SearchService
from bot.services.logging.export_service import ExportService
from bot.utils.embed_builder import EmbedBuilder
from bot.utils.permissions import PermissionLevel, require_permission


@app_commands.default_permissions(administrator=True)
class LoggingConfigCog(commands.GroupCog, group_name="logs"):
    """Search and export server audit logs."""

    def __init__(self, bot: ManagementBot) -> None:
        self.bot = bot

    @app_commands.command(name="search", description="Search recent server audit logs")
    @app_commands.describe(
        action="The type of action to search for",
        user="The user who performed or was targeted by the action",
        days="How many days ago to search"
    )
    @require_permission(PermissionLevel.ADMIN)
    async def search_logs(
        self, 
        interaction: discord.Interaction, 
        action: str | None = None,
        user: discord.User | discord.Member | None = None,
        days: int = 7
    ) -> None:
        if not interaction.guild:
            return

        await interaction.response.defer(ephemeral=True)

        async with self.bot.db.session() as session:
            logs = await SearchService.search(
                session=session,
                guild_id=interaction.guild.id,
                action_type=action,
                user_id=user.id if user else None,
                days_ago=days,
                limit=10
            )

        if not logs:
            await interaction.followup.send(
                embed=EmbedBuilder.error("No logs found matching your criteria."),
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Audit Log Search Results",
            description=f"Showing the {len(logs)} most recent matches.",
            color=discord.Color.blue()
        )

        for log in logs:
            time_str = f"<t:{int(log.created_at.timestamp())}:R>" if log.created_at else "Unknown Time"
            details = f"**Action:** `{log.action_type}` | **User:** <@{log.executor_id}>"
            if log.target_id:
                details += f" | **Target:** <@{log.target_id}>"
            if log.channel_id:
                details += f" | **Channel:** <#{log.channel_id}>"
                
            embed.add_field(name=time_str, value=details, inline=False)

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="export", description="Export server logs to a file")
    @app_commands.describe(
        format="The file format for the export",
        days="How many days of logs to export"
    )
    @app_commands.choices(format=[
        app_commands.Choice(name="CSV", value="csv"),
        app_commands.Choice(name="JSON", value="json"),
        app_commands.Choice(name="HTML", value="html"),
    ])
    @require_permission(PermissionLevel.ADMIN)
    async def export_logs(
        self,
        interaction: discord.Interaction,
        format: str = "csv",
        days: int = 30
    ) -> None:
        if not interaction.guild:
            return

        await interaction.response.defer(ephemeral=True)

        async with self.bot.db.session() as session:
            logs = await SearchService.search(
                session=session,
                guild_id=interaction.guild.id,
                days_ago=days,
                limit=10000 # Large limit for export
            )

        if not logs:
            await interaction.followup.send(
                embed=EmbedBuilder.error("No logs found to export."),
                ephemeral=True
            )
            return

        import io
        
        file = None
        filename = f"audit_export_{interaction.guild.id}.{format}"
        
        if format == "csv":
            buffer = ExportService.generate_csv(logs)
            file = discord.File(fp=io.BytesIO(buffer.getvalue().encode()), filename=filename)
        elif format == "json":
            json_str = ExportService.generate_json(logs)
            file = discord.File(fp=io.BytesIO(json_str.encode()), filename=filename)
        elif format == "html":
            html_str = ExportService.generate_html(logs)
            file = discord.File(fp=io.BytesIO(html_str.encode()), filename=filename)

        if file:
            await interaction.followup.send(
                content=f"✅ Exported {len(logs)} logs from the past {days} days.",
                file=file,
                ephemeral=True
            )
        else:
            await interaction.followup.send("Failed to generate export.", ephemeral=True)
