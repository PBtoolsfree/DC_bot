"""Math CAPTCHA provider."""

import random

from bot.services.verification.providers.base import CaptchaChallenge, CaptchaProvider


class MathCaptchaProvider(CaptchaProvider):
    """Generates simple arithmetic challenges."""

    @property
    def provider_id(self) -> str:
        return "math"

    async def generate_challenge(self, user_id: int) -> CaptchaChallenge:
        """Generate a random addition/subtraction problem."""
        operations = ["+", "-", "*"]
        op = random.choice(operations)

        if op == "*":
            a = random.randint(2, 9)
            b = random.randint(2, 9)
            expected = a * b
        else:
            a = random.randint(10, 50)
            b = random.randint(1, 20)
            if op == "-":
                # Ensure positive result
                if b > a:
                    a, b = b, a
                expected = a - b
            else:
                expected = a + b

        prompt = f"What is **{a} {op} {b}**?"

        return CaptchaChallenge(expected_answer=str(expected), prompt=prompt)

    async def validate_answer(self, expected_answer: str, user_provided_answer: str) -> bool:
        """Validate math answer."""
        return expected_answer.strip() == user_provided_answer.strip()
