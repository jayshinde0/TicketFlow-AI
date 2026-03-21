"""
services/knowledge_builder_service.py — Auto-builds KB articles from resolved tickets.
Triggered after successful ticket resolution.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from loguru import logger

from core.database import get_knowledge_articles_collection
from services.llm_service import llm_service
from services.retrieval_service import retrieval_service


class KnowledgeBuilderService:
    """
    Agent 5 knowledge building component.

    After a ticket is resolved:
    1. Calls Mistral to generate a structured KB article from the ticket+solution
    2. Stores article in MongoDB knowledge_articles collection
    3. Adds article embedding to ChromaDB for semantic search
    """

    async def build_article_from_ticket(
        self,
        ticket_id: str,
        ticket_text: str,
        category: str,
        solution: str,
        resolution_time_hours: float,
    ) -> Optional[dict]:
        """
        Generate and store a KB article from a resolved ticket.

        Args:
            ticket_id: Source ticket ID.
            ticket_text: Original ticket text.
            category: Ticket category.
            solution: Final resolution text.
            resolution_time_hours: Time to resolve.

        Returns:
            Created article dict, or None on failure.
        """
        # Step 1: Ask Mistral to generate structured article
        article_data = await llm_service.generate_knowledge_article(
            ticket_text=ticket_text,
            category=category,
            solution=solution,
            resolution_hours=resolution_time_hours,
        )

        if not article_data:
            logger.warning(
                f"KB article generation failed for ticket {ticket_id}. "
                f"LLM unavailable or returned invalid JSON."
            )
            # Build a minimal article from available data
            article_data = {
                "title": ticket_text[:80],
                "problem_description": ticket_text[:200],
                "likely_cause": "Requires investigation",
                "solution_steps": [solution],
                "prevention": "Monitor regularly",
                "tags": [category.lower()],
                "difficulty": "Medium",
                "estimated_resolution_time": f"{int(resolution_time_hours * 60)} minutes",
            }

        # Step 2: Build full article document
        article_id = f"KB-{str(uuid.uuid4())[:8].upper()}"
        now = datetime.now(timezone.utc)

        article_doc = {
            "article_id": article_id,
            "title": article_data.get("title", ticket_text[:80]),
            "category": category,
            "problem_description": article_data.get("problem_description", ""),
            "likely_cause": article_data.get("likely_cause", ""),
            "solution_steps": article_data.get("solution_steps", [solution]),
            "prevention": article_data.get("prevention", ""),
            "tags": article_data.get("tags", [category.lower()]),
            "difficulty": article_data.get("difficulty", "Medium"),
            "estimated_resolution_time": article_data.get(
                "estimated_resolution_time", f"{int(resolution_time_hours * 60)} min"
            ),
            "source_ticket_id": ticket_id,
            "usage_count": 0,
            "created_at": now,
            "last_used_at": None,
            "embedding_id": article_id,
        }

        # Step 3: Store in MongoDB
        try:
            collection = get_knowledge_articles_collection()
            await collection.insert_one(article_doc.copy())
            logger.info(f"KB article {article_id} created from ticket {ticket_id}")
        except Exception as e:
            logger.error(f"Failed to store KB article: {e}")
            return None

        # Step 4: Add embedding to ChromaDB
        article_content = (
            f"{article_doc['title']} {article_doc['problem_description']} "
            f"{' '.join(article_doc['solution_steps'])}"
        )
        await retrieval_service.add_knowledge_article(
            article_id=article_id,
            content=article_content,
            metadata={
                "article_id": article_id,
                "category": category,
                "difficulty": article_doc["difficulty"],
                "tags": ",".join(article_doc["tags"]),
            },
        )

        return article_doc

    async def increment_usage(self, article_id: str) -> None:
        """Increment usage_count when an article helps resolve a ticket."""
        try:
            collection = get_knowledge_articles_collection()
            await collection.update_one(
                {"article_id": article_id},
                {
                    "$inc": {"usage_count": 1},
                    "$set": {"last_used_at": datetime.now(timezone.utc)},
                },
            )
        except Exception as e:
            logger.warning(f"Failed to increment KB article usage: {e}")


# Module-level singleton
knowledge_builder_service = KnowledgeBuilderService()
