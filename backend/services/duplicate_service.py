"""
services/duplicate_service.py — Duplicate ticket detection using ChromaDB.
Finds exact and possible duplicate tickets using embedding similarity.
"""

from typing import Optional, Dict
from loguru import logger

from core.config import settings
from core.database import get_tickets_collection
from services.retrieval_service import retrieval_service


class DuplicateService:
    """
    Detects duplicate or related tickets using vector similarity.

    Thresholds:
    - >= 0.95: EXACT duplicate → link to parent, suppress new ticket
    - 0.85-0.95: POSSIBLE duplicate → flag for agent review
    - < 0.85: Independent ticket
    """

    async def check_duplicate(
        self,
        text: str,
        new_ticket_id: str,
        category: Optional[str] = None,
    ) -> dict:
        """
        Check if the incoming ticket is a duplicate of an open ticket.

        Args:
            text: Cleaned ticket text.
            new_ticket_id: ID of the new ticket being processed.
            category: Optional category filter for similarity search.

        Returns:
            Dict with duplicate status, parent ticket ID, and suggested response.
        """
        # Query ChromaDB for similar OPEN tickets (within last 24 hours)
        similar_open = await retrieval_service.find_open_tickets_similar(
            text=text,
            within_hours=24,
        )

        # Filter out the new ticket itself
        similar_open = [t for t in similar_open if t.get("ticket_id") != new_ticket_id]

        if not similar_open:
            return {
                "is_duplicate": False,
                "is_possible_duplicate": False,
                "parent_ticket_id": None,
                "similarity_score": 0.0,
                "message": None,
            }

        top = similar_open[0]
        similarity = top["similarity_score"]

        # ── Exact duplicate ──────────────────────────────────────────
        if similarity >= settings.DUPLICATE_EXACT_THRESHOLD:
            parent_id = top["ticket_id"]
            logger.info(
                f"Exact duplicate detected: {new_ticket_id} → {parent_id} "
                f"(similarity={similarity:.3f})"
            )

            # Increment parent's duplicate_count in MongoDB
            await self._increment_duplicate_count(parent_id)

            # Check if parent should be escalated (10+ dupes)
            parent_doc = await self._get_ticket(parent_id)
            duplicate_count = 0
            if parent_doc:
                metadata = parent_doc.get("metadata", {})
                duplicate_count = metadata.get("duplicate_count", 0)

            escalate_parent = duplicate_count >= 10

            return {
                "is_duplicate": True,
                "is_possible_duplicate": False,
                "parent_ticket_id": parent_id,
                "similarity_score": round(similarity, 4),
                "escalate_parent": escalate_parent,
                "duplicate_count": duplicate_count,
                "message": (
                    f"A similar issue is already being investigated "
                    f"under Ticket #{parent_id}. "
                    f"We'll update you when it's resolved."
                ),
            }

        # ── Possible duplicate ───────────────────────────────────────
        elif similarity >= settings.DUPLICATE_POSSIBLE_THRESHOLD:
            parent_id = top["ticket_id"]
            logger.debug(
                f"Possible duplicate: {new_ticket_id} ≈ {parent_id} "
                f"(similarity={similarity:.3f})"
            )
            return {
                "is_duplicate": False,
                "is_possible_duplicate": True,
                "parent_ticket_id": parent_id,
                "similarity_score": round(similarity, 4),
                "escalate_parent": False,
                "duplicate_count": 0,
                "message": (
                    f"Possibly related to Ticket #{parent_id} "
                    f"({similarity:.0%} similar). Please review."
                ),
            }

        # ── Independent ticket ────────────────────────────────────────
        return {
            "is_duplicate": False,
            "is_possible_duplicate": False,
            "parent_ticket_id": None,
            "similarity_score": round(similarity, 4),
            "message": None,
        }

    async def _increment_duplicate_count(self, ticket_id: str) -> None:
        """Atomically increment duplicate_count on the parent ticket."""
        try:
            collection = get_tickets_collection()
            await collection.update_one(
                {"ticket_id": ticket_id},
                {"$inc": {"metadata.duplicate_count": 1}},
            )
        except Exception as e:
            logger.error(f"Failed to increment duplicate count for {ticket_id}: {e}")

    async def _get_ticket(self, ticket_id: str) -> Optional[dict]:
        """Fetch a ticket document by ID."""
        try:
            collection = get_tickets_collection()
            return await collection.find_one({"ticket_id": ticket_id})
        except Exception:
            return None


# Module-level singleton
duplicate_service = DuplicateService()
