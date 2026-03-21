"""
services/notification_service.py — WebSocket and push notifications.
"""

from loguru import logger
from core.websocket_manager import ws_manager


class NotificationService:
    """
    Broadcasts system events via WebSocket to all connected dashboard clients.
    All methods are fire-and-forget async.
    """

    async def notify_new_ticket(self, ticket_data: dict) -> None:
        """Notify agents of a newly submitted ticket."""
        try:
            await ws_manager.broadcast_new_ticket(ticket_data)
        except Exception as e:
            logger.warning(f"notify_new_ticket error: {e}")

    async def notify_ticket_resolved(self, ticket_id: str, resolution: dict) -> None:
        """Notify all clients that a ticket was resolved."""
        try:
            await ws_manager.broadcast_ticket_update({
                "type": "resolved",
                "ticket_id": ticket_id,
                "resolution": resolution,
            })
        except Exception as e:
            logger.warning(f"notify_ticket_resolved error: {e}")

    async def notify_sla_warning(
        self,
        ticket_id: str,
        minutes_left: float,
        category: str,
        priority: str,
    ) -> None:
        """Warn agents when a ticket is approaching SLA breach."""
        try:
            await ws_manager.broadcast_sla_warning(
                ticket_id, int(minutes_left)
            )
        except Exception as e:
            logger.warning(f"notify_sla_warning error: {e}")

    async def notify_root_cause_alert(self, alert: dict) -> None:
        """Broadcast incident spike alert to all dashboard clients."""
        try:
            await ws_manager.broadcast_root_cause_alert(alert)
        except Exception as e:
            logger.warning(f"notify_root_cause_alert error: {e}")

    async def notify_retraining_complete(
        self,
        new_f1: float,
        old_f1: float,
        promoted: bool,
    ) -> None:
        """Notify admins when model retraining finishes."""
        try:
            await ws_manager.broadcast_to_room("admin", {
                "type": "retraining_complete",
                "new_f1": round(new_f1, 4),
                "old_f1": round(old_f1, 4),
                "promoted": promoted,
                "message": (
                    f"Model retrained: F1 {old_f1:.3f} → {new_f1:.3f} "
                    f"({'promoted' if promoted else 'kept old model'})"
                ),
            })
        except Exception as e:
            logger.warning(f"notify_retraining_complete error: {e}")

    async def notify_duplicate_detected(
        self,
        new_ticket_id: str,
        parent_ticket_id: str,
        similarity: float,
    ) -> None:
        """Notify agents that a duplicate was linked."""
        try:
            await ws_manager.broadcast_to_room("agent", {
                "type": "duplicate_detected",
                "new_ticket_id": new_ticket_id,
                "parent_ticket_id": parent_ticket_id,
                "similarity": round(similarity, 2),
            })
        except Exception as e:
            logger.warning(f"notify_duplicate_detected error: {e}")


# Module-level singleton
notification_service = NotificationService()
