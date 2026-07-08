"""Discord OAuth2 Authentication endpoints."""

import os
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from dashboard.backend.core.security import create_access_token, get_current_user

router = APIRouter()

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "123456789")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "dummy_secret")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:3000/auth/callback")

DISCORD_API_URL = "https://discord.com/api/v10"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


@router.get("/login")
async def login() -> RedirectResponse:
    """Redirect user to Discord OAuth2 authorization page."""
    auth_url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={DISCORD_CLIENT_ID}"
        f"&redirect_uri={DISCORD_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify%20guilds"
    )
    return RedirectResponse(url=auth_url)


@router.get("/callback", response_model=TokenResponse)
async def callback(code: str) -> dict[str, Any]:
    """Exchange OAuth2 code for an access token and generate a JWT."""
    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": DISCORD_REDIRECT_URI,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with httpx.AsyncClient() as client:
        # 1. Exchange Code for Token
        token_res = await client.post(
            "https://discord.com/api/oauth2/token", data=data, headers=headers
        )
        if token_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid OAuth code.")

        token_data = token_res.json()
        discord_access_token = token_data.get("access_token")

        # 2. Get User Info
        user_res = await client.get(
            f"{DISCORD_API_URL}/users/@me",
            headers={"Authorization": f"Bearer {discord_access_token}"},
        )
        if user_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch user data.")

        user_data = user_res.json()

        # 3. Create Dashboard JWT
        jwt_payload = {
            "sub": str(user_data["id"]),
            "username": user_data["username"],
            "avatar": user_data.get("avatar"),
            "discord_access_token": discord_access_token,
        }

        jwt_token = create_access_token(data=jwt_payload)

        return {"access_token": jwt_token, "token_type": "bearer"}


@router.get("/me")
async def get_me(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    """Return the currently authenticated user's data."""
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "avatar": current_user["avatar"],
    }
