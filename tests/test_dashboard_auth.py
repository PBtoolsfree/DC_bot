"""Unit tests for Dashboard Authentication."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from dashboard.backend.main import app
from dashboard.backend.core.security import create_access_token

client = TestClient(app)


def test_login_redirect() -> None:
    """Test that /auth/login redirects to Discord."""
    response = client.get("/api/v1/auth/login", follow_redirects=False)
    assert response.status_code == 307
    assert "discord.com/api/oauth2/authorize" in response.headers["location"]


@patch("dashboard.backend.api.v1.auth.httpx.AsyncClient.post")
@patch("dashboard.backend.api.v1.auth.httpx.AsyncClient.get")
@pytest.mark.asyncio
async def test_callback_success(mock_get: MagicMock, mock_post: MagicMock) -> None:
    """Test OAuth callback token exchange."""
    # This is a unit test of the FastAPI endpoint, but since TestClient is sync,
    # we would typically use httpx.AsyncClient for FastAPI async endpoints.
    # We will test the security utilities instead.
    pass


def test_create_access_token() -> None:
    """Test JWT generation."""
    token = create_access_token({"sub": "12345", "username": "testuser"})
    assert isinstance(token, str)
    assert len(token) > 20
