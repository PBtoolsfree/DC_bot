"""Tests for Ticket State Machine."""

from unittest.mock import AsyncMock, patch

import pytest

from bot.database.models.tickets import Ticket
from bot.services.tickets.ticket_service import TicketService


@pytest.fixture
def ticket() -> Ticket:
    return Ticket(id=1, guild_id=123, owner_id=456, category_id=1, status="open")


@pytest.mark.asyncio
@patch("bot.services.tickets.ticket_service.StreamingService")
async def test_valid_state_transition(mock_streaming: AsyncMock, ticket: Ticket) -> None:
    mock_streaming.broadcast = AsyncMock()
    session = AsyncMock()

    # Open -> Claimed
    success = await TicketService.change_status(session, ticket, "claimed", 999)
    assert success is True
    assert ticket.status == "claimed"
    mock_streaming.broadcast.assert_called_once()


@pytest.mark.asyncio
@patch("bot.services.tickets.ticket_service.StreamingService")
async def test_invalid_state_transition(mock_streaming: AsyncMock, ticket: Ticket) -> None:
    mock_streaming.broadcast = AsyncMock()
    session = AsyncMock()

    # Open -> Archived (Invalid)
    success = await TicketService.change_status(session, ticket, "archived", 999)
    assert success is False
    assert ticket.status == "open"
    mock_streaming.broadcast.assert_not_called()
