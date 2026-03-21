"""
services/retrieval_service.py — Agent 2: ChromaDB vector retrieval.

Queries the vector database for similar resolved tickets.
Returns top-3 most similar past cases with solutions and similarity scores.
"""

import asyncio
from typing import List, Dict, Optional
from loguru import logger

from core.config import settings
from services.embedding_service import embedding_service


class RetrievalService:
    """
    Agent 2 of the TicketFlow pipeline.

    Responsibilities:
    - Connect to ChromaDB (local or remote)
    - Store resolved tickets and knowledge articles as embeddings
    - Query similar past resolved tickets for a new ticket
    - Return top-K matches with cosine similarity scores

    Collections:
    - resolved_tickets: past tickets with solutions (for RAG)
    - knowledge_articles: auto-generated KB articles
    """

    def __init__(self):
        self._client = None
        self._tickets_collection = None
        self._articles_collection = None
        self._initialized = False

    def _init_client(self):
        """Initialize ChromaDB client (lazy, called on first use)."""
        if self._initialized:
            return

        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            # Try HttpClient first (for Docker/remote ChromaDB)
            try:
                self._client = chromadb.HttpClient(
                    host=settings.CHROMA_HOST,
                    port=settings.CHROMA_PORT,
                )
                # Test connection
                self._client.heartbeat()
                logger.info(
                    f"ChromaDB connected at "
                    f"{settings.CHROMA_HOST}:{settings.CHROMA_PORT}"
                )
            except Exception:
                # Fall back to local persistent client
                logger.warning(
                    "ChromaDB remote unavailable. Using local persistent client."
                )
                self._client = chromadb.PersistentClient(path="./chroma_data")

            # Get or create collections
            self._tickets_collection = self._client.get_or_create_collection(
                name=settings.CHROMA_TICKETS_COLLECTION,
                metadata={"hnsw:space": "cosine"},
            )
            self._articles_collection = self._client.get_or_create_collection(
                name=settings.CHROMA_ARTICLES_COLLECTION,
                metadata={"hnsw:space": "cosine"},
            )
            self._initialized = True
            logger.info(
                f"ChromaDB collections ready: "
                f"tickets={self._tickets_collection.count()}, "
                f"articles={self._articles_collection.count()}"
            )

        except Exception as e:
            logger.error(f"ChromaDB initialization failed: {e}")
            self._initialized = True  # mark as attempted, use fallback

    async def add_resolved_ticket(
        self,
        ticket_id: str,
        text: str,
        solution: str,
        category: str,
        priority: str,
        resolution_time_hours: float,
        status: str = "resolved",
    ) -> bool:
        """
        Add a newly resolved ticket to ChromaDB for future retrieval.

        Args:
            ticket_id: e.g. "TKT-A3F8"
            text: Original cleaned ticket text.
            solution: Final resolution text sent to user.
            category: e.g. "Network"
            resolution_time_hours: How long it took to resolve.
            status: Typically "resolved".

        Returns:
            True if added successfully.
        """
        self._init_client()
        if self._tickets_collection is None:
            return False

        try:
            embedding = await embedding_service.embed_async(text)
            self._tickets_collection.upsert(
                ids=[ticket_id],
                embeddings=[embedding.tolist()],
                documents=[text],
                metadatas=[{
                    "ticket_id": ticket_id,
                    "solution": solution[:2000],   # cap at 2000 chars
                    "category": category,
                    "priority": priority,
                    "resolution_time_hours": str(resolution_time_hours),
                    "status": status,
                }]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add ticket {ticket_id} to ChromaDB: {e}")
            return False

    def _query_similar(
        self,
        embedding: list,
        category: Optional[str],
        top_k: int = 3,
        status_filter: str = "resolved",
    ) -> List[Dict]:
        """
        Query ChromaDB for similar tickets.

        Args:
            embedding: 384-dim embedding list.
            category: If provided, filter by same category.
            top_k: Number of results to return.
            status_filter: Only return tickets with this status.

        Returns:
            List of similar ticket dicts.
        """
        self._init_client()
        if self._tickets_collection is None:
            return []

        try:
            # Build where filter
            where = {"status": {"$eq": status_filter}}
            if category:
                where = {
                    "$and": [
                        {"status": {"$eq": status_filter}},
                        {"category": {"$eq": category}},
                    ]
                }

            # Query ChromaDB — request more results since we filter below
            results = self._tickets_collection.query(
                query_embeddings=[embedding],
                n_results=min(top_k * 2, max(top_k, 5)),
                where=where if self._tickets_collection.count() > 0 else None,
                include=["distances", "documents", "metadatas"],
            )

            similar = []
            if not results["ids"] or not results["ids"][0]:
                return []

            for i, (ticket_id, distance, document, metadata) in enumerate(zip(
                results["ids"][0],
                results["distances"][0],
                results["documents"][0],
                results["metadatas"][0],
            )):
                # ChromaDB cosine distance: 0=identical, 2=opposite
                # Convert to similarity: 1 - distance/2
                similarity = max(0.0, 1.0 - (distance / 2.0))

                if similarity < 0.3:
                    continue   # skip low-quality matches

                similar.append({
                    "ticket_id": ticket_id,
                    "summary": document[:300],
                    "solution": metadata.get("solution", "No solution recorded"),
                    "similarity_score": round(similarity, 4),
                    "category": metadata.get("category", "Unknown"),
                    "resolution_time_hours": float(
                        metadata.get("resolution_time_hours", 2.0)
                    ),
                })

            # Sort by similarity and take top_k
            similar.sort(key=lambda x: x["similarity_score"], reverse=True)
            return similar[:top_k]

        except Exception as e:
            logger.error(f"ChromaDB query error: {e}")
            return []

    async def find_similar_tickets(
        self,
        text: str,
        category: Optional[str] = None,
        top_k: int = 3,
    ) -> dict:
        """
        Agent 2 main method: find top-K similar resolved tickets.

        Args:
            text: Cleaned ticket text.
            category: Predicted category for filtering.
            top_k: Max results to return.

        Returns:
            Agent 2 output dict matching pipeline spec.
        """
        # Generate embedding
        embedding = await embedding_service.embed_async(text)
        embedding_list = embedding_service.embedding_to_list(embedding)

        # Run ChromaDB query in thread pool
        loop = asyncio.get_event_loop()
        similar = await loop.run_in_executor(
            None,
            lambda: self._query_similar(embedding_list, category, top_k)
        )

        # If category-filtered query returned no results, try without filter
        if not similar and category:
            similar = await loop.run_in_executor(
                None,
                lambda: self._query_similar(embedding_list, None, top_k)
            )

        top_score = similar[0]["similarity_score"] if similar else 0.0

        collection_size = 0
        try:
            if self._tickets_collection:
                collection_size = self._tickets_collection.count()
        except Exception:
            pass

        return {
            "similar_tickets": similar,
            "top_similarity_score": round(top_score, 4),
            "knowledge_base_size": collection_size,
            "embedding": embedding,   # pass to duplicate detector + LLM
        }

    async def find_open_tickets_similar(
        self,
        text: str,
        within_hours: int = 24,
    ) -> List[Dict]:
        """
        Query for similar OPEN tickets (used for duplicate detection).
        Returns all open tickets with similarity > 0.5.
        """
        embedding = await embedding_service.embed_async(text)
        embedding_list = embedding_service.embedding_to_list(embedding)

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._query_similar(
                embedding_list,
                category=None,
                top_k=10,
                status_filter="open",
            )
        )

    async def add_knowledge_article(
        self,
        article_id: str,
        content: str,
        metadata: dict,
    ) -> bool:
        """Add a KB article to the articles ChromaDB collection."""
        self._init_client()
        if self._articles_collection is None:
            return False
        try:
            embedding = await embedding_service.embed_async(content)
            self._articles_collection.upsert(
                ids=[article_id],
                embeddings=[embedding.tolist()],
                documents=[content],
                metadatas=metadata,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add article {article_id}: {e}")
            return False

    def get_collection_stats(self) -> dict:
        """Return sizes of both ChromaDB collections."""
        self._init_client()
        try:
            return {
                "resolved_tickets": (
                    self._tickets_collection.count()
                    if self._tickets_collection else 0
                ),
                "knowledge_articles": (
                    self._articles_collection.count()
                    if self._articles_collection else 0
                ),
            }
        except Exception:
            return {"resolved_tickets": 0, "knowledge_articles": 0}


# Module-level singleton
retrieval_service = RetrievalService()
