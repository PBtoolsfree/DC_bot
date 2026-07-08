"""Tests for the permissions utility module."""

from __future__ import annotations

from unittest.mock import MagicMock

from bot.utils.permissions import (
    PermissionLevel,
    check_bot_hierarchy,
    check_hierarchy,
    get_permission_level,
)
from tests.conftest import MockRole


class TestGetPermissionLevel:
    """Tests for get_permission_level function."""

    def test_bot_owner_highest_priority(self) -> None:
        """Bot owner should get BOT_OWNER level regardless of Discord perms."""
        member = MagicMock()
        member.id = 12345
        member.guild = MagicMock()
        member.guild.owner_id = 99999  # Not the guild owner
        member.guild_permissions = MagicMock()
        member.guild_permissions.administrator = False
        member.guild_permissions.manage_guild = False
        member.guild_permissions.manage_channels = False
        member.guild_permissions.manage_messages = False
        member.guild_permissions.kick_members = False
        member.guild_permissions.ban_members = False

        level = get_permission_level(member, bot_owner_ids={12345})
        assert level == PermissionLevel.BOT_OWNER

    def test_server_owner(self) -> None:
        """Server owner should get SERVER_OWNER level."""
        member = MagicMock()
        member.id = 12345
        member.guild = MagicMock()
        member.guild.owner_id = 12345
        member.guild_permissions = MagicMock()
        member.guild_permissions.administrator = False

        level = get_permission_level(member)
        assert level == PermissionLevel.SERVER_OWNER

    def test_administrator(self) -> None:
        """Member with administrator permission should get ADMIN level."""
        member = MagicMock()
        member.id = 12345
        member.guild = MagicMock()
        member.guild.owner_id = 99999
        member.guild_permissions = MagicMock()
        member.guild_permissions.administrator = True

        level = get_permission_level(member)
        assert level == PermissionLevel.ADMIN

    def test_moderator_manage_guild(self) -> None:
        """Member with manage_guild should get MODERATOR level."""
        member = MagicMock()
        member.id = 12345
        member.guild = MagicMock()
        member.guild.owner_id = 99999
        member.guild_permissions = MagicMock()
        member.guild_permissions.administrator = False
        member.guild_permissions.manage_guild = True
        member.guild_permissions.manage_channels = False

        level = get_permission_level(member)
        assert level == PermissionLevel.MODERATOR

    def test_moderator_manage_channels(self) -> None:
        """Member with manage_channels should get MODERATOR level."""
        member = MagicMock()
        member.id = 12345
        member.guild = MagicMock()
        member.guild.owner_id = 99999
        member.guild_permissions = MagicMock()
        member.guild_permissions.administrator = False
        member.guild_permissions.manage_guild = False
        member.guild_permissions.manage_channels = True

        level = get_permission_level(member)
        assert level == PermissionLevel.MODERATOR

    def test_helper_manage_messages(self) -> None:
        """Member with manage_messages should get HELPER level."""
        member = MagicMock()
        member.id = 12345
        member.guild = MagicMock()
        member.guild.owner_id = 99999
        member.guild_permissions = MagicMock()
        member.guild_permissions.administrator = False
        member.guild_permissions.manage_guild = False
        member.guild_permissions.manage_channels = False
        member.guild_permissions.manage_messages = True
        member.guild_permissions.kick_members = False
        member.guild_permissions.ban_members = False

        level = get_permission_level(member)
        assert level == PermissionLevel.HELPER

    def test_helper_kick_members(self) -> None:
        """Member with kick_members should get HELPER level."""
        member = MagicMock()
        member.id = 12345
        member.guild = MagicMock()
        member.guild.owner_id = 99999
        member.guild_permissions = MagicMock()
        member.guild_permissions.administrator = False
        member.guild_permissions.manage_guild = False
        member.guild_permissions.manage_channels = False
        member.guild_permissions.manage_messages = False
        member.guild_permissions.kick_members = True
        member.guild_permissions.ban_members = False

        level = get_permission_level(member)
        assert level == PermissionLevel.HELPER

    def test_regular_member(self) -> None:
        """Member with no special permissions should get MEMBER level."""
        member = MagicMock()
        member.id = 12345
        member.guild = MagicMock()
        member.guild.owner_id = 99999
        member.guild_permissions = MagicMock()
        member.guild_permissions.administrator = False
        member.guild_permissions.manage_guild = False
        member.guild_permissions.manage_channels = False
        member.guild_permissions.manage_messages = False
        member.guild_permissions.kick_members = False
        member.guild_permissions.ban_members = False

        level = get_permission_level(member)
        assert level == PermissionLevel.MEMBER

    def test_permission_level_ordering(self) -> None:
        """Permission levels should be properly ordered."""
        assert PermissionLevel.MEMBER < PermissionLevel.HELPER
        assert PermissionLevel.HELPER < PermissionLevel.MODERATOR
        assert PermissionLevel.MODERATOR < PermissionLevel.ADMIN
        assert PermissionLevel.ADMIN < PermissionLevel.SERVER_OWNER
        assert PermissionLevel.SERVER_OWNER < PermissionLevel.BOT_OWNER


class TestCheckHierarchy:
    """Tests for the check_hierarchy function."""

    def test_higher_role_outranks(self) -> None:
        """Actor with higher role position should outrank target."""
        actor = MagicMock()
        actor.guild = MagicMock()
        actor.guild.owner_id = 99999
        actor.top_role = MockRole(10)
        actor.id = 11111

        target = MagicMock()
        target.guild = actor.guild
        target.top_role = MockRole(5)
        target.id = 22222

        assert check_hierarchy(actor, target) is True

    def test_lower_role_does_not_outrank(self) -> None:
        """Actor with lower role position should NOT outrank target."""
        actor = MagicMock()
        actor.guild = MagicMock()
        actor.guild.owner_id = 99999
        actor.top_role = MockRole(3)
        actor.id = 11111

        target = MagicMock()
        target.guild = actor.guild
        target.top_role = MockRole(8)
        target.id = 22222

        assert check_hierarchy(actor, target) is False

    def test_server_owner_always_outranks(self) -> None:
        """Server owner should always outrank anyone."""
        actor = MagicMock()
        actor.id = 12345
        actor.guild = MagicMock()
        actor.guild.owner_id = 12345  # Actor IS the owner
        actor.top_role = MockRole(1)  # Even with low role

        target = MagicMock()
        target.guild = actor.guild
        target.top_role = MockRole(100)
        target.id = 99999

        assert check_hierarchy(actor, target) is True

    def test_cannot_outrank_server_owner(self) -> None:
        """Nobody should outrank the server owner (except bot owner check)."""
        actor = MagicMock()
        actor.id = 11111
        actor.guild = MagicMock()
        actor.guild.owner_id = 99999  # Target IS the owner
        actor.top_role = MockRole(100)

        target = MagicMock()
        target.guild = actor.guild
        target.top_role = MockRole(1)
        target.id = 99999  # The owner

        assert check_hierarchy(actor, target) is False


class TestCheckBotHierarchy:
    """Tests for the check_bot_hierarchy function."""

    def test_bot_outranks_lower_member(self) -> None:
        """Bot with higher role should outrank a lower member."""
        bot_member = MagicMock()
        bot_member.top_role = MockRole(10)

        target = MagicMock()
        target.guild = MagicMock()
        target.guild.owner_id = 99999
        target.top_role = MockRole(5)
        target.id = 22222

        assert check_bot_hierarchy(bot_member, target) is True

    def test_bot_cannot_outrank_owner(self) -> None:
        """Bot should never outrank the server owner."""
        bot_member = MagicMock()
        bot_member.top_role = MockRole(100)

        target = MagicMock()
        target.guild = MagicMock()
        target.guild.owner_id = 12345
        target.id = 12345  # Target IS the owner

        assert check_bot_hierarchy(bot_member, target) is False
