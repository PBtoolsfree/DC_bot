"""Verification Session Service."""

import secrets

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.verification import VerificationSession


class SessionService:
    """Manages secure verification session lifecycle."""

    @staticmethod
    def generate_token() -> str:
        """Generate a secure unique token."""
        return secrets.token_urlsafe(32)

    @staticmethod
    async def create_session(
        session: AsyncSession,
        guild_id: int,
        user_id: int,
        verification_type: str,
        risk_score: int,
        expected_answer: str | None,
        timeout_minutes: int,
    ) -> VerificationSession:
        """Create a new signed session."""
        token = SessionService.generate_token()

        # For Captchas, storing the raw expected answer is fine since they are short-lived.
        v_session = VerificationSession(
            session_id=token,
            guild_id=guild_id,
            user_id=user_id,
            verification_type=verification_type,
            risk_score=risk_score,
            expected_answer=expected_answer,
            expires_at=expires_at,
            state="challenge_issued",
        )

        session.add(v_session)
        await session.flush()
        return v_session

    @staticmethod
    async def get_session(session: AsyncSession, token: str) -> VerificationSession | None:
        """Retrieve a session by token."""
        stmt = select(VerificationSession).where(VerificationSession.session_id == token)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def validate_answer(
        v_session: VerificationSession, user_provided: str, is_case_sensitive: bool = False
    ) -> bool:
        """Fallback raw validation if provider validation isn't used."""
        if not v_session.expected_answer:
            return True

        if is_case_sensitive:
            return v_session.expected_answer == user_provided
        return v_session.expected_answer.lower() == user_provided.lower()

    @staticmethod
    async def mark_success(session: AsyncSession, token: str) -> None:
        stmt = (
            update(VerificationSession)
            .where(VerificationSession.session_id == token)
            .values(state="verified")
        )
        await session.execute(stmt)

    @staticmethod
    async def increment_attempts(session: AsyncSession, token: str) -> None:
        stmt = (
            update(VerificationSession)
            .where(VerificationSession.session_id == token)
            .values(attempts=VerificationSession.attempts + 1)
        )
        await session.execute(stmt)
