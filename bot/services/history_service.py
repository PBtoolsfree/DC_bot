"""History service for retrieving and formatting moderation history."""

from __future__ import annotations

from typing import TYPE_CHECKING

from bot.database.repositories.member_repo import MemberRepository
from bot.utils.embed_builder import EmbedBuilder

if TYPE_CHECKING:
    import discord
    from sqlalchemy.ext.asyncio import AsyncSession

    from bot.database.models.member import ModActionType


class HistoryService:
    """Service for retrieving and formatting moderation history."""

    @staticmethod
    async def get_user_history_embeds(
        session: AsyncSession,
        guild: discord.Guild,
        user: discord.Member | discord.User,
        action_type: ModActionType | str | None = None,
    ) -> list[discord.Embed]:
        """Get paginated history embeds for a user.

        Args:
            session: Active database session.
            guild: The Discord guild.
            user: The target user.
            action_type: Optional filter by action type.

        Returns:
            A list of Embeds ready for pagination.
        """
        actions = await MemberRepository.get_actions(
            session, guild.id, user.id, action_type=action_type
        )
        total_actions = len(actions)
        active_warnings = await MemberRepository.get_warning_count(session, guild.id, user.id)

        if not actions:
            title = f"History for {user}"
            if action_type:
                title += f" ({action_type})"
            embed = EmbedBuilder.info(
                title=title,
                description="No moderation history found for this user.",
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            return [embed]

        embeds = []
        items_per_page = 5
        pages = max(1, (total_actions + items_per_page - 1) // items_per_page)

        for page in range(pages):
            start_idx = page * items_per_page
            end_idx = start_idx + items_per_page
            page_actions = actions[start_idx:end_idx]

            embed = EmbedBuilder.info(
                title=f"History for {user}",
                description=f"**Total Actions:** {total_actions}\n"
                f"**Active Warnings:** {active_warnings}",
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.set_footer(text=f"Page {page + 1}/{pages} • ID: {user.id}")

            for action in page_actions:
                # Format time
                time_str = f"<t:{int(action.created_at.timestamp())}:R>"

                # Format moderator
                mod_str = f"<@{action.moderator_id}>"
                if action.is_automated:
                    mod_str += " (Automated)"

                # Build field value
                val = f"**Type:** {action.action_type.title()}\n"
                val += f"**Moderator:** {mod_str}\n"
                val += f"**Reason:** {action.reason}\n"
                val += f"**Date:** {time_str}"

                if action.duration_seconds:
                    from bot.utils.time_parser import format_seconds

                    val += f"\n**Duration:** {format_seconds(action.duration_seconds)}"
                if action.details:
                    val += f"\n**Details:** {action.details}"

                embed.add_field(
                    name=f"Case #{action.id}",
                    value=val,
                    inline=False,
                )

            embeds.append(embed)

        return embeds

    @staticmethod
    async def get_warnings_embeds(
        session: AsyncSession,
        guild: discord.Guild,
        user: discord.Member | discord.User,
        active_only: bool = True,
    ) -> list[discord.Embed]:
        """Get paginated warnings embeds for a user.

        Args:
            session: Active database session.
            guild: The Discord guild.
            user: The target user.
            active_only: Whether to show only active warnings.

        Returns:
            A list of Embeds ready for pagination.
        """
        warnings = await MemberRepository.get_warnings(
            session, guild.id, user.id, active_only=active_only
        )
        total = len(warnings)

        if not warnings:
            embed = EmbedBuilder.info(
                title=f"Warnings for {user}",
                description="This user has no warnings.",
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            return [embed]

        embeds = []
        items_per_page = 5
        pages = max(1, (total + items_per_page - 1) // items_per_page)

        for page in range(pages):
            start_idx = page * items_per_page
            end_idx = start_idx + items_per_page
            page_warnings = warnings[start_idx:end_idx]

            title = f"Warnings for {user}"
            if not active_only:
                title += " (Including Pardoned)"

            embed = EmbedBuilder.info(
                title=title,
                description=f"**Total Warnings:** {total}",
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.set_footer(text=f"Page {page + 1}/{pages} • ID: {user.id}")

            for warn in page_warnings:
                time_str = f"<t:{int(warn.created_at.timestamp())}:R>"
                status = "🔴 Active" if warn.is_active else "🟢 Pardoned"

                val = f"**Status:** {status}\n"
                val += f"**Moderator:** <@{warn.moderator_id}>\n"
                val += f"**Reason:** {warn.reason}\n"
                val += f"**Date:** {time_str}"

                if not warn.is_active and warn.pardoned_by:
                    val += f"\n**Pardoned by:** <@{warn.pardoned_by}>"

                embed.add_field(
                    name=f"Warning ID: {warn.id}",
                    value=val,
                    inline=False,
                )

            embeds.append(embed)

        return embeds
