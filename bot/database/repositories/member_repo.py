"""Member repository — CRUD operations for members, warnings, and mod actions.

All methods accept an AsyncSession and operate within its transaction.
The caller (typically a service layer) manages the session lifecycle.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.member import MemberData, ModAction, ModActionType, Warning
from bot.utils.logger import get_logger

logger = get_logger(__name__)


class MemberRepository:
    """Data access layer for member-related models.

    Provides typed, reusable query methods for MemberData,
    Warning, and ModAction.
    """

    # ------------------------------------------------------------------
    # MemberData CRUD
    # ------------------------------------------------------------------

    @staticmethod
    async def get_member(
        session: AsyncSession,
        guild_id: int,
        user_id: int,
    ) -> MemberData | None:
        """Get member data for a specific user in a guild.

        Args:
            session: Active database session.
            guild_id: Discord guild snowflake ID.
            user_id: Discord user snowflake ID.

        Returns:
            MemberData if found, None otherwise.
        """
        result = await session.execute(
            select(MemberData).where(
                MemberData.guild_id == guild_id,
                MemberData.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_or_create_member(
        session: AsyncSession,
        guild_id: int,
        user_id: int,
        username: str = "Unknown",
        display_name: str | None = None,
    ) -> MemberData:
        """Get or create member data, ensuring a row exists.

        Args:
            session: Active database session.
            guild_id: Discord guild snowflake ID.
            user_id: Discord user snowflake ID.
            username: User's current username.
            display_name: User's display/nick name.

        Returns:
            The existing or newly created MemberData.
        """
        member = await MemberRepository.get_member(session, guild_id, user_id)
        if member is not None:
            # Update cached info
            member.username = username
            if display_name is not None:
                member.display_name = display_name
            await session.flush()
            return member

        member = MemberData(
            guild_id=guild_id,
            user_id=user_id,
            username=username,
            display_name=display_name,
        )
        session.add(member)
        await session.flush()
        return member

    @staticmethod
    async def increment_messages(
        session: AsyncSession,
        guild_id: int,
        user_id: int,
    ) -> None:
        """Increment a member's total message count by 1.

        Args:
            session: Active database session.
            guild_id: Discord guild snowflake ID.
            user_id: Discord user snowflake ID.
        """
        member = await MemberRepository.get_member(session, guild_id, user_id)
        if member is not None:
            member.total_messages += 1
            await session.flush()

    # ------------------------------------------------------------------
    # Warning CRUD
    # ------------------------------------------------------------------

    @staticmethod
    async def add_warning(
        session: AsyncSession,
        guild_id: int,
        user_id: int,
        moderator_id: int,
        reason: str,
    ) -> Warning:
        """Issue a new warning to a member.

        Also increments the member's total_warnings count.

        Args:
            session: Active database session.
            guild_id: Discord guild snowflake ID.
            user_id: Target user's Discord ID.
            moderator_id: Moderator's Discord ID.
            reason: Warning reason.

        Returns:
            The newly created Warning.
        """
        # Ensure member data exists
        member = await MemberRepository.get_or_create_member(session, guild_id, user_id)

        warning = Warning(
            guild_id=guild_id,
            user_id=user_id,
            moderator_id=moderator_id,
            reason=reason,
            member_data_id=member.id,
        )
        session.add(warning)

        # Increment warning count
        member.total_warnings += 1
        await session.flush()

        logger.info(
            "member_repo.warning_added",
            warning_id=warning.id,
            guild_id=guild_id,
            user_id=user_id,
            moderator_id=moderator_id,
        )
        return warning

    @staticmethod
    async def get_warnings(
        session: AsyncSession,
        guild_id: int,
        user_id: int,
        active_only: bool = True,
    ) -> list[Warning]:
        """Get all warnings for a member in a guild.

        Args:
            session: Active database session.
            guild_id: Discord guild snowflake ID.
            user_id: Target user's Discord ID.
            active_only: If True, only return active (non-pardoned) warnings.

        Returns:
            List of Warning records, ordered by creation date (newest first).
        """
        query = (
            select(Warning)
            .where(
                Warning.guild_id == guild_id,
                Warning.user_id == user_id,
            )
            .order_by(Warning.created_at.desc())
        )

        if active_only:
            query = query.where(Warning.is_active.is_(True))

        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_warning_count(
        session: AsyncSession,
        guild_id: int,
        user_id: int,
    ) -> int:
        """Get the count of active warnings for a member.

        Args:
            session: Active database session.
            guild_id: Discord guild snowflake ID.
            user_id: Target user's Discord ID.

        Returns:
            Number of active warnings.
        """
        result = await session.execute(
            select(func.count(Warning.id)).where(
                Warning.guild_id == guild_id,
                Warning.user_id == user_id,
                Warning.is_active.is_(True),
            )
        )
        return result.scalar_one()

    @staticmethod
    async def pardon_warning(
        session: AsyncSession,
        warning_id: int,
        pardoned_by: int,
    ) -> Warning | None:
        """Pardon (deactivate) a specific warning.

        Args:
            session: Active database session.
            warning_id: The warning's database ID.
            pardoned_by: Moderator's Discord ID who is pardoning.

        Returns:
            The pardoned Warning, or None if not found.
        """
        result = await session.execute(select(Warning).where(Warning.id == warning_id))
        warning = result.scalar_one_or_none()

        if warning is None or not warning.is_active:
            return None

        warning.is_active = False
        warning.pardoned_by = pardoned_by
        warning.pardoned_at = datetime.now(timezone.utc)

        # Decrement member's warning count
        member = await MemberRepository.get_member(session, warning.guild_id, warning.user_id)
        if member is not None and member.total_warnings > 0:
            member.total_warnings -= 1

        await session.flush()
        return warning

    @staticmethod
    async def clear_warnings(
        session: AsyncSession,
        guild_id: int,
        user_id: int,
        cleared_by: int,
    ) -> int:
        """Clear all active warnings for a member.

        Args:
            session: Active database session.
            guild_id: Discord guild snowflake ID.
            user_id: Target user's Discord ID.
            cleared_by: Moderator's Discord ID who is clearing.

        Returns:
            Number of warnings cleared.
        """
        warnings = await MemberRepository.get_warnings(session, guild_id, user_id, active_only=True)

        now = datetime.now(timezone.utc)
        for warning in warnings:
            warning.is_active = False
            warning.pardoned_by = cleared_by
            warning.pardoned_at = now

        # Reset member's warning count
        member = await MemberRepository.get_member(session, guild_id, user_id)
        if member is not None:
            member.total_warnings = 0

        await session.flush()
        return len(warnings)

    # ------------------------------------------------------------------
    # ModAction CRUD
    # ------------------------------------------------------------------

    @staticmethod
    async def log_action(
        session: AsyncSession,
        guild_id: int,
        user_id: int,
        moderator_id: int,
        action_type: ModActionType | str,
        reason: str = "No reason provided",
        duration_seconds: int | None = None,
        details: str | None = None,
        is_automated: bool = False,
    ) -> ModAction:
        """Log a moderation action.

        This is the central audit trail method. Every moderation action
        (manual or automated) should call this.

        Args:
            session: Active database session.
            guild_id: Discord guild snowflake ID.
            user_id: Target user's Discord ID.
            moderator_id: Acting moderator's Discord ID (or bot ID for auto).
            action_type: Type of action from ModActionType.
            reason: Reason for the action.
            duration_seconds: Duration for timed actions (timeouts, mutes).
            details: Additional context string.
            is_automated: Whether this was triggered by auto-mod/security.

        Returns:
            The newly created ModAction record.
        """
        # Resolve member_data_id if member data exists
        member = await MemberRepository.get_member(session, guild_id, user_id)
        member_data_id = member.id if member else None

        action_type_str = (
            action_type.value if isinstance(action_type, ModActionType) else str(action_type)
        )
        action = ModAction(
            guild_id=guild_id,
            user_id=user_id,
            moderator_id=moderator_id,
            action_type=action_type_str,
            reason=reason,
            duration_seconds=duration_seconds,
            details=details,
            is_automated=is_automated,
            member_data_id=member_data_id,
        )
        session.add(action)
        await session.flush()

        logger.info(
            "member_repo.action_logged",
            action_id=action.id,
            action_type=str(action_type),
            guild_id=guild_id,
            user_id=user_id,
            moderator_id=moderator_id,
            is_automated=is_automated,
        )
        return action

    @staticmethod
    async def get_actions(
        session: AsyncSession,
        guild_id: int,
        user_id: int | None = None,
        action_type: ModActionType | str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ModAction]:
        """Get moderation actions with optional filters.

        Args:
            session: Active database session.
            guild_id: Discord guild snowflake ID.
            user_id: Filter by target user (None = all users).
            action_type: Filter by action type (None = all types).
            limit: Maximum records to return.
            offset: Pagination offset.

        Returns:
            List of ModAction records, newest first.
        """
        query = (
            select(ModAction)
            .where(ModAction.guild_id == guild_id)
            .order_by(ModAction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        if user_id is not None:
            query = query.where(ModAction.user_id == user_id)
        if action_type is not None:
            action_type_val = (
                action_type.value if isinstance(action_type, ModActionType) else str(action_type)
            )
            query = query.where(ModAction.action_type == action_type_val)

        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_action_count(
        session: AsyncSession,
        guild_id: int,
        user_id: int | None = None,
    ) -> int:
        """Get the total count of moderation actions.

        Args:
            session: Active database session.
            guild_id: Discord guild snowflake ID.
            user_id: Filter by target user (None = all users).

        Returns:
            Total action count.
        """
        query = select(func.count(ModAction.id)).where(ModAction.guild_id == guild_id)
        if user_id is not None:
            query = query.where(ModAction.user_id == user_id)

        result = await session.execute(query)
        return result.scalar_one()
