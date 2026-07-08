"""Service for interacting with Redis, providing an in-memory fallback.

Handles rate limiting, caching, and duplicate detection.
Automatically falls back to a thread-safe in-memory dictionary if Redis is unavailable.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, TypeVar

from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError, TimeoutError as RedisTimeoutError

from bot.config import get_settings
from bot.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class InMemoryCache:
    """A thread-safe, TTL-aware in-memory cache.
    
    Used as a fallback when Redis is unavailable.
    """

    def __init__(self) -> None:
        self._cache: dict[str, tuple[Any, float | None]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            if key not in self._cache:
                return None
            value, expires_at = self._cache[key]
            if expires_at is not None and time.time() > expires_at:
                del self._cache[key]
                return None
            return value

    async def set(self, key: str, value: Any, ex: int | None = None) -> None:
        async with self._lock:
            expires_at = time.time() + ex if ex is not None else None
            self._cache[key] = (value, expires_at)

    async def delete(self, *keys: str) -> int:
        count = 0
        async with self._lock:
            for key in keys:
                if key in self._cache:
                    del self._cache[key]
                    count += 1
        return count

    async def incr(self, key: str, amount: int = 1) -> int:
        async with self._lock:
            if key not in self._cache:
                self._cache[key] = (0, None)
            
            value, expires_at = self._cache[key]
            
            if expires_at is not None and time.time() > expires_at:
                value = 0
                expires_at = None
                
            try:
                new_value = int(value) + amount
            except (ValueError, TypeError):
                new_value = amount
                
            self._cache[key] = (new_value, expires_at)
            return new_value

    async def expire(self, key: str, time_seconds: int) -> bool:
        async with self._lock:
            if key not in self._cache:
                return False
            value, _ = self._cache[key]
            self._cache[key] = (value, time.time() + time_seconds)
            return True

    async def exists(self, key: str) -> bool:
        async with self._lock:
            if key not in self._cache:
                return False
            _, expires_at = self._cache[key]
            if expires_at is not None and time.time() > expires_at:
                del self._cache[key]
                return False
            return True

    async def clear(self) -> None:
        async with self._lock:
            self._cache.clear()


class RedisService:
    """High-level caching and rate limiting service.
    
    Transparently falls back to InMemoryCache if Redis fails.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.redis_url = settings.redis_url
        self.redis: Redis | None = None
        self.fallback = InMemoryCache()
        self.is_connected = False

    async def connect(self) -> None:
        """Establish connection to Redis."""
        try:
            self.redis = Redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=2.0,
                socket_connect_timeout=2.0,
            )
            # Test connection
            await self.redis.ping()
            self.is_connected = True
            logger.info("redis_connected", url=self.redis_url)
        except (RedisConnectionError, RedisTimeoutError) as e:
            self.is_connected = False
            self.redis = None
            logger.warning("redis_connection_failed", error=str(e), fallback="in_memory")
        except Exception as e:
            self.is_connected = False
            self.redis = None
            logger.error("redis_connection_error", error=str(e), fallback="in_memory")

    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.aclose() # type: ignore
            self.is_connected = False

    async def get(self, key: str) -> Any | None:
        if self.is_connected and self.redis:
            try:
                return await self.redis.get(key)
            except Exception as e:
                logger.debug("redis_get_error", key=key, error=str(e))
                self.is_connected = False
        return await self.fallback.get(key)

    async def set(self, key: str, value: Any, ex: int | None = None) -> None:
        if self.is_connected and self.redis:
            try:
                await self.redis.set(key, value, ex=ex)
                return
            except Exception as e:
                logger.debug("redis_set_error", key=key, error=str(e))
                self.is_connected = False
        await self.fallback.set(key, value, ex=ex)

    async def delete(self, *keys: str) -> int:
        if self.is_connected and self.redis:
            try:
                return await self.redis.delete(*keys)
            except Exception as e:
                logger.debug("redis_delete_error", error=str(e))
                self.is_connected = False
        return await self.fallback.delete(*keys)

    async def incr(self, key: str, amount: int = 1) -> int:
        if self.is_connected and self.redis:
            try:
                return await self.redis.incr(key, amount)
            except Exception as e:
                logger.debug("redis_incr_error", key=key, error=str(e))
                self.is_connected = False
        return await self.fallback.incr(key, amount)

    async def expire(self, key: str, time_seconds: int) -> bool:
        if self.is_connected and self.redis:
            try:
                return await self.redis.expire(key, time_seconds)
            except Exception as e:
                logger.debug("redis_expire_error", key=key, error=str(e))
                self.is_connected = False
        return await self.fallback.expire(key, time_seconds)

    async def exists(self, key: str) -> bool:
        if self.is_connected and self.redis:
            try:
                return await self.redis.exists(key) > 0
            except Exception as e:
                logger.debug("redis_exists_error", key=key, error=str(e))
                self.is_connected = False
        return await self.fallback.exists(key)

    # ------------------------------------------------------------------
    # High-level utilities
    # ------------------------------------------------------------------

    async def get_json(self, key: str) -> dict[str, Any] | None:
        """Get and parse a JSON string from cache."""
        data = await self.get(key)
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                pass
        return None

    async def set_json(self, key: str, value: dict[str, Any] | list[Any], ex: int | None = None) -> None:
        """Serialize and set a JSON string in cache."""
        await self.set(key, json.dumps(value), ex=ex)

    async def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Check if a rate limit has been exceeded.
        
        Args:
            key: Unique identifier for the rate limit bucket.
            limit: Maximum number of actions allowed.
            window: Time window in seconds.
            
        Returns:
            True if the action is ALLOWED (under limit).
            False if the action is RATE LIMITED (over limit).
        """
        count = await self.incr(key)
        if count == 1:
            await self.expire(key, window)
            
        return count <= limit
