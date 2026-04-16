"""
services/nlp_cache.py — Upstash Redis cache for NLP preprocessing results.

Uses the Upstash Redis REST API (no redis-py driver needed — just httpx).

Cache key : "nlp:" + SHA256(raw_text)[:16]
TTL       : 7 days (604800 seconds)
Expected hit rate: 40-60% (same IT errors repeat constantly)
Benefit   : skips ~50-100ms spaCy processing on cache hits

Falls back silently to None on any network/config error so the pipeline
never breaks if Upstash is unreachable.
"""

import hashlib
import json
import asyncio
from typing import Optional
from loguru import logger

import httpx

from core.config import settings

# 7 days in seconds
_TTL_SECONDS = 604_800
_KEY_PREFIX = "nlp:"


class NLPCache:
    """
    Thin async wrapper around the Upstash Redis REST API.

    Only two operations needed:
        get(text)       → dict | None
        set(text, data) → None

    Disabled automatically when UPSTASH_REDIS_REST_URL is not configured.
    """

    def __init__(self):
        self._url = settings.UPSTASH_REDIS_REST_URL.rstrip("/")
        self._token = settings.UPSTASH_REDIS_REST_TOKEN
        self._enabled = bool(self._url and self._token)
        self._hits = 0
        self._misses = 0

        if self._enabled:
            logger.info(f"NLP cache: Upstash Redis enabled ({self._url})")
        else:
            logger.warning(
                "NLP cache: UPSTASH_REDIS_REST_URL or TOKEN not set — "
                "NLP preprocessing cache disabled."
            )

    def _cache_key(self, text: str) -> str:
        """SHA256 hash of the raw text, prefixed."""
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        return f"{_KEY_PREFIX}{digest}"

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._token}"}

    async def get(self, text: str) -> Optional[dict]:
        """
        Fetch cached NLP result for the given raw text.

        Returns:
            Deserialized dict if cache hit, None otherwise.
        """
        if not self._enabled:
            return None

        key = self._cache_key(text)
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(
                    f"{self._url}/get/{key}",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                data = resp.json()
                value = data.get("result")

                if value is None:
                    self._misses += 1
                    return None

                self._hits += 1
                logger.debug(f"NLP cache HIT  key={key}")
                return json.loads(value)

        except Exception as e:
            logger.debug(f"NLP cache GET error (non-fatal): {e}")
            self._misses += 1
            return None

    async def set(self, text: str, result: dict) -> None:
        """
        Store NLP result in Upstash with 7-day TTL.
        Fire-and-forget — errors are logged but never raised.
        """
        if not self._enabled:
            return

        key = self._cache_key(text)
        try:
            payload = json.dumps(result)
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.post(
                    f"{self._url}/set/{key}",
                    headers=self._headers(),
                    # Upstash REST: SET key value EX ttl
                    json=["SET", key, payload, "EX", _TTL_SECONDS],
                )
                resp.raise_for_status()
                logger.debug(f"NLP cache SET  key={key} ttl={_TTL_SECONDS}s")

        except Exception as e:
            logger.debug(f"NLP cache SET error (non-fatal): {e}")

    @property
    def stats(self) -> dict:
        total = self._hits + self._misses
        return {
            "enabled": self._enabled,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 3) if total else 0.0,
        }


# Module-level singleton
nlp_cache = NLPCache()
