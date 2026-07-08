"""Manual Approval Service for Verification."""

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.verification import VerificationSession


class ApprovalService:
    """Manages the Manual/Moderator approval queues for high-risk users."""

    @staticmethod
    async def request_manual_approval(session: AsyncSession, token: str) -> None:
        """Mark a session as requiring manual review."""
        stmt = (
            update(VerificationSession)
            .where(VerificationSession.session_id == token)
            .values(state="manual_review")
        )
        await session.execute(stmt)

    @staticmethod
    async def approve_user(
        session: AsyncSession, token: str, moderator_id: int
    ) -> VerificationSession | None:
        """Approve a user that was pending manual review."""
        # Find session
        from sqlalchemy import select

        stmt = select(VerificationSession).where(VerificationSession.session_id == token)
        result = await session.execute(stmt)
        v_session = result.scalar_one_or_none()

        if not v_session or v_session.state != "manual_review":
            return None

        v_session.state = "verified"
        await session.flush()
        return v_session

    @staticmethod
    async def reject_user(
        session: AsyncSession, token: str, moderator_id: int
    ) -> VerificationSession | None:
        """Reject a user that was pending manual review."""
        from sqlalchemy import select

        stmt = select(VerificationSession).where(VerificationSession.session_id == token)
        result = await session.execute(stmt)
        v_session = result.scalar_one_or_none()

        if not v_session or v_session.state != "manual_review":
            return None

        v_session.state = "rejected"
        await session.flush()
        return v_session
