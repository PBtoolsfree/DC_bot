"""Voice Tracking Service for XP."""

import logging
import time

logger = logging.getLogger(__name__)


class VoiceSessionService:
    """Tracks time spent in voice using Redis (mocked here as in-memory)."""

    # Mock Redis: user_id -> join_time
    import typing

    _active_sessions: typing.ClassVar[dict[int, float]] = {}

    @classmethod
    async def join_voice(cls, user_id: int) -> None:
        """Mark user as joined."""
        cls._active_sessions[user_id] = time.time()

    @classmethod
    async def leave_voice(cls, user_id: int) -> int:
        """Mark user as left, return minutes spent."""
        join_time = cls._active_sessions.pop(user_id, None)
        if not join_time:
            return 0

        seconds = time.time() - join_time
        return int(seconds // 60)

    @classmethod
    async def get_active_minutes(cls, user_id: int) -> int:
        """Calculate how many minutes so far without popping the session."""
        join_time = cls._active_sessions.get(user_id)
        if not join_time:
            return 0

        seconds = time.time() - join_time
        return int(seconds // 60)

    @classmethod
    async def reset_session(cls, user_id: int) -> None:
        """Resets the timer after committing periodic XP."""
        if user_id in cls._active_sessions:
            cls._active_sessions[user_id] = time.time()
