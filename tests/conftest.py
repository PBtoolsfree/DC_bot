"""Pytest fixtures shared across all test modules.

Provides:
- In-memory SQLite database for testing (no PostgreSQL required)
- Async session factory
- Mock bot instance
- Mock Discord objects (guild, member, channel)
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from bot.database.models.base import Base

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

# ======================================================================
# Event Loop
# ======================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ======================================================================
# Database Fixtures
# ======================================================================


@pytest_asyncio.fixture(scope="function")
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create an in-memory SQLite engine for testing.

    Each test function gets a fresh database with all tables created.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(
    db_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session.

    Wraps each test in a transaction that is rolled back after the test,
    ensuring test isolation.
    """
    session_factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with session_factory() as session:
        yield session
        await session.rollback()


# ======================================================================
# Mock Discord Objects
# ======================================================================


class MockRole:
    def __init__(self, position: int):
        self.position = position

    def __gt__(self, other: MockRole) -> bool:
        return self.position > other.position

    def __lt__(self, other: MockRole) -> bool:
        return self.position < other.position


@pytest.fixture
def mock_guild() -> MagicMock:
    """Create a mock Discord guild."""
    guild = MagicMock(
        spec=[
            "id",
            "name",
            "owner_id",
            "member_count",
            "icon",
            "me",
            "members",
            "features",
            "verification_level",
            "explicit_content_filter",
            "roles",
        ]
    )
    guild.id = 123456789012345678
    guild.name = "Test Server"
    guild.owner_id = 123456789012345678
    guild.member_count = 100
    guild.features = ["COMMUNITY"]
    guild.verification_level = discord.VerificationLevel.high
    guild.explicit_content_filter = discord.ContentFilter.all_members
    guild.roles = []

    # Mock bot member (the bot itself in the guild)
    bot_member = MagicMock()
    bot_member.id = 999999999999999999
    bot_member.top_role = MockRole(10)
    guild.me = bot_member

    return guild


@pytest.fixture
def mock_member(mock_guild: MagicMock) -> MagicMock:
    """Create a mock Discord member."""
    member = MagicMock()
    member.id = 222222222222222222
    member.name = "TestUser"
    member.display_name = "Test User"
    member.guild = mock_guild
    member.guild_permissions = MagicMock()
    member.guild_permissions.administrator = False
    member.guild_permissions.manage_guild = False
    member.guild_permissions.manage_channels = False
    member.guild_permissions.manage_messages = False
    member.guild_permissions.kick_members = False
    member.guild_permissions.ban_members = False
    member.top_role = MockRole(5)
    member.mention = f"<@{member.id}>"
    member.display_avatar = MagicMock()
    member.display_avatar.url = "https://cdn.discordapp.com/embed/avatars/0.png"
    return member


@pytest.fixture
def mock_admin_member(mock_guild: MagicMock) -> MagicMock:
    """Create a mock Discord member with admin permissions."""
    member = MagicMock()
    member.id = 333333333333333333
    member.name = "AdminUser"
    member.display_name = "Admin User"
    member.guild = mock_guild
    member.guild_permissions = MagicMock()
    member.guild_permissions.administrator = True
    member.guild_permissions.manage_guild = True
    member.guild_permissions.manage_channels = True
    member.guild_permissions.manage_messages = True
    member.guild_permissions.kick_members = True
    member.guild_permissions.ban_members = True
    member.top_role = MockRole(8)
    member.mention = f"<@{member.id}>"
    member.display_avatar = MagicMock()
    member.display_avatar.url = "https://cdn.discordapp.com/embed/avatars/0.png"
    return member


@pytest.fixture
def mock_interaction(mock_guild: MagicMock, mock_admin_member: MagicMock) -> MagicMock:
    """Create a mock Discord interaction for slash commands."""
    interaction = MagicMock()
    interaction.guild = mock_guild
    interaction.user = mock_admin_member
    interaction.response = AsyncMock()
    interaction.response.is_done.return_value = False
    interaction.response.send_message = AsyncMock()
    interaction.followup = AsyncMock()
    interaction.followup.send = AsyncMock()
    interaction.original_response = AsyncMock()

    # Mock the bot client
    bot = MagicMock()
    bot.settings = MagicMock()
    bot.settings.bot_owner_ids = []
    bot.db = MagicMock()
    session_mock = AsyncMock()
    bot.db.session.return_value.__aenter__.return_value = session_mock
    bot.db.session.return_value.__aexit__ = AsyncMock(return_value=None)
    interaction.client = bot

    return interaction


@pytest.fixture
def mock_bot() -> MagicMock:
    """Create a mock bot instance."""
    bot = MagicMock()
    bot.settings = MagicMock()
    bot.settings.bot_owner_ids = []
    bot.db = MagicMock()
    session_mock = AsyncMock()
    bot.db.session.return_value.__aenter__.return_value = session_mock
    bot.db.session.return_value.__aexit__ = AsyncMock(return_value=None)
    return bot


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock environment variables for BotSettings validation."""
    monkeypatch.setenv("DISCORD_TOKEN", "test_token_123")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
