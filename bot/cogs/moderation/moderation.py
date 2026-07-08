"""Discord interface for moderation commands.

Provides all slash commands for moderation, warning, history, and config.
Delegates business logic and database interactions to the Service layer.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Literal

import discord
from discord import app_commands
from discord.ext import commands

from bot.database.models.member import ModActionType
from bot.services.history_service import HistoryService
from bot.services.logging_service import LoggingService
from bot.services.moderation_service import BotHierarchyError, HierarchyError, ModerationError, ModerationService
from bot.services.punishment_service import PunishmentService
from bot.utils.embed_builder import EmbedBuilder
from bot.utils.logger import get_logger
from bot.utils.paginator import PaginatorView
from bot.utils.permissions import check_bot_hierarchy, check_hierarchy
from bot.utils.time_parser import DurationParseError, parse_duration

if TYPE_CHECKING:
    from bot.core.bot import ManagementBot

logger = get_logger(__name__)


@app_commands.guild_only()
class ModerationCog(commands.Cog, name="Moderation"):
    """Moderation commands for server management."""

    def __init__(self, bot: ManagementBot) -> None:
        self.bot = bot
        self.mod_service = ModerationService(bot)
        self.punishment_service = PunishmentService(bot, self.mod_service)
        self.history_service = HistoryService()
        self.logging_service = LoggingService(bot)

    async def _handle_mod_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        """Handle specific moderation errors and display friendly messages."""
        if isinstance(error, (HierarchyError, BotHierarchyError, ModerationError, DurationParseError)):
            embed = EmbedBuilder.error(
                title="Moderation Failed",
                description=str(error)
            )
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            # Let the global error handler deal with unexpected exceptions
            raise error

    # ==================================================================
    # Standard Moderation Commands
    # ==================================================================

    @app_commands.command(name="kick", description="Kick a member from the server.")
    @app_commands.describe(
        target="The member to kick",
        reason="Reason for the kick"
    )
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(
        self,
        interaction: discord.Interaction,
        target: discord.Member,
        reason: str = "No reason provided",
    ) -> None:
        """Kick command."""
        assert interaction.guild is not None
        await interaction.response.defer(ephemeral=True)

        try:
            async with self.bot.db.session() as session:
                await self.mod_service.kick_member(
                    session, interaction.guild, target, interaction.user, reason
                )
                await session.commit()
            
            embed = EmbedBuilder.success(
                title="Member Kicked",
                description=f"Successfully kicked {target.mention}."
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await self._handle_mod_error(interaction, e)

    @app_commands.command(name="ban", description="Ban a member from the server.")
    @app_commands.describe(
        target="The user to ban",
        reason="Reason for the ban",
        delete_days="Number of days of messages to delete (0-7)"
    )
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(
        self,
        interaction: discord.Interaction,
        target: discord.User,
        reason: str = "No reason provided",
        delete_days: app_commands.Range[int, 0, 7] = 0,
    ) -> None:
        """Ban command."""
        assert interaction.guild is not None
        await interaction.response.defer(ephemeral=True)

        # Resolve to Member if in guild for hierarchy checks
        member_target = interaction.guild.get_member(target.id) or target

        try:
            async with self.bot.db.session() as session:
                # Type ignoring Literal restriction for the dynamically passed int, 
                # discord.py Range validator ensures it's 0-7.
                await self.mod_service.ban_member(
                    session, interaction.guild, member_target, interaction.user, 
                    reason, delete_days, False  # type: ignore
                )
                await session.commit()
            
            embed = EmbedBuilder.success(
                title="Member Banned",
                description=f"Successfully banned {target.mention}."
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await self._handle_mod_error(interaction, e)

    @app_commands.command(name="unban", description="Unban a user from the server.")
    @app_commands.describe(
        user_id="The ID of the user to unban",
        reason="Reason for the unban"
    )
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(
        self,
        interaction: discord.Interaction,
        user_id: str,
        reason: str = "No reason provided",
    ) -> None:
        """Unban command."""
        assert interaction.guild is not None
        await interaction.response.defer(ephemeral=True)

        try:
            target_id = int(user_id)
            target = await self.bot.fetch_user(target_id)
            
            async with self.bot.db.session() as session:
                await self.mod_service.unban_member(
                    session, interaction.guild, target, interaction.user, reason
                )
                await session.commit()
                
            embed = EmbedBuilder.success(
                title="User Unbanned",
                description=f"Successfully unbanned {target.mention}."
            )
            await interaction.followup.send(embed=embed)
        except ValueError:
            await interaction.followup.send(
                embed=EmbedBuilder.error(description="Invalid user ID provided."),
                ephemeral=True
            )
        except discord.NotFound:
            await interaction.followup.send(
                embed=EmbedBuilder.error(description="User not found (or not banned)."),
                ephemeral=True
            )
        except Exception as e:
            await self._handle_mod_error(interaction, e)

    @app_commands.command(name="softban", description="Ban and unban a member to clear their recent messages.")
    @app_commands.describe(
        target="The member to softban",
        reason="Reason for the softban",
        delete_days="Number of days of messages to delete (1-7)"
    )
    @app_commands.checks.has_permissions(ban_members=True, kick_members=True)
    async def softban(
        self,
        interaction: discord.Interaction,
        target: discord.Member,
        reason: str = "No reason provided",
        delete_days: app_commands.Range[int, 1, 7] = 1,
    ) -> None:
        """Softban command."""
        assert interaction.guild is not None
        await interaction.response.defer(ephemeral=True)

        try:
            async with self.bot.db.session() as session:
                await self.mod_service.softban_member(
                    session, interaction.guild, target, interaction.user, 
                    reason, delete_days  # type: ignore
                )
                await session.commit()
            
            embed = EmbedBuilder.success(
                title="Member Softbanned",
                description=f"Successfully softbanned {target.mention} (Messages cleared)."
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await self._handle_mod_error(interaction, e)

    @app_commands.command(name="timeout", description="Timeout (mute) a member temporarily.")
    @app_commands.describe(
        target="The member to timeout",
        duration="Duration (e.g. 10m, 2h, 1d)",
        reason="Reason for the timeout"
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(
        self,
        interaction: discord.Interaction,
        target: discord.Member,
        duration: str,
        reason: str = "No reason provided",
    ) -> None:
        """Timeout command."""
        assert interaction.guild is not None
        await interaction.response.defer(ephemeral=True)

        try:
            time_delta = parse_duration(duration)
            
            async with self.bot.db.session() as session:
                await self.mod_service.timeout_member(
                    session, interaction.guild, target, interaction.user, 
                    time_delta, reason
                )
                await session.commit()
            
            from bot.utils.time_parser import format_duration
            
            embed = EmbedBuilder.success(
                title="Member Timed Out",
                description=f"Successfully timed out {target.mention} for {format_duration(time_delta)}."
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await self._handle_mod_error(interaction, e)

    @app_commands.command(name="untimeout", description="Remove a timeout from a member.")
    @app_commands.describe(
        target="The member to remove the timeout from",
        reason="Reason for untimeout"
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def untimeout(
        self,
        interaction: discord.Interaction,
        target: discord.Member,
        reason: str = "No reason provided",
    ) -> None:
        """Untimeout command."""
        assert interaction.guild is not None
        await interaction.response.defer(ephemeral=True)

        try:
            async with self.bot.db.session() as session:
                await self.mod_service.untimeout_member(
                    session, interaction.guild, target, interaction.user, reason
                )
                await session.commit()
            
            embed = EmbedBuilder.success(
                title="Timeout Removed",
                description=f"Successfully removed timeout from {target.mention}."
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await self._handle_mod_error(interaction, e)

    # ==================================================================
    # Warning System Commands
    # ==================================================================

    @app_commands.command(name="warn", description="Issue a formal warning to a member.")
    @app_commands.describe(
        target="The member to warn",
        reason="Reason for the warning"
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warn(
        self,
        interaction: discord.Interaction,
        target: discord.Member,
        reason: str,
    ) -> None:
        """Warn command."""
        assert interaction.guild is not None
        await interaction.response.defer(ephemeral=True)

        try:
            async with self.bot.db.session() as session:
                warning, punishment_msg = await self.punishment_service.add_warning(
                    session, interaction.guild, target, interaction.user, reason
                )
                await session.commit()
            
            desc = f"Successfully warned {target.mention} (Warning ID: `{warning.id}`)."
            if punishment_msg:
                desc += f"\n\n**Auto-Punishment Applied:** {punishment_msg}"
                
            embed = EmbedBuilder.success(
                title="Member Warned",
                description=desc
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await self._handle_mod_error(interaction, e)

    @app_commands.command(name="warnings", description="View warnings for a member.")
    @app_commands.describe(
        target="The member to view warnings for",
        active_only="Show only active warnings (default True)"
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warnings(
        self,
        interaction: discord.Interaction,
        target: discord.Member,
        active_only: bool = True,
    ) -> None:
        """Warnings view command."""
        assert interaction.guild is not None
        await interaction.response.defer(ephemeral=True)

        async with self.bot.db.session() as session:
            embeds = await self.history_service.get_warnings_embeds(
                session, interaction.guild, target, active_only
            )
            
        if len(embeds) == 1:
            await interaction.followup.send(embed=embeds[0])
        else:
            view = PaginatorView(embeds, interaction.user)
            await interaction.followup.send(embed=embeds[0], view=view)

    @app_commands.command(name="clearwarnings", description="Clear all active warnings for a member.")
    @app_commands.describe(
        target="The member to clear warnings for",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def clearwarnings(
        self,
        interaction: discord.Interaction,
        target: discord.Member,
    ) -> None:
        """Clear warnings command."""
        assert interaction.guild is not None
        await interaction.response.defer(ephemeral=True)

        async with self.bot.db.session() as session:
            count = await self.punishment_service.clear_warnings(
                session, interaction.guild, target, interaction.user
            )
            await session.commit()
            
        embed = EmbedBuilder.success(
            title="Warnings Cleared",
            description=f"Cleared {count} active warnings for {target.mention}."
        )
        await interaction.followup.send(embed=embed)

    # ==================================================================
    # Utility Commands
    # ==================================================================

    @app_commands.command(name="purge", description="Bulk delete messages in the current channel.")
    @app_commands.describe(
        amount="Number of messages to search/delete (max 1000)",
        user="Only delete messages from this user",
        contains="Only delete messages containing this text",
        bots_only="Only delete messages from bots",
        humans_only="Only delete messages from humans",
        attachments="Only delete messages with attachments",
        links="Only delete messages containing links",
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge(
        self,
        interaction: discord.Interaction,
        amount: app_commands.Range[int, 1, 1000],
        user: discord.Member | discord.User | None = None,
        contains: str | None = None,
        bots_only: bool = False,
        humans_only: bool = False,
        attachments: bool = False,
        links: bool = False,
    ) -> None:
        """Purge command."""
        assert interaction.guild is not None
        
        # We don't defer because purge takes time and followup.send creates a message
        # we might want to delete. We'll send an ephemeral response instead at the end.
        if bots_only and humans_only:
            await interaction.response.send_message(
                embed=EmbedBuilder.error(description="Cannot specify both bots_only and humans_only."),
                ephemeral=True
            )
            return

        # Defer ephemerally
        await interaction.response.defer(ephemeral=True)

        channel = interaction.channel
        if not isinstance(channel, (discord.TextChannel, discord.Thread, discord.VoiceChannel)):
            await interaction.followup.send(
                embed=EmbedBuilder.error(description="Cannot purge in this channel type."),
                ephemeral=True
            )
            return

        try:
            async with self.bot.db.session() as session:
                deleted = await self.mod_service.purge_messages(
                    session,
                    channel,
                    interaction.user,
                    amount=amount,
                    reason="Command purge",
                    target_user=user,
                    contains_text=contains,
                    bots_only=bots_only,
                    humans_only=humans_only,
                    has_attachments=attachments,
                    has_links=links,
                )
                await session.commit()

            embed = EmbedBuilder.success(
                title="Purge Complete",
                description=f"Successfully deleted {deleted} messages."
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await self._handle_mod_error(interaction, e)

    @app_commands.command(name="slowmode", description="Set the slowmode delay for the current channel.")
    @app_commands.describe(
        duration="Delay duration (e.g. 5s, 1m) or 0 to disable",
        reason="Reason for setting slowmode"
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode(
        self,
        interaction: discord.Interaction,
        duration: str,
        reason: str = "No reason provided",
    ) -> None:
        """Slowmode command."""
        assert interaction.guild is not None
        await interaction.response.defer(ephemeral=True)

        channel = interaction.channel
        if not isinstance(channel, (discord.TextChannel, discord.Thread, discord.VoiceChannel)):
            await interaction.followup.send(
                embed=EmbedBuilder.error(description="Cannot set slowmode in this channel type."),
                ephemeral=True
            )
            return

        try:
            if duration in ("0", "0s", "off", "disable"):
                seconds = 0
            else:
                seconds = int(parse_duration(duration).total_seconds())

            async with self.bot.db.session() as session:
                await self.mod_service.set_slowmode(
                    session, channel, interaction.user, seconds, reason
                )
                await session.commit()
                
            status = "disabled" if seconds == 0 else f"set to {seconds} seconds"
            embed = EmbedBuilder.success(
                title="Slowmode Updated",
                description=f"Slowmode in {channel.mention} has been {status}."
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await self._handle_mod_error(interaction, e)

    @app_commands.command(name="nick", description="Change a member's nickname.")
    @app_commands.describe(
        target="The member to rename",
        nickname="The new nickname (leave empty to reset)",
        reason="Reason for nickname change"
    )
    @app_commands.checks.has_permissions(manage_nicknames=True)
    async def nick(
        self,
        interaction: discord.Interaction,
        target: discord.Member,
        nickname: str | None = None,
        reason: str = "No reason provided",
    ) -> None:
        """Nickname command."""
        assert interaction.guild is not None
        await interaction.response.defer(ephemeral=True)

        try:
            async with self.bot.db.session() as session:
                await self.mod_service.set_nickname(
                    session, interaction.guild, target, interaction.user, nickname, reason
                )
                await session.commit()
                
            status = f"set to '{nickname}'" if nickname else "reset"
            embed = EmbedBuilder.success(
                title="Nickname Updated",
                description=f"{target.mention}'s nickname was {status}."
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await self._handle_mod_error(interaction, e)

    @app_commands.command(name="lock", description="Lock the current channel (prevents @everyone from sending messages).")
    @app_commands.describe(reason="Reason for lockdown")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock(
        self,
        interaction: discord.Interaction,
        reason: str = "No reason provided",
    ) -> None:
        """Lock command."""
        assert interaction.guild is not None
        await interaction.response.defer(ephemeral=False)

        channel = interaction.channel
        if not isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
            await interaction.followup.send(
                embed=EmbedBuilder.error(description="Cannot lock this channel type."),
                ephemeral=True
            )
            return

        try:
            async with self.bot.db.session() as session:
                await self.mod_service.lock_channel(
                    session, channel, interaction.user, reason
                )
                await session.commit()
                
            embed = EmbedBuilder.warning(
                title="🔒 Channel Locked",
                description=f"This channel has been locked down.\n**Reason:** {reason}"
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await self._handle_mod_error(interaction, e)

    @app_commands.command(name="unlock", description="Unlock the current channel.")
    @app_commands.describe(reason="Reason for unlock")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock(
        self,
        interaction: discord.Interaction,
        reason: str = "No reason provided",
    ) -> None:
        """Unlock command."""
        assert interaction.guild is not None
        await interaction.response.defer(ephemeral=False)

        channel = interaction.channel
        if not isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
            await interaction.followup.send(
                embed=EmbedBuilder.error(description="Cannot unlock this channel type."),
                ephemeral=True
            )
            return

        try:
            async with self.bot.db.session() as session:
                await self.mod_service.unlock_channel(
                    session, channel, interaction.user, reason
                )
                await session.commit()
                
            embed = EmbedBuilder.success(
                title="🔓 Channel Unlocked",
                description=f"This channel has been unlocked.\n**Reason:** {reason}"
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await self._handle_mod_error(interaction, e)

    # ==================================================================
    # History and Configuration
    # ==================================================================

    @app_commands.command(name="history", description="View moderation history for a user.")
    @app_commands.describe(
        user="The user to view history for",
        action_type="Filter by specific action type"
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def history(
        self,
        interaction: discord.Interaction,
        user: discord.Member | discord.User,
        action_type: ModActionType | None = None,
    ) -> None:
        """History command."""
        assert interaction.guild is not None
        await interaction.response.defer(ephemeral=True)

        async with self.bot.db.session() as session:
            embeds = await self.history_service.get_user_history_embeds(
                session, interaction.guild, user, action_type
            )
            
        if len(embeds) == 1:
            await interaction.followup.send(embed=embeds[0])
        else:
            view = PaginatorView(embeds, interaction.user)
            await interaction.followup.send(embed=embeds[0], view=view)

    @app_commands.command(name="modlogs", description="Set or disable the moderation logging channel.")
    @app_commands.describe(
        channel="The channel to send mod logs to (leave empty to disable)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def modlogs(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel | None = None,
    ) -> None:
        """Modlogs config command."""
        assert interaction.guild is not None
        await interaction.response.defer(ephemeral=True)

        async with self.bot.db.session() as session:
            await self.logging_service.set_log_channel(
                session, interaction.guild.id, channel.id if channel else None
            )
            await session.commit()
            
        if channel:
            embed = EmbedBuilder.success(
                title="Mod Logs Configured",
                description=f"Moderation logs will now be sent to {channel.mention}."
            )
        else:
            embed = EmbedBuilder.info(
                title="Mod Logs Disabled",
                description="Moderation logs will no longer be sent to any channel."
            )
            
        await interaction.followup.send(embed=embed)
