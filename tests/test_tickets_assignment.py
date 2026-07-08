"""Tests for Assignment Engine."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from bot.database.models.tickets import TicketCategory
from bot.services.tickets.assignment_service import AssignmentService


@pytest.mark.asyncio
async def test_assign_least_loaded() -> None:
    session = AsyncMock()

    mock_guild = MagicMock()
    mock_role = MagicMock()

    mock_member1 = MagicMock()
    mock_member1.id = 111

    mock_member2 = MagicMock()
    mock_member2.id = 222

    mock_role.members = [mock_member1, mock_member2]
    mock_guild.get_role.return_value = mock_role

    category = TicketCategory(support_team_roles=[999])

    # Mock DB returning workloads: Member 1 has 5 tickets, Member 2 has 1 ticket.
    # So it should assign to Member 2 (id=222)
    mock_result = MagicMock()
    mock_result.all.return_value = [(111, 5), (222, 1)]
    session.execute.return_value = mock_result

    assigned_to = await AssignmentService.assign_least_loaded(session, mock_guild, None, category)

    assert assigned_to == 222
