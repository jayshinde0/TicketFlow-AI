"""
services/cache_service.py — LRU caching layer for performance optimization.
Caches TF-IDF vectors, similarity results, and Ollama responses.
"""

import hashlib
from typing import Optional, Any
from functools import lru_cache
from loguru import logger

try:
    from cachetools import TTLCache
except ImportError:
    TTLCache = None
    logger.warning("cachetools not installed; caching disabled")


class CacheService:
    """
    LRU + TTL caching for frequently accessed data.

    Caches:
    - TF-IDF vectors: TTL 1 hour, max 500 entries
    - Similarity results: TTL 30 minutes, max 200 entries
    - Ollama responses: TTL 1 hour, max 100 entries (keyed by SHA256 of prompt)
    """

    def __init__(self):
        if TTLCache is not None:
            self._tfidf_cache = TTLCache(maxsize=500, ttl=3600)  # 1 hour
            self._similarity_cache = TTLCache(maxsize=200, ttl=1800)  # 30 min
            self._llm_cache = TTLCache(maxsize=100, ttl=3600)  # 1 hour
            self._enabled = True
        else:
            self._tfidf_cache = {}
            self._similarity_cache = {}
            self._llm_cache = {}
            self._enabled = False

        self._hits = 0
        self._misses = 0

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    def _hash_key(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    # ── TF-IDF cache ──────────────────────────────────────────────────
    def get_tfidf(self, text: str) -> Optional[Any]:
        key = self._hash_key(text)
        result = self._tfidf_cache.get(key)
        if result is not None:
            self._hits += 1
            return result
        self._misses += 1
        return None

    def set_tfidf(self, text: str, vector: Any) -> None:
        key = self._hash_key(text)
        self._tfidf_cache[key] = vector

    # ── Similarity cache ──────────────────────────────────────────────
    def get_similarity(self, text: str, category: str) -> Optional[Any]:
        key = self._hash_key(f"{text}|{category}")
        result = self._similarity_cache.get(key)
        if result is not None:
            self._hits += 1
            return result
        self._misses += 1
        return None

    def set_similarity(self, text: str, category: str, results: Any) -> None:
        key = self._hash_key(f"{text}|{category}")
        self._similarity_cache[key] = results

    # ── LLM response cache ────────────────────────────────────────────
    def get_llm_response(self, prompt: str) -> Optional[str]:
        key = self._hash_key(prompt)
        result = self._llm_cache.get(key)
        if result is not None:
            self._hits += 1
            return result
        self._misses += 1
        return None

    def set_llm_response(self, prompt: str, response: str) -> None:
        key = self._hash_key(prompt)
        self._llm_cache[key] = response

    # ── Stats ─────────────────────────────────────────────────────────
    def get_stats(self) -> dict:
        return {
            "enabled": self._enabled,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self.hit_rate, 3),
            "tfidf_size": len(self._tfidf_cache),
            "similarity_size": len(self._similarity_cache),
            "llm_size": len(self._llm_cache),
        }

    def clear(self) -> None:
        self._tfidf_cache.clear() if hasattr(self._tfidf_cache, "clear") else None
        (
            self._similarity_cache.clear()
            if hasattr(self._similarity_cache, "clear")
            else None
        )
        self._llm_cache.clear() if hasattr(self._llm_cache, "clear") else None
        self._hits = 0
        self._misses = 0


# Module-level singleton
cache_service = CacheService()
