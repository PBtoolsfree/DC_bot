"""Embed builder — factory for consistent, branded Discord embeds.

Every embed the bot sends should be created through this module to ensure
consistent styling, branding, and field formatting.

Usage:
    from bot.utils.embed_builder import EmbedBuilder

    embed = EmbedBuilder.success(
        title="Member Warned",
        description="User#1234 has been warned.",
    )
    embed.add_field(name="Reason", value="Spamming", inline=False)
    await ctx.send(embed=embed)
"""

from __future__ import annotations

from datetime import datetime, timezone

import discord

from bot.utils.constants import Colors, Emojis


class EmbedBuilder:
    """Factory for creating consistently styled Discord embeds.

    All factory methods return a discord.Embed that can be further
    customized with add_field(), set_image(), etc.
    """

    BOT_NAME = "Management Bot"
    FOOTER_TEXT = "Management Bot • discord.gg/your-invite"
    ICON_URL: str | None = None  # Set after bot is ready if desired

    @classmethod
    def _base(
        cls,
        title: str | None = None,
        description: str | None = None,
        color: discord.Color = Colors.INFO,
        timestamp: bool = True,
    ) -> discord.Embed:
        """Create a base embed with standard formatting.

        Args:
            title: Embed title.
            description: Embed description.
            color: Embed sidebar color.
            timestamp: Whether to include the current UTC timestamp.

        Returns:
            A pre-formatted discord.Embed.
        """
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
        )

        if timestamp:
            embed.timestamp = datetime.now(timezone.utc)

        embed.set_footer(text=cls.FOOTER_TEXT)

        return embed

    @classmethod
    def success(
        cls,
        title: str | None = None,
        description: str | None = None,
    ) -> discord.Embed:
        """Create a success embed (green).

        Args:
            title: Embed title (auto-prefixed with ✅).
            description: Embed description.

        Returns:
            Green-colored embed.
        """
        formatted_title = f"{Emojis.SUCCESS} {title}" if title else None
        return cls._base(
            title=formatted_title,
            description=description,
            color=Colors.SUCCESS,
        )

    @classmethod
    def error(
        cls,
        title: str | None = None,
        description: str | None = None,
    ) -> discord.Embed:
        """Create an error embed (red).

        Args:
            title: Embed title (auto-prefixed with ❌).
            description: Embed description.

        Returns:
            Red-colored embed.
        """
        formatted_title = f"{Emojis.ERROR} {title}" if title else None
        return cls._base(
            title=formatted_title,
            description=description,
            color=Colors.ERROR,
        )

    @classmethod
    def warning(
        cls,
        title: str | None = None,
        description: str | None = None,
    ) -> discord.Embed:
        """Create a warning embed (yellow).

        Args:
            title: Embed title (auto-prefixed with ⚠️).
            description: Embed description.

        Returns:
            Yellow-colored embed.
        """
        formatted_title = f"{Emojis.WARNING} {title}" if title else None
        return cls._base(
            title=formatted_title,
            description=description,
            color=Colors.WARNING,
        )

    @classmethod
    def info(
        cls,
        title: str | None = None,
        description: str | None = None,
    ) -> discord.Embed:
        """Create an info embed (blurple).

        Args:
            title: Embed title (auto-prefixed with ℹ️).
            description: Embed description.

        Returns:
            Blurple-colored embed.
        """
        formatted_title = f"{Emojis.INFO} {title}" if title else None
        return cls._base(
            title=formatted_title,
            description=description,
            color=Colors.INFO,
        )

    @classmethod
    def moderation(
        cls,
        action: str,
        target: discord.Member | discord.User | str,
        moderator: discord.Member | discord.User | str,
        reason: str = "No reason provided",
        duration: str | None = None,
        case_id: int | None = None,
    ) -> discord.Embed:
        """Create a moderation action embed with standardized fields.

        Args:
            action: Action name (e.g., "Warn", "Ban", "Kick").
            target: The user being moderated.
            moderator: The moderator performing the action.
            reason: Reason for the action.
            duration: Human-readable duration string (for timeouts).
            case_id: Database case/action ID.

        Returns:
            A moderation-styled embed with all fields populated.
        """
        target_str = str(target)
        moderator_str = str(moderator)

        title = f"{Emojis.HAMMER} {action}"
        if case_id is not None:
            title += f" — Case #{case_id}"

        embed = cls._base(
            title=title,
            color=Colors.MODERATION,
        )

        embed.add_field(name="Target", value=target_str, inline=True)
        embed.add_field(name="Moderator", value=moderator_str, inline=True)

        if duration is not None:
            embed.add_field(name="Duration", value=duration, inline=True)

        embed.add_field(name="Reason", value=reason, inline=False)

        # Set target's avatar as thumbnail if it's a User/Member object
        if isinstance(target, (discord.Member, discord.User)):
            embed.set_thumbnail(url=target.display_avatar.url)

        return embed

    @classmethod
    def log(
        cls,
        action: str,
        target: discord.Member | discord.User | str | None = None,
        executor: discord.Member | discord.User | str | None = None,
        channel: discord.abc.GuildChannel | None = None,
        color: discord.Color = Colors.LOGS,
    ) -> discord.Embed:
        """Create a server log embed with standardized enterprise fields.

        Args:
            action: Log event title/action.
            target: The user/object being targeted.
            executor: The user who performed the action.
            channel: The channel where it occurred.
            color: Embed color (defaults to LOGS color).

        Returns:
            A log-styled embed.
        """
        embed = cls._base(
            title=action,
            color=color,
        )

        if executor:
            embed.add_field(name="Executor", value=str(executor), inline=True)
        if target:
            embed.add_field(name="Target", value=str(target), inline=True)
        if channel:
            embed.add_field(name="Channel", value=channel.mention, inline=True)

        return embed

    @classmethod
    def welcome(
        cls,
        member: discord.Member,
        message: str,
        guild: discord.Guild,
    ) -> discord.Embed:
        """Create a welcome embed for new members.

        Args:
            member: The member who joined.
            message: Formatted welcome message.
            guild: The guild the member joined.

        Returns:
            A welcome-styled embed with member avatar and server info.
        """
        embed = cls._base(
            title=f"{Emojis.WAVE} Welcome!",
            description=message,
            color=Colors.WELCOME,
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        if guild.icon:
            embed.set_footer(
                text=f"{guild.name} • Member #{guild.member_count}",
                icon_url=guild.icon.url,
            )

        return embed

    @classmethod
    def premium(
        cls,
        title: str | None = None,
        description: str | None = None,
    ) -> discord.Embed:
        """Create a premium feature embed (gold).

        Args:
            title: Embed title (auto-prefixed with 👑).
            description: Embed description.

        Returns:
            Gold-colored premium embed.
        """
        formatted_title = f"{Emojis.CROWN} {title}" if title else None
        return cls._base(
            title=formatted_title,
            description=description,
            color=Colors.PREMIUM,
        )

    @classmethod
    def security_alert(
        cls,
        title: str,
        description: str | None = None,
    ) -> discord.Embed:
        """Create a security alert embed (amber).

        Args:
            title: Alert title (auto-prefixed with 🛡️).
            description: Alert description.

        Returns:
            Amber-colored security alert embed.
        """
        formatted_title = f"{Emojis.SHIELD} {title}"
        return cls._base(
            title=formatted_title,
            description=description,
            color=Colors.SECURITY,
        )
