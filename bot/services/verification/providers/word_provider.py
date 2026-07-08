"""Word CAPTCHA provider."""

import random

from bot.services.verification.providers.base import CaptchaProvider, CaptchaChallenge

WORDS = [
    "server", "discord", "security", "verify", "human", 
    "shield", "protect", "welcome", "community", "member"
]


class WordCaptchaProvider(CaptchaProvider):
    """Generates text-based word challenges."""

    @property
    def provider_id(self) -> str:
        return "word"

    async def generate_challenge(self, user_id: int) -> CaptchaChallenge:
        """Pick a random word and ask the user to type it."""
        expected = random.choice(WORDS)
        
        # Obfuscate the prompt slightly to prevent simple regex bots
        obfuscated = expected.replace("", " ").strip()
        prompt = f"Please type the following word: **`{obfuscated}`** (ignore spaces)."
        
        return CaptchaChallenge(
            expected_answer=expected,
            prompt=prompt
        )

    async def validate_answer(self, expected_answer: str, user_provided_answer: str) -> bool:
        """Validate word answer case-insensitively, ignoring spaces."""
        cleaned_user = user_provided_answer.replace(" ", "").strip().lower()
        return expected_answer.lower() == cleaned_user
