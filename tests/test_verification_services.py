"""Integration-like tests for Verification Services."""

from unittest.mock import AsyncMock, patch

import pytest

from bot.database.models.verification import VerificationSettings
from bot.services.verification.verification_service import VerificationService


@pytest.fixture
def verification_service() -> VerificationService:
    return VerificationService()


@pytest.mark.asyncio
async def test_initiate_verification_disabled(verification_service: VerificationService) -> None:
    settings = VerificationSettings(enabled=False)
    session = AsyncMock()
    member = AsyncMock()

    v_session = await verification_service.initiate_verification(session, member, settings)
    assert v_session is None


@pytest.mark.asyncio
@patch("bot.services.verification.verification_service.SessionService")
@patch("bot.services.verification.verification_service.RiskEngineService")
@patch("bot.services.verification.verification_service.StreamingService")
async def test_initiate_verification_enabled(
    mock_streaming: AsyncMock,
    mock_risk: AsyncMock,
    mock_session_service: AsyncMock,
    verification_service: VerificationService,
) -> None:
    settings = VerificationSettings(
        enabled=True, verification_type="math", risk_threshold_high=70, timeout_minutes=15
    )

    session = AsyncMock()
    member = AsyncMock()
    member.id = 123
    member.guild.id = 456

    mock_risk.calculate_risk = AsyncMock(return_value=10)

    mock_v_session = AsyncMock()
    mock_v_session.session_id = "test_token"
    mock_session_service.create_session = AsyncMock(return_value=mock_v_session)
    mock_streaming.broadcast = AsyncMock()

    v_session = await verification_service.initiate_verification(session, member, settings)

    assert v_session is not None
    mock_session_service.create_session.assert_called_once()
    mock_streaming.broadcast.assert_called_once()
