"""Anonymous Ticket Relay Service."""

import logging

logger = logging.getLogger(__name__)


class RelayService:
    """Acts as a proxy between a User DM and a Ticket Channel."""

    # In production, this would be a Redis client. We use a mock dict here for the skeleton.
    # The dictionary maps user_id -> ticket_channel_id and ticket_channel_id -> user_id
    # so we can route messages in both directions.
    import typing

    _redis_cache: typing.ClassVar[dict[str, int]] = {}

    @classmethod
    async def establish_relay(cls, user_id: int, ticket_channel_id: int) -> None:
        """Map the user's DMs to the ticket channel."""
        cls._redis_cache[f"user_{user_id}"] = ticket_channel_id
        cls._redis_cache[f"channel_{ticket_channel_id}"] = user_id
        logger.info(f"Relay established: User {user_id} <-> Channel {ticket_channel_id}")

    @classmethod
    async def destroy_relay(cls, user_id: int, ticket_channel_id: int) -> None:
        """Remove the mapping."""
        cls._redis_cache.pop(f"user_{user_id}", None)
        cls._redis_cache.pop(f"channel_{ticket_channel_id}", None)

    @classmethod
    async def get_target_channel(cls, user_id: int) -> int | None:
        """Find where to send the user's DM."""
        return cls._redis_cache.get(f"user_{user_id}")

    @classmethod
    async def get_target_user(cls, channel_id: int) -> int | None:
        """Find where to send the staff's message."""
        return cls._redis_cache.get(f"channel_{channel_id}")
