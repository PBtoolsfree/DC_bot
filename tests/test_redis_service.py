"""Unit tests for the Redis Service and InMemory fallback."""

import asyncio

import pytest
from bot.services.redis_service import InMemoryCache, RedisService


@pytest.fixture
def in_memory_cache() -> InMemoryCache:
    return InMemoryCache()


@pytest.mark.asyncio
class TestInMemoryCache:
    async def test_set_and_get(self, in_memory_cache: InMemoryCache) -> None:
        await in_memory_cache.set("key1", "value1")
        val = await in_memory_cache.get("key1")
        assert val == "value1"

    async def test_get_nonexistent(self, in_memory_cache: InMemoryCache) -> None:
        assert await in_memory_cache.get("key2") is None

    async def test_delete(self, in_memory_cache: InMemoryCache) -> None:
        await in_memory_cache.set("key1", "val1")
        assert await in_memory_cache.exists("key1") is True
        await in_memory_cache.delete("key1")
        assert await in_memory_cache.exists("key1") is False

    async def test_incr(self, in_memory_cache: InMemoryCache) -> None:
        assert await in_memory_cache.incr("counter") == 1
        assert await in_memory_cache.incr("counter") == 2
        assert await in_memory_cache.incr("counter", 5) == 7

    async def test_expiration(self, in_memory_cache: InMemoryCache) -> None:
        await in_memory_cache.set("key1", "val1", ex=1)
        assert await in_memory_cache.get("key1") == "val1"
        await asyncio.sleep(1.1)
        assert await in_memory_cache.get("key1") is None

    async def test_incr_expiration(self, in_memory_cache: InMemoryCache) -> None:
        await in_memory_cache.incr("counter")
        await in_memory_cache.expire("counter", 1)
        await asyncio.sleep(1.1)
        # Should reset to 1 because old value expired
        assert await in_memory_cache.incr("counter") == 1


@pytest.mark.asyncio
class TestRedisServiceFallback:
    # Test that RedisService correctly falls back to in-memory 
    # when connection is not established.
    
    @pytest.fixture
    def redis_service(self) -> RedisService:
        # Do not call .connect() to simulate failure/unavailable
        return RedisService()

    async def test_fallback_get_set(self, redis_service: RedisService) -> None:
        await redis_service.set("test_key", "test_val")
        assert await redis_service.get("test_key") == "test_val"

    async def test_fallback_incr(self, redis_service: RedisService) -> None:
        assert await redis_service.incr("test_counter") == 1
        assert await redis_service.incr("test_counter", 4) == 5

    async def test_rate_limit(self, redis_service: RedisService) -> None:
        # Limit 3 per 1 second window
        assert await redis_service.check_rate_limit("limit_test", 3, 1) is True
        assert await redis_service.check_rate_limit("limit_test", 3, 1) is True
        assert await redis_service.check_rate_limit("limit_test", 3, 1) is True
        assert await redis_service.check_rate_limit("limit_test", 3, 1) is False
