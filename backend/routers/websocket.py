"""
routers/websocket.py — WebSocket endpoint for real-time dashboard updates.
"""

import json
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from loguru import logger

from core.websocket_manager import ws_manager
from core.security import decode_access_token

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/{room}")
async def websocket_endpoint(
    websocket: WebSocket,
    room: str,
    token: str = Query(default=None),
):
    """
    WebSocket endpoint for real-time dashboard updates.
    Rooms: agent | admin | user
    Query param token: JWT for authentication.
    """
    user_id = "anonymous"
    role = "user"

    # Validate JWT token
    if token:
        try:
            payload = decode_access_token(token)
            user_id = payload.get("sub", "anonymous")
            role = payload.get("role", "user")
        except Exception:
            pass

    # Authorization: only agents/admins/senior_engineers can join agent/admin rooms
    if room == "admin" and role not in ("admin",):
        await websocket.accept()
        await websocket.close(code=4003, reason="Unauthorized")
        return
    if room == "agent" and role not in ("agent", "admin", "senior_engineer"):
        await websocket.accept()
        await websocket.close(code=4003, reason="Unauthorized")
        return

    # Generate a unique connection ID for this session
    connection_id = str(uuid.uuid4())

    # Connect — passes connection_id and role correctly
    await ws_manager.connect(
        websocket,
        connection_id=connection_id,
        user_id=user_id,
        role=role,
    )

    # Also join the specific room the client requested (agent / admin / user)
    await ws_manager.join_room(connection_id, room)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except Exception:
                pass
    except WebSocketDisconnect:
        await ws_manager.disconnect(connection_id)
        logger.debug(f"WebSocket disconnected: {user_id} from room {room}")
    except Exception as e:
        logger.warning(f"WebSocket error for {user_id}: {e}")
        await ws_manager.disconnect(connection_id)
