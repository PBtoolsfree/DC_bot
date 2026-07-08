"""Async database engine and session management.

Provides a centralized database engine class that manages:
- Connection pool creation and configuration
- Session factory for request-scoped sessions
- Schema initialization (create_all)
- Graceful connection cleanup

Usage:
    db = DatabaseEngine(settings)
    await db.initialize()

    async with db.session() as session:
        result = await session.execute(select(MyModel))
        ...

    await db.close()
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from bot.utils.logger import get_logger

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from bot.config import BotSettings

logger = get_logger(__name__)


class DatabaseEngine:
    """Manages the async SQLAlchemy engine and session factory.

    This class encapsulates all database connection logic and provides
    a clean interface for the rest of the application.

    Attributes:
        engine: The async SQLAlchemy engine (connection pool).
        session_factory: Factory for creating new async sessions.
    """

    def __init__(self, settings: BotSettings) -> None:
        """Create a new DatabaseEngine.

        Args:
            settings: Application settings containing database configuration.
        """
        self._settings = settings
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    @property
    def engine(self) -> AsyncEngine:
        """Get the database engine, raising if not initialized."""
        if self._engine is None:
            raise RuntimeError(
                "Database engine not initialized. Call `await db.initialize()` first."
            )
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get the session factory, raising if not initialized."""
        if self._session_factory is None:
            raise RuntimeError(
                "Session factory not initialized. Call `await db.initialize()` first."
            )
        return self._session_factory

    async def initialize(self) -> None:
        """Create the engine, session factory, and database tables.

        This must be called before any database operations. It:
        1. Creates the async engine with connection pooling
        2. Creates the session factory
        3. Creates all tables from the ORM models (safe for existing tables)
        """
        logger.info(
            "database.initializing",
            pool_size=self._settings.database_pool_size,
            max_overflow=self._settings.database_max_overflow,
        )

        self._engine = create_async_engine(
            self._settings.database_url,
            echo=self._settings.database_echo,
            pool_size=self._settings.database_pool_size,
            max_overflow=self._settings.database_max_overflow,
            pool_recycle=self._settings.database_pool_recycle,
            pool_pre_ping=True,
        )

        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

        # Create tables (Alembic is preferred for production migrations,
        # but create_all is safe and idempotent for initial setup)
        from bot.database.models.base import Base

        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("database.initialized")

    async def close(self) -> None:
        """Dispose of the engine and close all pooled connections."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("database.closed")

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Provide a transactional async session scope.

        Usage:
            async with db.session() as session:
                result = await session.execute(select(MyModel))
                # session auto-commits on success, auto-rollbacks on error

        Yields:
            AsyncSession: A short-lived database session.

        Raises:
            RuntimeError: If the database has not been initialized.
        """
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
