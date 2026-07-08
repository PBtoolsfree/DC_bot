"""Abstract base class for Captcha Providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from io import BytesIO


@dataclass
class CaptchaChallenge:
    """Represents a generated challenge to be presented to the user."""

    expected_answer: str

    # Optional image data if it's an image captcha
    image_bytes: BytesIO | None = None

    # Text prompt for the user
    prompt: str = "Please solve the captcha."


class CaptchaProvider(ABC):
    """Base provider interface for all Verification challenges."""

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """The unique identifier for this provider (e.g., 'image', 'math')."""

    @abstractmethod
    async def generate_challenge(self, user_id: int) -> CaptchaChallenge:
        """Generate a new challenge for the user."""

    @abstractmethod
    async def validate_answer(self, expected_answer: str, user_provided_answer: str) -> bool:
        """Validate if the user's answer is correct."""
