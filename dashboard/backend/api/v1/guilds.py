"""API endpoints for Discord Guilds."""

import os
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from dashboard.backend.core.database import get_db
from dashboard.backend.core.security import get_current_user

router = APIRouter()

DISCORD_API_URL = "https://discord.com/api/v10"


@router.get("/")
async def list_guilds(current_user: dict[str, Any] = Depends(get_current_user)) -> list[dict[str, Any]]:
    """Fetch the user's guilds and filter by permissions."""
    access_token = current_user.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Discord access token missing.")
        
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{DISCORD_API_URL}/users/@me/guilds",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if res.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch guilds from Discord.")
            
        guilds = res.json()
        
    # Filter guilds where the user has Manage Server (0x20) or Administrator (0x8)
    # Permissions are returned as string bitmask
    valid_guilds = []
    for g in guilds:
        perms = int(g.get("permissions", "0"))
        is_owner = g.get("owner", False)
        
        has_admin = (perms & 0x8) == 0x8
        has_manage_server = (perms & 0x20) == 0x20
        
        if is_owner or has_admin or has_manage_server:
            valid_guilds.append({
                "id": g["id"],
                "name": g["name"],
                "icon": g["icon"],
                "owner": is_owner,
                "permissions": perms
            })
            
    return valid_guilds
