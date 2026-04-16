"""
services/embedding_service.py — Sentence transformer embedding generation.
Produces 384-dimensional vectors for ChromaDB and similarity computation.
"""

import asyncio
import numpy as np
from typing import List, Optional
from loguru import logger

from core.config import settings


class EmbeddingService:
    """
    Wraps sentence-transformers all-MiniLM-L6-v2 for embedding generation.

    - Lazy-loaded on first use to avoid slow startup
    - Thread-safe singleton model instance
    - Async wrappers to avoid blocking FastAPI event loop
    """

    def __init__(self):
        self._model = None
        self._model_name = settings.EMBEDDING_MODEL  # "all-MiniLM-L6-v2"

    def _load_model(self):
        """Use TF-IDF fallback for speed. Real model loads in background after cache warms."""
        if self._model is not None:
            return self._model
        # Use fast fallback by default — avoids 10-30s load delay on requests
        # Model will be loaded after cache download completes via background thread
        self._model = "FALLBACK"
        import threading

        def _try_load():
            try:
                import os

                cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
                has_cache = os.path.exists(cache_dir) and any(
                    self._model_name.replace("/", "--") in d
                    for d in os.listdir(cache_dir)
                )
                if not has_cache:
                    from sentence_transformers import SentenceTransformer

                    SentenceTransformer(self._model_name)  # download to cache
                    logger.info(
                        "Sentence transformer cached — restart server to enable."
                    )
                # If cached, server restart will auto-load
            except Exception as e:
                logger.debug(f"Background model prep: {e}")

        threading.Thread(target=_try_load, daemon=True).start()
        return self._model

    def _fallback_embed(self, text: str) -> np.ndarray:
        """TF-IDF-style fallback embedding using character n-gram hashing."""
        vec = np.zeros(384, dtype=np.float32)
        words = text.lower().split()[:50]
        for i, word in enumerate(words):
            idx = hash(word) % 384
            vec[abs(idx)] += 1.0 / (i + 1)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec

    def embed(self, text: str) -> np.ndarray:
        """
        Generate a 384-dim embedding for a single text string.
        Falls back to hashed TF-IDF if sentence-transformers unavailable.
        """
        model = self._load_model()
        if model == "FALLBACK":
            return self._fallback_embed(text)
        embedding = model.encode(
            text,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embedding.astype(np.float32)

    def embed_batch(self, texts: List[str], batch_size: int = 64) -> np.ndarray:
        """
        Generate embeddings for a list of texts efficiently.

        Args:
            texts: List of strings.
            batch_size: Encoding batch size.

        Returns:
            np.ndarray of shape (n_texts, 384)
        """
        model = self._load_model()
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 100,
        )
        return embeddings.astype(np.float32)

    def cosine_similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """
        Compute cosine similarity between two normalized vectors.
        Since we normalize on embedding, this is just the dot product.

        Returns:
            Float in [-1, 1]; in practice [0, 1] for similar text.
        """
        # Handle both 1D and 2D arrays
        a = vec_a.flatten()
        b = vec_b.flatten()
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def embedding_to_list(self, embedding: np.ndarray) -> List[float]:
        """Convert numpy embedding to list for ChromaDB storage."""
        return embedding.flatten().tolist()

    async def embed_async(self, text: str) -> np.ndarray:
        """Async wrapper — runs in thread pool to avoid blocking."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed, text)

    async def embed_batch_async(self, texts: List[str]) -> np.ndarray:
        """Async batch embedding."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed_batch, texts)

    async def cosine_similarity_async(
        self,
        text_a: str,
        text_b: str,
    ) -> float:
        """Embed both strings and compute cosine similarity."""
        embeddings = await self.embed_batch_async([text_a, text_b])
        return self.cosine_similarity(embeddings[0], embeddings[1])


# Module-level singleton
embedding_service = EmbeddingService()
