"""Background task to clean up expired verification sessions."""

import contextlib
import datetime

from discord.ext import commands, tasks
from sqlalchemy import delete, select

from bot.database.core import db
from bot.database.models.verification import VerificationSession
from bot.services.verification.verification_service import VerificationService
from bot.utils.logger import get_logger

logger = get_logger(__name__)


class VerificationCleanupTask(commands.Cog):
    """Periodically cleans up expired verification sessions."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.cleanup_expired_sessions.start()

    def cog_unload(self) -> None:
        self.cleanup_expired_sessions.cancel()

    @tasks.loop(minutes=5)
    async def cleanup_expired_sessions(self) -> None:
        """Finds expired sessions and processes them (kicks or deletes)."""
        now = datetime.datetime.now(datetime.timezone.utc)

        try:
            async with db.session() as session:
                # Find expired pending sessions
                stmt = select(VerificationSession).where(
                    VerificationSession.expires_at < now,
                    VerificationSession.state.in_(["pending", "challenge_issued"]),
                )
                result = await session.execute(stmt)
                expired_sessions = result.scalars().all()

                for v_session in expired_sessions:
                    guild = self.bot.get_guild(v_session.guild_id)
                    if not guild:
                        continue

                    # Fetch settings to see if we should kick
                    from bot.database.repositories.verification_repo import VerificationRepository

                    settings = await VerificationRepository.get_settings(session, guild.id)

                    if settings and settings.kick_on_timeout:
                        member = guild.get_member(v_session.user_id)
                        if member:
                            with contextlib.suppress(Exception):
                                await member.kick(reason="Verification Timeout")

                    v_session.state = "timeout"

                    # Log History
                    v_service = VerificationService()
                    await v_service._log_history(session, v_session, "timeout")

                # Delete old sessions completely after they are logged as timeout
                delete_stmt = delete(VerificationSession).where(
                    VerificationSession.expires_at < now
                )
                await session.execute(delete_stmt)

                await session.commit()

        except Exception as e:
            logger.error("verification_cleanup_failed", error=str(e))

    @cleanup_expired_sessions.before_loop
    async def before_cleanup(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VerificationCleanupTask(bot))
