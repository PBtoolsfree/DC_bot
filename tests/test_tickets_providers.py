"""Tests for Transcript Providers."""

import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone

from bot.database.models.tickets import Ticket, TicketMessage
from bot.services.tickets.providers.json_provider import JSONTranscriptProvider
from bot.services.tickets.providers.markdown_provider import MarkdownTranscriptProvider


@pytest.fixture
def mock_ticket() -> Ticket:
    return Ticket(id=1, guild_id=123, owner_id=456, created_at=datetime.now(timezone.utc), status="closed")


@pytest.fixture
def mock_messages() -> list[TicketMessage]:
    return [
        TicketMessage(message_id=1, author_id=456, author_name="User", content="Help me", timestamp=datetime.now(timezone.utc), attachments=[]),
        TicketMessage(message_id=2, author_id=999, author_name="Staff", content="Hello", timestamp=datetime.now(timezone.utc), attachments=[])
    ]


@pytest.mark.asyncio
async def test_json_provider(mock_ticket: Ticket, mock_messages: list[TicketMessage]) -> None:
    provider = JSONTranscriptProvider()
    assert provider.extension == ".json"
    
    data = await provider.generate(mock_ticket, mock_messages)
    assert b"Help me" in data
    assert b'"status": "closed"' in data


@pytest.mark.asyncio
async def test_markdown_provider(mock_ticket: Ticket, mock_messages: list[TicketMessage]) -> None:
    provider = MarkdownTranscriptProvider()
    assert provider.extension == ".md"
    
    data = await provider.generate(mock_ticket, mock_messages)
    assert b"# Ticket Transcript: 1" in data
    assert b"Help me" in data
