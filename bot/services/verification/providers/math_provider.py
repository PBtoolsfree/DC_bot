"""Math CAPTCHA provider."""

from bot.services.verification.providers.base import CaptchaChallenge, CaptchaProvider


class MathCaptchaProvider(CaptchaProvider):
    """Generates simple arithmetic challenges."""

    @property
    def provider_id(self) -> str:
        return "math"

    async def generate_challenge(self, _user_id: int) -> CaptchaChallenge:
        """Generate a random addition/subtraction problem."""
        operations = ["+", "-", "*"]
        import secrets

        op = secrets.choice(operations)

        if op == "*":
            a = secrets.randbelow(8) + 2
            b = secrets.randbelow(8) + 2
            expected = a * b
        else:
            import secrets

            a = secrets.randbelow(41) + 10
            b = secrets.randbelow(20) + 1
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
