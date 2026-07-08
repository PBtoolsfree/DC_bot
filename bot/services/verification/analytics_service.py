"""Analytics Service for Verification metrics."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.verification import VerificationHistory


class AnalyticsService:
    """Generates verification statistics for the Dashboard."""

    @staticmethod
    async def get_guild_stats(session: AsyncSession, guild_id: int) -> dict[str, Any]:
        """Calculate success/failure rates and average verification time."""

        stmt = (
            select(VerificationHistory.result, func.count(VerificationHistory.id))
            .where(VerificationHistory.guild_id == guild_id)
            .group_by(VerificationHistory.result)
        )
        result = await session.execute(stmt)
        counts = {res: count for res, count in result.all()}

        total = sum(counts.values())
        success_rate = (counts.get("success", 0) / total * 100) if total > 0 else 0

        # Average time for successful verifications
        time_stmt = (
            select(func.avg(VerificationHistory.time_taken_seconds))
            .where(VerificationHistory.guild_id == guild_id)
            .where(VerificationHistory.result == "success")
        )
        time_result = await session.execute(time_stmt)
        avg_time = time_result.scalar() or 0

        return {
            "total_attempts": total,
            "success_rate_percent": round(success_rate, 2),
            "failure_rate_percent": round(100 - success_rate, 2) if total > 0 else 0,
            "average_time_seconds": round(avg_time, 2),
            "breakdown": counts,
        }
