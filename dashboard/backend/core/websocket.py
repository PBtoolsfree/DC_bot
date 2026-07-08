"""WebSocket manager and Redis PubSub integration."""

from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    """Manages active WebSocket connections."""
    
    def __init__(self) -> None:
        # Map of guild_id to list of active websockets
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, guild_id: int) -> None:
        """Accept a connection and add it to the tracking dictionary."""
        await websocket.accept()
        if guild_id not in self.active_connections:
            self.active_connections[guild_id] = []
        self.active_connections[guild_id].append(websocket)

    def disconnect(self, websocket: WebSocket, guild_id: int) -> None:
        """Remove a connection."""
        if guild_id in self.active_connections:
            if websocket in self.active_connections[guild_id]:
                self.active_connections[guild_id].remove(websocket)
            if not self.active_connections[guild_id]:
                del self.active_connections[guild_id]

    async def broadcast_to_guild(self, guild_id: int, message: dict[str, Any]) -> None:
        """Send a JSON message to all clients watching a specific guild."""
        if guild_id in self.active_connections:
            for connection in self.active_connections[guild_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass # Handle stale connections


ws_manager = ConnectionManager()
