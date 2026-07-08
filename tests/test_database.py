"""Tests for database models and repositories."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.guild import GuildConfig, GuildModuleSettings
from bot.database.models.member import MemberData, ModAction, ModActionType, Warning
from bot.database.repositories.guild_repo import GuildRepository
from bot.database.repositories.member_repo import MemberRepository


# ======================================================================
# Guild Repository Tests
# ======================================================================


class TestGuildRepository:
    """Tests for GuildRepository CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_guild_config(self, db_session: AsyncSession) -> None:
        """Should create a new guild config with defaults."""
        config = await GuildRepository.get_or_create_config(
            db_session,
            guild_id=123456789,
            name="Test Server",
            owner_id=111111111,
        )
        await db_session.commit()

        assert config.id == 123456789
        assert config.name == "Test Server"
        assert config.owner_id == 111111111
        assert config.welcome_enabled is False
        assert config.locale == "en-US"
        assert config.timezone == "UTC"

    @pytest.mark.asyncio
    async def test_get_existing_config(self, db_session: AsyncSession) -> None:
        """Should return existing config without creating duplicate."""
        # Create first
        config1 = await GuildRepository.get_or_create_config(
            db_session, guild_id=123456789, name="Test Server"
        )
        await db_session.flush()

        # Get again
        config2 = await GuildRepository.get_or_create_config(
            db_session, guild_id=123456789, name="Updated Name"
        )

        assert config1.id == config2.id

    @pytest.mark.asyncio
    async def test_update_config(self, db_session: AsyncSession) -> None:
        """Should update specific fields on a guild config."""
        await GuildRepository.get_or_create_config(
            db_session, guild_id=123456789
        )
        await db_session.flush()

        updated = await GuildRepository.update_config(
            db_session,
            guild_id=123456789,
            welcome_enabled=True,
            welcome_message="Hello {user}!",
            locale="en-GB",
        )

        assert updated is not None
        assert updated.welcome_enabled is True
        assert updated.welcome_message == "Hello {user}!"
        assert updated.locale == "en-GB"

    @pytest.mark.asyncio
    async def test_update_nonexistent_config_returns_none(
        self, db_session: AsyncSession
    ) -> None:
        """Updating a non-existent guild should return None."""
        result = await GuildRepository.update_config(
            db_session, guild_id=999999999, welcome_enabled=True
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_config(self, db_session: AsyncSession) -> None:
        """Should delete a guild config."""
        await GuildRepository.get_or_create_config(
            db_session, guild_id=123456789
        )
        await db_session.flush()

        deleted = await GuildRepository.delete_config(db_session, guild_id=123456789)
        assert deleted is True

        config = await GuildRepository.get_config(db_session, guild_id=123456789)
        assert config is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_config(self, db_session: AsyncSession) -> None:
        """Deleting a non-existent guild should return False."""
        result = await GuildRepository.delete_config(db_session, guild_id=999999999)
        assert result is False

    @pytest.mark.asyncio
    async def test_module_settings_get_or_create(
        self, db_session: AsyncSession
    ) -> None:
        """Should create module settings with defaults."""
        await GuildRepository.get_or_create_config(
            db_session, guild_id=123456789
        )
        await db_session.flush()

        settings = await GuildRepository.get_or_create_module_settings(
            db_session,
            guild_id=123456789,
            module_name="automod",
            default_config={"spam_enabled": True, "spam_threshold": 5},
        )

        assert settings.guild_id == 123456789
        assert settings.module_name == "automod"
        assert settings.enabled is False
        assert settings.config["spam_enabled"] is True
        assert settings.config["spam_threshold"] == 5

    @pytest.mark.asyncio
    async def test_update_module_settings(self, db_session: AsyncSession) -> None:
        """Should update module enabled state and config."""
        await GuildRepository.get_or_create_config(
            db_session, guild_id=123456789
        )
        await db_session.flush()

        await GuildRepository.get_or_create_module_settings(
            db_session, guild_id=123456789, module_name="automod"
        )
        await db_session.flush()

        updated = await GuildRepository.update_module_settings(
            db_session,
            guild_id=123456789,
            module_name="automod",
            enabled=True,
            config={"spam_enabled": True},
        )

        assert updated is not None
        assert updated.enabled is True
        assert updated.config["spam_enabled"] is True

    @pytest.mark.asyncio
    async def test_is_premium_default_false(self, db_session: AsyncSession) -> None:
        """Non-premium guild should return False."""
        await GuildRepository.get_or_create_config(
            db_session, guild_id=123456789
        )
        await db_session.flush()

        assert await GuildRepository.is_premium(db_session, 123456789) is False


# ======================================================================
# Member Repository Tests
# ======================================================================


class TestMemberRepository:
    """Tests for MemberRepository CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_member(self, db_session: AsyncSession) -> None:
        """Should create member data with defaults."""
        # Need a guild first (for FK)
        await GuildRepository.get_or_create_config(
            db_session, guild_id=123456789
        )
        await db_session.flush()

        member = await MemberRepository.get_or_create_member(
            db_session,
            guild_id=123456789,
            user_id=222222222,
            username="TestUser",
            display_name="Test User",
        )

        assert member.guild_id == 123456789
        assert member.user_id == 222222222
        assert member.username == "TestUser"
        assert member.is_muted is False
        assert member.is_verified is False
        assert member.total_warnings == 0
        assert member.total_messages == 0

    @pytest.mark.asyncio
    async def test_add_warning(self, db_session: AsyncSession) -> None:
        """Should create a warning and increment total_warnings."""
        await GuildRepository.get_or_create_config(
            db_session, guild_id=123456789
        )
        await db_session.flush()

        warning = await MemberRepository.add_warning(
            db_session,
            guild_id=123456789,
            user_id=222222222,
            moderator_id=333333333,
            reason="Spamming in general",
        )

        assert warning.id is not None
        assert warning.guild_id == 123456789
        assert warning.user_id == 222222222
        assert warning.moderator_id == 333333333
        assert warning.reason == "Spamming in general"
        assert warning.is_active is True

        # Check member's warning count was incremented
        member = await MemberRepository.get_member(
            db_session, guild_id=123456789, user_id=222222222
        )
        assert member is not None
        assert member.total_warnings == 1

    @pytest.mark.asyncio
    async def test_multiple_warnings(self, db_session: AsyncSession) -> None:
        """Adding multiple warnings should increment total correctly."""
        await GuildRepository.get_or_create_config(
            db_session, guild_id=123456789
        )
        await db_session.flush()

        await MemberRepository.add_warning(
            db_session, 123456789, 222222222, 333333333, "Warning 1"
        )
        await MemberRepository.add_warning(
            db_session, 123456789, 222222222, 333333333, "Warning 2"
        )
        await MemberRepository.add_warning(
            db_session, 123456789, 222222222, 333333333, "Warning 3"
        )

        count = await MemberRepository.get_warning_count(
            db_session, 123456789, 222222222
        )
        assert count == 3

        member = await MemberRepository.get_member(
            db_session, 123456789, 222222222
        )
        assert member is not None
        assert member.total_warnings == 3

    @pytest.mark.asyncio
    async def test_pardon_warning(self, db_session: AsyncSession) -> None:
        """Should deactivate a warning and decrement total."""
        await GuildRepository.get_or_create_config(
            db_session, guild_id=123456789
        )
        await db_session.flush()

        warning = await MemberRepository.add_warning(
            db_session, 123456789, 222222222, 333333333, "Test warning"
        )
        await db_session.flush()

        pardoned = await MemberRepository.pardon_warning(
            db_session, warning.id, pardoned_by=333333333
        )

        assert pardoned is not None
        assert pardoned.is_active is False
        assert pardoned.pardoned_by == 333333333
        assert pardoned.pardoned_at is not None

        member = await MemberRepository.get_member(
            db_session, 123456789, 222222222
        )
        assert member is not None
        assert member.total_warnings == 0

    @pytest.mark.asyncio
    async def test_clear_all_warnings(self, db_session: AsyncSession) -> None:
        """Should clear all active warnings for a member."""
        await GuildRepository.get_or_create_config(
            db_session, guild_id=123456789
        )
        await db_session.flush()

        for i in range(5):
            await MemberRepository.add_warning(
                db_session, 123456789, 222222222, 333333333, f"Warning {i+1}"
            )
        await db_session.flush()

        cleared = await MemberRepository.clear_warnings(
            db_session, 123456789, 222222222, cleared_by=333333333
        )
        assert cleared == 5

        count = await MemberRepository.get_warning_count(
            db_session, 123456789, 222222222
        )
        assert count == 0

    @pytest.mark.asyncio
    async def test_get_active_warnings_only(self, db_session: AsyncSession) -> None:
        """Should return only active warnings when active_only=True."""
        await GuildRepository.get_or_create_config(
            db_session, guild_id=123456789
        )
        await db_session.flush()

        w1 = await MemberRepository.add_warning(
            db_session, 123456789, 222222222, 333333333, "Active 1"
        )
        await MemberRepository.add_warning(
            db_session, 123456789, 222222222, 333333333, "Active 2"
        )
        await db_session.flush()

        # Pardon one
        await MemberRepository.pardon_warning(db_session, w1.id, 333333333)

        active = await MemberRepository.get_warnings(
            db_session, 123456789, 222222222, active_only=True
        )
        assert len(active) == 1
        assert active[0].reason == "Active 2"

        all_warnings = await MemberRepository.get_warnings(
            db_session, 123456789, 222222222, active_only=False
        )
        assert len(all_warnings) == 2

    @pytest.mark.asyncio
    async def test_log_mod_action(self, db_session: AsyncSession) -> None:
        """Should log a moderation action."""
        await GuildRepository.get_or_create_config(
            db_session, guild_id=123456789
        )
        await db_session.flush()

        action = await MemberRepository.log_action(
            db_session,
            guild_id=123456789,
            user_id=222222222,
            moderator_id=333333333,
            action_type=ModActionType.BAN,
            reason="Repeated violations",
            duration_seconds=None,
            details="Final ban after 5 warnings",
        )

        assert action.id is not None
        assert action.action_type == "ban"
        assert action.reason == "Repeated violations"
        assert action.is_automated is False

    @pytest.mark.asyncio
    async def test_log_automated_action(self, db_session: AsyncSession) -> None:
        """Should log an automated moderation action."""
        await GuildRepository.get_or_create_config(
            db_session, guild_id=123456789
        )
        await db_session.flush()

        action = await MemberRepository.log_action(
            db_session,
            guild_id=123456789,
            user_id=222222222,
            moderator_id=999999999,  # Bot ID
            action_type=ModActionType.AUTO_TIMEOUT,
            reason="Spam detected",
            duration_seconds=3600,
            is_automated=True,
        )

        assert action.is_automated is True
        assert action.action_type == "auto_timeout"
        assert action.duration_seconds == 3600

    @pytest.mark.asyncio
    async def test_get_actions_with_filters(self, db_session: AsyncSession) -> None:
        """Should filter mod actions by user and type."""
        await GuildRepository.get_or_create_config(
            db_session, guild_id=123456789
        )
        await db_session.flush()

        # Log various actions
        await MemberRepository.log_action(
            db_session, 123456789, 222222222, 333333333, ModActionType.WARN, "W1"
        )
        await MemberRepository.log_action(
            db_session, 123456789, 222222222, 333333333, ModActionType.WARN, "W2"
        )
        await MemberRepository.log_action(
            db_session, 123456789, 222222222, 333333333, ModActionType.KICK, "K1"
        )
        await MemberRepository.log_action(
            db_session, 123456789, 444444444, 333333333, ModActionType.BAN, "B1"
        )
        await db_session.flush()

        # Filter by user
        user_actions = await MemberRepository.get_actions(
            db_session, 123456789, user_id=222222222
        )
        assert len(user_actions) == 3

        # Filter by type
        warns = await MemberRepository.get_actions(
            db_session, 123456789, action_type=ModActionType.WARN
        )
        assert len(warns) == 2

        # All guild actions
        all_actions = await MemberRepository.get_actions(db_session, 123456789)
        assert len(all_actions) == 4

    @pytest.mark.asyncio
    async def test_get_action_count(self, db_session: AsyncSession) -> None:
        """Should count mod actions correctly."""
        await GuildRepository.get_or_create_config(
            db_session, guild_id=123456789
        )
        await db_session.flush()

        await MemberRepository.log_action(
            db_session, 123456789, 222222222, 333333333, ModActionType.WARN
        )
        await MemberRepository.log_action(
            db_session, 123456789, 222222222, 333333333, ModActionType.KICK
        )
        await db_session.flush()

        total = await MemberRepository.get_action_count(db_session, 123456789)
        assert total == 2

        user_total = await MemberRepository.get_action_count(
            db_session, 123456789, user_id=222222222
        )
        assert user_total == 2

    @pytest.mark.asyncio
    async def test_increment_messages(self, db_session: AsyncSession) -> None:
        """Should increment message count for existing member."""
        await GuildRepository.get_or_create_config(
            db_session, guild_id=123456789
        )
        await db_session.flush()

        await MemberRepository.get_or_create_member(
            db_session, 123456789, 222222222
        )
        await db_session.flush()

        await MemberRepository.increment_messages(db_session, 123456789, 222222222)
        await MemberRepository.increment_messages(db_session, 123456789, 222222222)
        await MemberRepository.increment_messages(db_session, 123456789, 222222222)
        await db_session.flush()

        member = await MemberRepository.get_member(db_session, 123456789, 222222222)
        assert member is not None
        assert member.total_messages == 3
