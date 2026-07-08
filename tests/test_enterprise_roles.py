"""Tests for Reaction Roles."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bot.services.roles.reaction_role_service import ReactionRoleService
from bot.database.models.roles import ReactionRoleGroup


@pytest.mark.asyncio
@patch("bot.services.roles.reaction_role_service.StreamingService")
async def test_reaction_role_exclusivity(mock_streaming: AsyncMock) -> None:
    mock_streaming.broadcast = AsyncMock()
    session = AsyncMock()
    
    mock_member = MagicMock()
    mock_member.add_roles = AsyncMock()
    mock_member.remove_roles = AsyncMock()
    
    mock_role = MagicMock()
    mock_role.id = 111
    mock_role.name = "Red"
    
    # User currently has a different role from the same group
    existing_role = MagicMock()
    existing_role.id = 222
    mock_member.roles = [existing_role]
    mock_member.guild.get_role.return_value = mock_role
    
    # DB returns max_roles = 1 (Single Choice)
    group = ReactionRoleGroup(id=1, name="Colors", min_roles=0, max_roles=1, required_roles=[], blacklisted_roles=[])
    
    # Mocking session scalar
    mock_group_result = MagicMock()
    mock_group_result.scalar_one_or_none.return_value = group
    
    # Mocking group items (222 is in the group)
    mock_items_result = MagicMock()
    mock_items_result.scalars().all.return_value = [111, 222]
    
    session.execute.side_effect = [mock_group_result, mock_items_result]
    
    # The member tries to add 111 while they already have 222.
    # Since max_roles=1, it should automatically swap (remove 222, add 111)
    
    success, msg = await ReactionRoleService.toggle_role(session, mock_member, group_id=1, role_id=111)
    
    assert success is True
    assert msg == "Added Red."
    
    mock_member.remove_roles.assert_called_once_with(existing_role, reason="Reaction Role swap")
    mock_member.add_roles.assert_called_once_with(mock_role, reason="Reaction Role toggle")
