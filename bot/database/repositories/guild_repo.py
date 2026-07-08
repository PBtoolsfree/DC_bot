"""Guild repository — CRUD operations for guild configuration.

All methods accept an AsyncSession and operate within its transaction.
The caller (typically a service layer) manages the session lifecycle.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.guild import GuildConfig, GuildModuleSettings, GuildPremium
from bot.utils.logger import get_logger

logger = get_logger(__name__)


class GuildRepository:
    """Data access layer for guild-related models.

    This repository provides typed, reusable query methods
    for GuildConfig, GuildModuleSettings, and GuildPremium.
    """

    # ------------------------------------------------------------------
    # GuildConfig CRUD
    # ------------------------------------------------------------------

    @staticmethod
    async def get_config(session: AsyncSession, guild_id: int) -> GuildConfig | None:
        """Get a guild's configuration by its Discord ID.

        Args:
            session: Active database session.
            guild_id: Discord guild snowflake ID.

        Returns:
            GuildConfig if found, None otherwise.
        """
        result = await session.execute(select(GuildConfig).where(GuildConfig.id == guild_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_or_create_config(
        session: AsyncSession,
        guild_id: int,
        name: str = "Unknown",
        owner_id: int = 0,
    ) -> GuildConfig:
        """Get an existing guild config or create a new one with defaults.

        This is the primary method for ensuring a guild has a config row.
        Called on guild_join events and before any config reads.

        Args:
            session: Active database session.
            guild_id: Discord guild snowflake ID.
            name: Guild display name.
            owner_id: Guild owner's Discord user ID.

        Returns:
            The existing or newly created GuildConfig.
        """
        config = await GuildRepository.get_config(session, guild_id)
        if config is not None:
            return config

        config = GuildConfig(
            id=guild_id,
            name=name,
            owner_id=owner_id,
        )
        session.add(config)
        await session.flush()
        logger.info("guild_repo.config_created", guild_id=guild_id, name=name)
        return config

    @staticmethod
    async def update_config(
        session: AsyncSession,
        guild_id: int,
        **kwargs: object,
    ) -> GuildConfig | None:
        """Update specific fields on a guild's configuration.

        Args:
            session: Active database session.
            guild_id: Discord guild snowflake ID.
            **kwargs: Field names and their new values.

        Returns:
            Updated GuildConfig, or None if guild not found.
        """
        config = await GuildRepository.get_config(session, guild_id)
        if config is None:
            return None

        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

        await session.flush()
        return config

    @staticmethod
    async def delete_config(session: AsyncSession, guild_id: int) -> bool:
        """Delete a guild's configuration and all related data (cascade).

        Args:
            session: Active database session.
            guild_id: Discord guild snowflake ID.

        Returns:
            True if deleted, False if not found.
        """
        config = await GuildRepository.get_config(session, guild_id)
        if config is None:
            return False

        await session.delete(config)
        await session.flush()
        logger.info("guild_repo.config_deleted", guild_id=guild_id)
        return True

    # ------------------------------------------------------------------
    # GuildModuleSettings CRUD
    # ------------------------------------------------------------------

    @staticmethod
    async def get_module_settings(
        session: AsyncSession,
        guild_id: int,
        module_name: str,
    ) -> GuildModuleSettings | None:
        """Get a specific module's settings for a guild.

        Args:
            session: Active database session.
            guild_id: Discord guild snowflake ID.
            module_name: Module identifier (e.g., 'automod', 'security').

        Returns:
            GuildModuleSettings if found, None otherwise.
        """
        result = await session.execute(
            select(GuildModuleSettings).where(
                GuildModuleSettings.guild_id == guild_id,
                GuildModuleSettings.module_name == module_name,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_or_create_module_settings(
        session: AsyncSession,
        guild_id: int,
        module_name: str,
        default_config: dict | None = None,  # type: ignore[type-arg]
    ) -> GuildModuleSettings:
        """Get or create module settings with sensible defaults.

        Args:
            session: Active database session.
            guild_id: Discord guild snowflake ID.
            module_name: Module identifier.
            default_config: Default JSONB config if creating new.

        Returns:
            The existing or newly created GuildModuleSettings.
        """
        settings = await GuildRepository.get_module_settings(session, guild_id, module_name)
        if settings is not None:
            return settings

        settings = GuildModuleSettings(
            guild_id=guild_id,
            module_name=module_name,
            enabled=False,
            config=default_config or {},
        )
        session.add(settings)
        await session.flush()
        return settings

    @staticmethod
    async def update_module_settings(
        session: AsyncSession,
        guild_id: int,
        module_name: str,
        enabled: bool | None = None,
        config: dict | None = None,  # type: ignore[type-arg]
    ) -> GuildModuleSettings | None:
        """Update a module's enabled state and/or config.

        Args:
            session: Active database session.
            guild_id: Discord guild snowflake ID.
            module_name: Module identifier.
            enabled: New enabled state (None = don't change).
            config: New config dict (None = don't change).

        Returns:
            Updated settings, or None if not found.
        """
        settings = await GuildRepository.get_module_settings(session, guild_id, module_name)
        if settings is None:
            return None

        if enabled is not None:
            settings.enabled = enabled
        if config is not None:
            settings.config = config

        await session.flush()
        return settings

    @staticmethod
    async def get_all_module_settings(
        session: AsyncSession,
        guild_id: int,
    ) -> list[GuildModuleSettings]:
        """Get all module settings for a guild.

        Args:
            session: Active database session.
            guild_id: Discord guild snowflake ID.

        Returns:
            List of all GuildModuleSettings for this guild.
        """
        result = await session.execute(
            select(GuildModuleSettings).where(GuildModuleSettings.guild_id == guild_id)
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # GuildPremium CRUD
    # ------------------------------------------------------------------

    @staticmethod
    async def get_premium(
        session: AsyncSession,
        guild_id: int,
    ) -> GuildPremium | None:
        """Get a guild's premium subscription info.

        Args:
            session: Active database session.
            guild_id: Discord guild snowflake ID.

        Returns:
            GuildPremium if found, None otherwise.
        """
        result = await session.execute(
            select(GuildPremium).where(GuildPremium.guild_id == guild_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def is_premium(session: AsyncSession, guild_id: int) -> bool:
        """Check if a guild has an active premium subscription.

        Args:
            session: Active database session.
            guild_id: Discord guild snowflake ID.

        Returns:
            True if the guild has active premium.
        """
        premium = await GuildRepository.get_premium(session, guild_id)
        return premium is not None and premium.is_active
