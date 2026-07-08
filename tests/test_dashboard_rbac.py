"""Unit tests for Dashboard RBAC System."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from bot.database.models.dashboard import DashboardMember
from dashboard.backend.services.rbac_service import RBACService
from dashboard.shared.permissions.enums import DashboardRole


@pytest.mark.asyncio
async def test_rbac_owner_has_all_perms() -> None:
    """Test that an owner has all permissions."""
    mock_session = AsyncMock()

    mock_member = DashboardMember(role=DashboardRole.OWNER)

    # Mock the DB query
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_member
    mock_session.execute.return_value = mock_result

    has_perm = await RBACService.has_permission(mock_session, 123, 456, "manage_automod")
    assert has_perm is True


@pytest.mark.asyncio
async def test_rbac_custom_permissions() -> None:
    """Test custom granular permissions."""
    mock_session = AsyncMock()

    mock_member = DashboardMember(
        role=DashboardRole.CUSTOM, permissions={"manage_security": True, "manage_automod": False}
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_member
    mock_session.execute.return_value = mock_result

    assert await RBACService.has_permission(mock_session, 123, 456, "manage_security") is True
    assert await RBACService.has_permission(mock_session, 123, 456, "manage_automod") is False
    assert await RBACService.has_permission(mock_session, 123, 456, "manage_logs") is False
