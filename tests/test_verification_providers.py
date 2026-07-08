"""Tests for Captcha Providers."""

import pytest

from bot.services.verification.providers.image_provider import ImageCaptchaProvider
from bot.services.verification.providers.math_provider import MathCaptchaProvider
from bot.services.verification.providers.word_provider import WordCaptchaProvider


@pytest.mark.asyncio
async def test_image_provider() -> None:
    provider = ImageCaptchaProvider()
    challenge = await provider.generate_challenge(123)

    assert len(challenge.expected_answer) == 6
    assert challenge.image_bytes is not None

    assert (
        await provider.validate_answer(challenge.expected_answer, challenge.expected_answer) is True
    )
    assert (
        await provider.validate_answer(challenge.expected_answer, challenge.expected_answer.lower())
        is True
    )
    assert await provider.validate_answer(challenge.expected_answer, "WRONG") is False


@pytest.mark.asyncio
async def test_math_provider() -> None:
    provider = MathCaptchaProvider()
    challenge = await provider.generate_challenge(123)

    assert challenge.expected_answer.isdigit()
    assert (
        await provider.validate_answer(challenge.expected_answer, challenge.expected_answer) is True
    )


@pytest.mark.asyncio
async def test_word_provider() -> None:
    provider = WordCaptchaProvider()
    challenge = await provider.generate_challenge(123)

    assert challenge.expected_answer in [
        "server",
        "discord",
        "security",
        "verify",
        "human",
        "shield",
        "protect",
        "welcome",
        "community",
        "member",
    ]

    # Test whitespace and case insensitivity
    assert (
        await provider.validate_answer(
            challenge.expected_answer, f"  {challenge.expected_answer.upper()}  "
        )
        is True
    )
