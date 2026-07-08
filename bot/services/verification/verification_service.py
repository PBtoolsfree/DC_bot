"""Verification Service Orchestrator."""

import datetime

import discord
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.verification import (
    VerificationHistory,
    VerificationSession,
    VerificationSettings,
)

# Assume we have a StreamingService to broadcast events (Module 5)
from bot.services.logging.streaming_service import StreamingService
from bot.services.verification.providers.base import CaptchaProvider
from bot.services.verification.providers.image_provider import ImageCaptchaProvider
from bot.services.verification.providers.math_provider import MathCaptchaProvider
from bot.services.verification.providers.word_provider import WordCaptchaProvider
from bot.services.verification.risk_engine import RiskEngineService
from bot.services.verification.session_service import SessionService


class VerificationService:
    """Orchestrates the entire Verification State Machine."""

    def __init__(self) -> None:
        self.providers: dict[str, CaptchaProvider] = {
            "image": ImageCaptchaProvider(),
            "math": MathCaptchaProvider(),
            "word": WordCaptchaProvider(),
        }

    async def initiate_verification(
        self, session: AsyncSession, member: discord.Member, settings: VerificationSettings
    ) -> VerificationSession | None:
        """Called when a member joins. Calculates risk and initiates session."""
        if not settings.enabled:
            return None

        # 1. Assign Quarantine Role
        if settings.quarantine_role_id:
            role = member.guild.get_role(settings.quarantine_role_id)
            if role:
                try:
                    await member.add_roles(role, reason="Verification Quarantine")
                except discord.HTTPException:
                    pass

        # 2. Calculate Risk
        risk_score = await RiskEngineService.calculate_risk(member)

        # 3. Determine Mode
        v_type = settings.verification_type
        if v_type == "adaptive":
            v_type = RiskEngineService.select_provider(risk_score, settings.risk_threshold_high)

        if risk_score >= settings.risk_threshold_high and settings.verification_type != "manual":
            v_type = "manual"  # Force manual if extremely high risk

        # 4. Generate Challenge if provider exists
        expected_answer = None
        challenge_data = None
        if v_type in self.providers:
            challenge = await self.providers[v_type].generate_challenge(member.id)
            expected_answer = challenge.expected_answer
            challenge_data = challenge

        # 5. Create Database Session
        v_session = await SessionService.create_session(
            session=session,
            guild_id=member.guild.id,
            user_id=member.id,
            verification_type=v_type,
            risk_score=risk_score,
            expected_answer=expected_answer,
            timeout_minutes=settings.timeout_minutes,
        )

        if v_type == "manual":
            v_session.state = "manual_review"
            await session.flush()

        # Broadcast Event
        await StreamingService.broadcast(
            guild_id=member.guild.id,
            event_type="VERIFICATION_STARTED",
            payload={"user_id": str(member.id), "type": v_type, "risk_score": risk_score},
        )

        return v_session

    async def process_answer(
        self,
        session: AsyncSession,
        member: discord.Member,
        token: str,
        user_provided: str,
        settings: VerificationSettings,
    ) -> bool:
        """Validates a user's answer and processes state transitions."""
        v_session = await SessionService.get_session(session, token)

        if not v_session or v_session.state != "challenge_issued":
            return False

        if v_session.expires_at < datetime.datetime.now(datetime.timezone.utc):
            v_session.state = "expired"
            await session.flush()
            return False

        # Validate
        is_valid = False
        v_type = v_session.verification_type
        if v_type in self.providers:
            is_valid = await self.providers[v_type].validate_answer(
                v_session.expected_answer or "", user_provided
            )
        elif v_type == "button":
            is_valid = True  # Button clicks don't need answer validation

        if is_valid:
            await SessionService.mark_success(session, token)
            await self._apply_success_roles(member, settings)
            await self._log_history(session, v_session, "success")

            await StreamingService.broadcast(
                guild_id=member.guild.id,
                event_type="VERIFICATION_SUCCESS",
                payload={"user_id": str(member.id)},
            )
            return True

        # Failed Attempt
        await SessionService.increment_attempts(session, token)
        if v_session.attempts + 1 >= settings.max_attempts:
            v_session.state = "failed"
            await self._log_history(session, v_session, "failed")

            await StreamingService.broadcast(
                guild_id=member.guild.id,
                event_type="VERIFICATION_FAILED",
                payload={"user_id": str(member.id)},
            )
        await session.flush()
        return False

    async def _apply_success_roles(
        self, member: discord.Member, settings: VerificationSettings
    ) -> None:
        """Remove quarantine and assign verified/temporary roles."""
        roles_to_add = []
        roles_to_remove = []

        if settings.quarantine_role_id:
            r = member.guild.get_role(settings.quarantine_role_id)
            if r:
                roles_to_remove.append(r)

        if settings.verified_role_id:
            r = member.guild.get_role(settings.verified_role_id)
            if r:
                roles_to_add.append(r)

        if settings.temporary_role_id:
            r = member.guild.get_role(settings.temporary_role_id)
            if r:
                roles_to_add.append(r)

        if roles_to_remove:
            try:
                await member.remove_roles(*roles_to_remove, reason="Verification Passed")
            except discord.HTTPException:
                pass

        if roles_to_add:
            try:
                await member.add_roles(*roles_to_add, reason="Verification Passed")
            except discord.HTTPException:
                pass

    async def _log_history(
        self, session: AsyncSession, v_session: VerificationSession, result: str
    ) -> None:
        """Write to the permanent VerificationHistory table."""
        now = datetime.datetime.now(datetime.timezone.utc)
        time_taken = int((now - v_session.created_at).total_seconds())

        history = VerificationHistory(
            guild_id=v_session.guild_id,
            user_id=v_session.user_id,
            result=result,
            verification_type=v_session.verification_type,
            risk_score=v_session.risk_score,
            time_taken_seconds=time_taken,
        )
        session.add(history)
