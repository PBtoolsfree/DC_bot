"""WebSocket endpoint."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from bot.utils.logger import get_logger
from dashboard.backend.core.security import ALGORITHM, SECRET_KEY
from dashboard.backend.core.websocket import ws_manager

logger = get_logger(__name__)
router = APIRouter()


async def get_ws_user(token: str) -> str | None:
    """Validate JWT token passed via WS query params."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


@router.websocket("/{guild_id}")
async def websocket_endpoint(websocket: WebSocket, guild_id: int, token: str) -> None:
    """Connect to the live event stream for a guild."""
    user_id = await get_ws_user(token)
    if not user_id:
        await websocket.close(code=1008)
        return

    # In a full implementation, we must check RBAC here to ensure `user_id` has access to `guild_id`

    await ws_manager.connect(websocket, guild_id)
    try:
        while True:
            # Keep alive ping/pong
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, guild_id)
