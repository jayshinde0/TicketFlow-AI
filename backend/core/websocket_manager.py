"""
core/websocket_manager.py — Real-time WebSocket connection manager.
Handles broadcasting to all connected dashboard clients.
"""

import asyncio
import json
from typing import Dict, List, Optional, Set
from fastapi import WebSocket
from loguru import logger
from datetime import datetime, timezone


class ConnectionManager:
    """
    Manages active WebSocket connections.

    Supports:
    - Broadcasting to all connected clients
    - Sending to specific user by user_id
    - Room-based broadcasting (e.g., admin room, agent room)
    - Graceful disconnection handling
    """

    def __init__(self):
        # Map of connection_id → WebSocket for all active connections
        self._active_connections: Dict[str, WebSocket] = {}

        # Map of user_id → set of connection_ids (user can have multiple tabs)
        self._user_connections: Dict[str, Set[str]] = {}

        # Map of room_name → set of connection_ids
        self._rooms: Dict[str, Set[str]] = {}

        # Map of connection_id → metadata (user_id, role, joined_at)
        self._connection_meta: Dict[str, dict] = {}

    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        user_id: Optional[str] = None,
        role: Optional[str] = None,
    ) -> None:
        """
        Accept a new WebSocket connection and register it.

        Args:
            websocket: The WebSocket object from FastAPI.
            connection_id: Unique ID for this connection (UUID).
            user_id: Optional authenticated user ID.
            role: Optional user role for room assignment.
        """
        await websocket.accept()

        self._active_connections[connection_id] = websocket
        self._connection_meta[connection_id] = {
            "user_id": user_id,
            "role": role,
            "joined_at": datetime.now(timezone.utc).isoformat(),
        }

        # Register in user→connections map
        if user_id:
            if user_id not in self._user_connections:
                self._user_connections[user_id] = set()
            self._user_connections[user_id].add(connection_id)

        # Auto-join role-based rooms
        if role:
            await self.join_room(connection_id, role)  # e.g., "agent" room
        await self.join_room(connection_id, "all")  # everyone

        logger.info(
            f"WebSocket connected: {connection_id} "
            f"(user={user_id}, role={role}). "
            f"Total connections: {len(self._active_connections)}"
        )

        # Send welcome message with server time
        await self.send_personal(
            connection_id,
            {
                "type": "connected",
                "connection_id": connection_id,
                "server_time": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def disconnect(self, connection_id: str) -> None:
        """
        Remove a connection and clean up all references.
        Safe to call even if connection_id is not registered.
        """
        websocket = self._active_connections.pop(connection_id, None)
        meta = self._connection_meta.pop(connection_id, {})

        # Remove from user map
        user_id = meta.get("user_id")
        if user_id and user_id in self._user_connections:
            self._user_connections[user_id].discard(connection_id)
            if not self._user_connections[user_id]:
                del self._user_connections[user_id]

        # Remove from all rooms
        for room_members in self._rooms.values():
            room_members.discard(connection_id)

        logger.info(
            f"WebSocket disconnected: {connection_id}. "
            f"Total connections: {len(self._active_connections)}"
        )

    async def join_room(self, connection_id: str, room: str) -> None:
        """Add a connection to a named room."""
        if room not in self._rooms:
            self._rooms[room] = set()
        self._rooms[room].add(connection_id)

    async def leave_room(self, connection_id: str, room: str) -> None:
        """Remove a connection from a named room."""
        if room in self._rooms:
            self._rooms[room].discard(connection_id)

    async def send_personal(self, connection_id: str, message: dict) -> bool:
        """
        Send a JSON message to a single connection.

        Returns:
            True if sent successfully, False if connection not found or broken.
        """
        websocket = self._active_connections.get(connection_id)
        if not websocket:
            return False
        try:
            await websocket.send_text(json.dumps(message, default=str))
            return True
        except Exception as e:
            logger.warning(f"Failed to send to {connection_id}: {e}. Disconnecting.")
            await self.disconnect(connection_id)
            return False

    async def send_to_user(self, user_id: str, message: dict) -> int:
        """
        Send a message to all connections belonging to a user (multi-tab).

        Returns:
            Number of connections successfully sent to.
        """
        connection_ids = list(self._user_connections.get(user_id, set()))
        sent = 0
        for cid in connection_ids:
            if await self.send_personal(cid, message):
                sent += 1
        return sent

    async def broadcast_to_room(self, room: str, message: dict) -> int:
        """
        Broadcast a JSON message to all connections in a room.

        Returns:
            Number of connections successfully sent to.
        """
        connection_ids = list(self._rooms.get(room, set()))
        sent = 0

        # Use asyncio.gather for concurrent sending
        tasks = [self.send_personal(cid, message) for cid in connection_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        sent = sum(1 for r in results if r is True)
        return sent

    async def broadcast_all(self, message: dict) -> int:
        """Broadcast to every connected client."""
        return await self.broadcast_to_room("all", message)

    async def broadcast_ticket_update(self, ticket_data: dict) -> None:
        """Convenience method — broadcast a ticket update event."""
        await self.broadcast_all(
            {
                "type": "ticket_update",
                "data": ticket_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    async def broadcast_root_cause_alert(self, alert_data: dict) -> None:
        """Convenience method — broadcast a root cause alert."""
        await self.broadcast_all(
            {
                "type": "root_cause_alert",
                "data": alert_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    async def broadcast_sla_warning(self, ticket_id: str, minutes_left: int) -> None:
        """Convenience method — broadcast an SLA breach warning."""
        await self.broadcast_to_room(
            "agent",
            {
                "type": "sla_warning",
                "ticket_id": ticket_id,
                "minutes_left": minutes_left,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def broadcast_new_ticket(self, ticket_data: dict) -> None:
        """Convenience method — notify agents of a new ticket."""
        await self.broadcast_to_room(
            "agent",
            {
                "type": "new_ticket",
                "data": ticket_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def broadcast_security_alert(self, alert_data: dict) -> None:
        """
        Broadcast a real-time security threat alert to all admin/agent clients.
        Used by the security pipeline when an attack or suspicious ticket is detected.
        """
        message = {
            "type": "security_alert",
            "data": alert_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        # Broadcast to both admin and agent rooms
        await self.broadcast_to_room("admin", message)
        await self.broadcast_to_room("agent", message)
        logger.warning(
            f"Security alert broadcast: ticket={alert_data.get('ticket_id')}, "
            f"level={alert_data.get('threat_level')}, type={alert_data.get('threat_type')}"
        )

    @property
    def connection_count(self) -> int:
        """Total number of active WebSocket connections."""
        return len(self._active_connections)

    @property
    def connected_users(self) -> List[str]:
        """List of all currently connected user IDs."""
        return list(self._user_connections.keys())

    def get_room_size(self, room: str) -> int:
        """Number of connections in a room."""
        return len(self._rooms.get(room, set()))


# Module-level singleton — import this in routers and services
ws_manager = ConnectionManager()
