"""Verification Risk Engine Service."""

import datetime
import re

import discord


class RiskEngineService:
    """Calculates verification risk scores dynamically."""

    @staticmethod
    async def calculate_risk(member: discord.Member) -> int:
        """
        Calculate a risk score from 0 (Safe) to 100 (High Risk).
        Factors:
        - Account age < 7 days (+30)
        - No avatar (+20)
        - Default username pattern (e.g. User1234) (+15)
        - Join velocity/raid mode (Placeholder for caching integration) (+25)
        """
        score = 0

        # 1. Account Age
        now = datetime.datetime.now(datetime.timezone.utc)
        age_days = (now - member.created_at).days
        if age_days < 1:
            score += 40
        elif age_days < 7:
            score += 20

        # 2. Avatar Presence
        if not member.avatar:
            score += 20

        # 3. Username pattern (common bot patterns)
        if re.match(r"^[a-zA-Z]+\d{4,8}$", member.name):
            score += 15

        # Ensure it stays within bounds
        return max(0, min(100, score))

    @staticmethod
    def select_provider(risk_score: int, high_threshold: int) -> str:
        """Select the appropriate provider based on the risk score."""
        if risk_score >= high_threshold:
            return "image"  # Image is the hardest CAPTCHA
        if risk_score >= (high_threshold // 2):
            return "math"
        return "button"  # Lowest risk gets simple button
