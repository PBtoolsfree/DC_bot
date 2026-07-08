"""Image CAPTCHA provider."""

import random
from io import BytesIO

from captcha.image import ImageCaptcha

from bot.services.verification.providers.base import CaptchaChallenge, CaptchaProvider


class ImageCaptchaProvider(CaptchaProvider):
    """Generates visual noise CAPTCHAs."""

    @property
    def provider_id(self) -> str:
        return "image"

    async def generate_challenge(self, user_id: int) -> CaptchaChallenge:
        """Generate a random 6-character alphanumeric image."""
        # Use simple alphanumeric characters avoiding confusing ones like l/1/I or O/0
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        expected = "".join(random.choices(chars, k=6))

        image = ImageCaptcha(width=280, height=90)
        data: BytesIO = image.generate(expected)
        data.seek(0)

        return CaptchaChallenge(
            expected_answer=expected,
            image_bytes=data,
            prompt="Type the 6 characters shown in the image below.",
        )

    async def validate_answer(self, expected_answer: str, user_provided_answer: str) -> bool:
        """Case-insensitive validation."""
        return expected_answer.upper() == user_provided_answer.strip().upper()
