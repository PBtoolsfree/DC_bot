"""Logging service for dispatching moderation logs to Discord channels."""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from bot.database.repositories.guild_repo import GuildRepository
from bot.utils.embed_builder import EmbedBuilder
from bot.utils.logger import get_logger

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from bot.core.bot import ManagementBot
    from bot.database.models.member import ModAction

logger = get_logger(__name__)


class LoggingService:
    """Service for sending moderation audit logs to Discord channels."""

    def __init__(self, bot: ManagementBot) -> None:
        """Initialize the logging service.

        Args:
            bot: The bot instance.
        """
        self.bot = bot

    async def get_log_channel(
        self,
        session: AsyncSession,
        guild: discord.Guild,
    ) -> discord.TextChannel | None:
        """Get the configured moderation log channel for a guild.

        Args:
            session: Active database session.
            guild: The Discord guild.

        Returns:
            The TextChannel if configured and valid, None otherwise.
        """
        settings = await GuildRepository.get_or_create_module_settings(session, guild.id, "logs")
        channel_id = settings.config.get("mod_log_channel_id")

        if not channel_id:
            return None

        # Try to get from cache first, then fetch
        channel = guild.get_channel(channel_id)
        if not channel:
            try:
                channel = await guild.fetch_channel(channel_id)
            except (discord.NotFound, discord.Forbidden):
                return None

        if isinstance(channel, discord.TextChannel):
            return channel
        return None

    async def log_action(
        self,
        session: AsyncSession,
        guild: discord.Guild,
        action: ModAction,
        target: discord.Member | discord.User | str,
        moderator: discord.Member | discord.User | str,
    ) -> None:
        """Send a moderation log embed to the configured channel.

        Args:
            session: Active database session.
            guild: The Discord guild.
            action: The ModAction database record.
            target: The target user/member or name.
            moderator: The moderator who performed the action.
        """
        channel = await self.get_log_channel(session, guild)
        if not channel:
            return

        # Format duration if present
        duration_str = None
        if action.duration_seconds:
            from bot.utils.time_parser import format_seconds

            duration_str = format_seconds(action.duration_seconds)

        # Create embed
        embed = EmbedBuilder.moderation(
            action=action.action_type.replace("_", " ").title(),
            target=target,
            moderator=moderator,
            reason=action.reason,
            duration=duration_str,
            case_id=action.id,
        )

        # Add additional details if present
        if action.details:
            embed.add_field(name="Details", value=action.details, inline=False)

        # Indicate if automated
        if action.is_automated:
            embed.set_footer(
                text=f"Case #{action.id} • Automated Action",
                icon_url=self.bot.user.display_avatar.url if self.bot.user else None,
            )

        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            logger.warning(
                "logging_service.forbidden",
                guild_id=guild.id,
                channel_id=channel.id,
                action_id=action.id,
            )
        except discord.HTTPException as e:
            logger.error(
                "logging_service.http_error",
                guild_id=guild.id,
                channel_id=channel.id,
                action_id=action.id,
                error=str(e),
            )

    async def set_log_channel(
        self,
        session: AsyncSession,
        guild_id: int,
        channel_id: int | None,
    ) -> None:
        """Configure the moderation log channel.

        Args:
            session: Active database session.
            guild_id: Discord guild ID.
            channel_id: The channel ID to set, or None to disable.
        """
        settings = await GuildRepository.get_or_create_module_settings(session, guild_id, "logs")

        config = settings.config.copy()
        if channel_id is None:
            config.pop("mod_log_channel_id", None)
        else:
            config["mod_log_channel_id"] = channel_id

        await GuildRepository.update_module_settings(
            session,
            guild_id,
            "logs",
            enabled=True,
            config=config,
        )
