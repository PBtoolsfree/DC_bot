"""Permission check utilities.

Provides decorators and helper functions for validating permissions
in both slash commands and context menu commands. Includes:
- Custom permission level system (member → mod → admin → owner)
- Hierarchy validation (can't moderate someone above you)
- Premium feature gating
- Friendly error messages
"""

from __future__ import annotations

from collections.abc import Callable
from enum import IntEnum
from functools import wraps
from typing import TYPE_CHECKING, Any, Concatenate, ParamSpec, TypeVar

import discord

from bot.utils.constants import Emojis
from bot.utils.logger import get_logger

if TYPE_CHECKING:
    from bot.core.bot import ManagementBot

logger = get_logger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


class PermissionLevel(IntEnum):
    """Permission levels for the bot's command hierarchy.

    Higher values = more permissions. A user's effective level
    is determined by their Discord permissions and roles.
    """

    MEMBER = 0
    HELPER = 1
    MODERATOR = 2
    ADMIN = 3
    SERVER_OWNER = 4
    BOT_OWNER = 5


def get_permission_level(
    member: discord.Member,
    bot_owner_ids: set[int] | None = None,
) -> PermissionLevel:
    """Determine a member's effective permission level.

    Checks are performed in order from highest to lowest:
    1. Bot owner (from config)
    2. Server owner
    3. Administrator permission
    4. Manage Guild or Manage Channels permission
    5. Manage Messages or Kick/Ban permission
    6. Default member

    Args:
        member: The Discord member to check.
        bot_owner_ids: Set of Discord user IDs who own the bot.

    Returns:
        The member's highest applicable PermissionLevel.
    """
    if bot_owner_ids and member.id in bot_owner_ids:
        return PermissionLevel.BOT_OWNER

    if member.guild.owner_id == member.id:
        return PermissionLevel.SERVER_OWNER

    permissions = member.guild_permissions

    if permissions.administrator:
        return PermissionLevel.ADMIN

    if permissions.manage_guild or permissions.manage_channels:
        return PermissionLevel.MODERATOR

    if permissions.manage_messages or permissions.kick_members or permissions.ban_members:
        return PermissionLevel.HELPER

    return PermissionLevel.MEMBER


def check_hierarchy(
    actor: discord.Member,
    target: discord.Member,
) -> bool:
    """Check if the actor has a higher role position than the target.

    This prevents moderators from acting on users with equal or higher
    roles. The guild owner is always at the top of the hierarchy.

    Args:
        actor: The member performing the action.
        target: The member being acted upon.

    Returns:
        True if the actor outranks the target.
    """
    # Server owner outranks everyone
    if actor.guild.owner_id == actor.id:
        return True
    if target.guild.owner_id == target.id:
        return False

    return actor.top_role > target.top_role


def check_bot_hierarchy(
    bot_member: discord.Member,
    target: discord.Member,
) -> bool:
    """Check if the bot's role is high enough to moderate the target.

    Args:
        bot_member: The bot's Member object in the guild.
        target: The member to be moderated.

    Returns:
        True if the bot outranks the target.
    """
    if target.guild.owner_id == target.id:
        return False
    return bot_member.top_role > target.top_role


def require_permission(
    level: PermissionLevel,
) -> Callable[
    [Callable[Concatenate[Any, discord.Interaction, P], Any]],
    Callable[Concatenate[Any, discord.Interaction, P], Any],
]:
    """Decorator that requires a minimum permission level for a slash command.

    Usage:
        @app_commands.command()
        @require_permission(PermissionLevel.MODERATOR)
        async def warn(self, interaction: discord.Interaction, ...):
            ...

    Args:
        level: Minimum PermissionLevel required.

    Returns:
        Decorated function that checks permissions before execution.
    """

    def decorator(
        func: Callable[Concatenate[Any, discord.Interaction, P], Any],
    ) -> Callable[Concatenate[Any, discord.Interaction, P], Any]:
        @wraps(func)
        async def wrapper(
            self: Any,
            interaction: discord.Interaction,
            *args: P.args,
            **kwargs: P.kwargs,
        ) -> Any:
            # Must be in a guild
            if interaction.guild is None or not isinstance(interaction.user, discord.Member):
                await interaction.response.send_message(
                    f"{Emojis.ERROR} This command can only be used in a server.",
                    ephemeral=True,
                )
                return None

            # Get bot owner IDs
            bot: ManagementBot = interaction.client  # type: ignore[assignment]
            bot_owner_ids = set(bot.settings.bot_owner_ids)

            # Check permission level
            user_level = get_permission_level(interaction.user, bot_owner_ids)

            if user_level < level:
                level_name = level.name.replace("_", " ").title()
                await interaction.response.send_message(
                    f"{Emojis.ERROR} You need **{level_name}** "
                    f"permissions to use this command.",
                    ephemeral=True,
                )
                logger.warning(
                    "permission.denied",
                    command=func.__name__,
                    user_id=interaction.user.id,
                    required=level.name,
                    actual=user_level.name,
                )
                return None

            return await func(self, interaction, *args, **kwargs)

        return wrapper

    return decorator


def require_premium() -> Callable[
    [Callable[Concatenate[Any, discord.Interaction, P], Any]],
    Callable[Concatenate[Any, discord.Interaction, P], Any],
]:
    """Decorator that requires the guild to have an active premium subscription.

    Usage:
        @app_commands.command()
        @require_premium()
        async def premium_feature(self, interaction: discord.Interaction, ...):
            ...

    Returns:
        Decorated function that checks premium status before execution.
    """

    def decorator(
        func: Callable[Concatenate[Any, discord.Interaction, P], Any],
    ) -> Callable[Concatenate[Any, discord.Interaction, P], Any]:
        @wraps(func)
        async def wrapper(
            self: Any,
            interaction: discord.Interaction,
            *args: P.args,
            **kwargs: P.kwargs,
        ) -> Any:
            if interaction.guild is None:
                await interaction.response.send_message(
                    f"{Emojis.ERROR} This command can only be used in a server.",
                    ephemeral=True,
                )
                return None

            bot: ManagementBot = interaction.client  # type: ignore[assignment]

            from bot.database.repositories.guild_repo import GuildRepository

            async with bot.db.session() as session:
                is_premium = await GuildRepository.is_premium(session, interaction.guild.id)

            if not is_premium:
                await interaction.response.send_message(
                    f"{Emojis.CROWN} This is a **Premium** feature. " f"Upgrade to unlock it!",
                    ephemeral=True,
                )
                return None

            return await func(self, interaction, *args, **kwargs)

        return wrapper

    return decorator


async def validate_target(
    interaction: discord.Interaction,
    target: discord.Member,
) -> bool:
    """Validate that a moderation target is actionable.

    Checks:
    1. Can't target yourself
    2. Can't target the bot
    3. Actor must outrank target (role hierarchy)
    4. Bot must outrank target

    Args:
        interaction: The slash command interaction.
        target: The member to be moderated.

    Returns:
        True if the target is valid. False if a validation error
        was sent to the interaction.
    """
    assert isinstance(interaction.user, discord.Member)
    assert interaction.guild is not None
    bot_member = interaction.guild.me

    # Can't target yourself
    if target.id == interaction.user.id:
        await interaction.response.send_message(
            f"{Emojis.ERROR} You cannot moderate yourself.",
            ephemeral=True,
        )
        return False

    # Can't target the bot
    if target.id == bot_member.id:
        await interaction.response.send_message(
            f"{Emojis.ERROR} I cannot moderate myself.",
            ephemeral=True,
        )
        return False

    # Actor must outrank target
    if not check_hierarchy(interaction.user, target):
        await interaction.response.send_message(
            f"{Emojis.ERROR} You cannot moderate {target.mention} — "
            f"they have a higher or equal role.",
            ephemeral=True,
        )
        return False

    # Bot must outrank target
    if not check_bot_hierarchy(bot_member, target):
        await interaction.response.send_message(
            f"{Emojis.ERROR} I cannot moderate {target.mention} — "
            f"they have a higher or equal role than me.",
            ephemeral=True,
        )
        return False

    return True
