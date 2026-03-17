"""
WebSocket endpoint for real-time agent updates.
"""

import json
from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_access_token
from app.db import async_session_factory

router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections per user."""

    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_to_user(self, user_id: str, message: dict):
        """Send a message to all connections for a user."""
        if user_id in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead_connections.append(connection)

            # Clean up dead connections
            for conn in dead_connections:
                self.active_connections[user_id].remove(conn)

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected users."""
        for user_id in list(self.active_connections.keys()):
            await self.send_to_user(user_id, message)


manager = ConnectionManager()


@router.websocket("/agent")
async def agent_websocket(
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    WebSocket endpoint for real-time agent status updates.

    Connect with: ws://host/api/v1/ws/agent?token=<access_token>

    Messages sent from server:
    - {"type": "status", "data": {...}}  - Agent status update
    - {"type": "log", "data": {...}}     - New log entry
    - {"type": "application", "data": {...}} - Application completed
    - {"type": "error", "data": {...}}   - Error occurred
    """
    # Authenticate via token query parameter
    payload = verify_access_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token payload")
        return

    await manager.connect(user_id, websocket)

    try:
        # Send initial status
        await websocket.send_json({
            "type": "connected",
            "data": {"message": "Connected to agent updates"},
        })

        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle ping/pong for keepalive
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif message.get("type") == "subscribe":
                    # Client can subscribe to specific event types
                    await websocket.send_json({
                        "type": "subscribed",
                        "data": {"events": message.get("events", [])},
                    })

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "Invalid JSON"},
                })

    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
    except Exception:
        manager.disconnect(user_id, websocket)


async def notify_agent_update(user_id: str, event_type: str, data: dict):
    """
    Send an agent update to a user's WebSocket connections.
    Call this from services/workers when agent state changes.
    """
    await manager.send_to_user(user_id, {
        "type": event_type,
        "data": data,
    })
