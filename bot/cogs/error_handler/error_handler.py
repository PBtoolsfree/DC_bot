"""Global error handler for all slash commands and app commands.

Catches all unhandled exceptions in commands and sends user-friendly
error messages while logging the full traceback for debugging.
"""

from __future__ import annotations

import traceback
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from bot.utils.embed_builder import EmbedBuilder
from bot.utils.logger import get_logger

if TYPE_CHECKING:
    from bot.core.bot import ManagementBot

logger = get_logger(__name__)


class ErrorHandler(commands.Cog):
    """Global error handler cog.

    Listens for command errors and app command errors, providing
    consistent, user-friendly error responses.
    """

    def __init__(self, bot: ManagementBot) -> None:
        self.bot = bot
        # Register the app command error handler
        self.bot.tree.on_error = self.on_app_command_error

    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        """Handle errors from slash commands and context menus.

        Args:
            interaction: The interaction that caused the error.
            error: The error that occurred.
        """
        # Unwrap the error if it's wrapped in a CommandInvokeError
        original = getattr(error, "original", error)

        # --- Permission Errors ---
        if isinstance(error, app_commands.MissingPermissions):
            missing = ", ".join(
                perm.replace("_", " ").title() for perm in error.missing_permissions
            )
            await self._send_error(
                interaction,
                f"You're missing the following permissions: **{missing}**",
            )
            return

        if isinstance(error, app_commands.BotMissingPermissions):
            missing = ", ".join(
                perm.replace("_", " ").title() for perm in error.missing_permissions
            )
            await self._send_error(
                interaction,
                f"I'm missing the following permissions: **{missing}**\n"
                f"Please update my role permissions and try again.",
            )
            return

        # --- Cooldown ---
        if isinstance(error, app_commands.CommandOnCooldown):
            await self._send_error(
                interaction,
                f"This command is on cooldown. "
                f"Try again in **{error.retry_after:.1f}** seconds.",
            )
            return

        # --- Check Failures ---
        if isinstance(error, app_commands.CheckFailure):
            await self._send_error(
                interaction,
                "You don't have permission to use this command.",
            )
            return

        # --- Command Not Found ---
        if isinstance(error, app_commands.CommandNotFound):
            # Silently ignore — this can happen during sync transitions
            return

        # --- Transformer Errors (bad argument conversion) ---
        if isinstance(error, app_commands.TransformerError):
            await self._send_error(
                interaction,
                f"Invalid argument: {error}",
            )
            return

        # --- Discord HTTP Errors ---
        if isinstance(original, discord.HTTPException):
            if original.status == 403:
                await self._send_error(
                    interaction,
                    "I don't have permission to perform this action. "
                    "Check my role position and permissions.",
                )
                return
            if original.status == 404:
                await self._send_error(
                    interaction,
                    "The requested resource was not found. " "It may have been deleted.",
                )
                return

        # --- Unknown Errors ---
        error_id = id(error)
        logger.error(
            "command.error.unhandled",
            error_id=error_id,
            error_type=type(original).__name__,
            error_message=str(original),
            command=getattr(interaction.command, "name", "unknown"),
            user_id=interaction.user.id,
            guild_id=getattr(interaction.guild, "id", None),
            traceback=traceback.format_exception(type(original), original, original.__traceback__),
        )

        await self._send_error(
            interaction,
            f"An unexpected error occurred. This has been logged.\n" f"Error ID: `{error_id}`",
        )

    @commands.Cog.listener()
    async def on_command_error(
        self,
        ctx: commands.Context[ManagementBot],
        error: commands.CommandError,
    ) -> None:
        """Handle errors from prefix commands (if any).

        Args:
            ctx: The command context.
            error: The error that occurred.
        """
        # Ignore command not found (we primarily use slash commands)
        if isinstance(error, commands.CommandNotFound):
            return

        original = getattr(error, "original", error)

        logger.error(
            "prefix_command.error",
            error_type=type(original).__name__,
            error_message=str(original),
            command=ctx.command.name if ctx.command else "unknown",
            user_id=ctx.author.id,
            guild_id=getattr(ctx.guild, "id", None),
        )

    async def _send_error(
        self,
        interaction: discord.Interaction,
        message: str,
    ) -> None:
        """Send an error message, handling both responded and unresponded interactions.

        Args:
            interaction: The slash command interaction.
            message: Error message to display.
        """
        embed = EmbedBuilder.error(title="Error", description=message)

        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.HTTPException:
            # If we can't even send the error message, just log it
            logger.error(
                "error_handler.send_failed",
                user_id=interaction.user.id,
                message=message,
            )
