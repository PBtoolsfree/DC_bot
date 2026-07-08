"""Database dependencies for FastAPI."""

import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.engine import DatabaseEngine

# Use the same database URL or configure it for the dashboard
DATABASE_URL = os.getenv(
    "DATABASE_URL", "sqlite+aiosqlite:///bot_database.db"  # Defaulting to SQLite for dev
)

db = DatabaseEngine(DATABASE_URL)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to inject database sessions into API routes.

    This uses the same database connection pool as the Discord bot.
    """
    if not db._engine:
        await db.init_db()

    async with db.session() as session:
        yield session
