"""
services/nlp_cache.py — Upstash Redis cache for NLP preprocessing results
Caches the output of nlp_service.preprocess() to speed up duplicate tickets
"""

import json
import hashlib
import asyncio
from loguru import logger
from typing import Optional, Dict, Any
from urllib.parse import quote

from core.config import settings


class NLPCache:
    """
    Upstash Redis-based cache for NLP preprocessing results.
    
    - TTL: 7 days (604800 seconds)
    - Key format: nlp:{text_hash}
    - Value: JSON-serialized dict
    - Uses Upstash REST API (HTTP) instead of socket connection
    """

    def __init__(self):
        """Initialize Upstash Redis REST client."""
        self.enabled = False
        self.http_client = None
        
        if settings.UPSTASH_REDIS_REST_URL and settings.UPSTASH_REDIS_REST_TOKEN:
            try:
                # Use HTTP REST client for Upstash
                import httpx
                self.http_client = httpx.AsyncClient()
                self.enabled = True
                logger.info(f"NLP cache: Upstash Redis enabled ({settings.UPSTASH_REDIS_REST_URL})")
            except ImportError:
                logger.warning("httpx not installed. NLP cache disabled.")
        else:
            logger.warning("Upstash credentials not configured. NLP cache disabled.")

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text hash."""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"nlp:{text_hash}"

    async def get(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Get NLP result from cache.
        
        Args:
            text: Input text
            
        Returns:
            Dict with NLP result, or None if not cached
        """
        if not self.enabled or not self.http_client:
            return None
        
        try:
            key = self._get_cache_key(text)
            
            # Upstash REST API GET request
            url = f"{settings.UPSTASH_REDIS_REST_URL}/get/{key}"
            headers = {
                "Authorization": f"Bearer {settings.UPSTASH_REDIS_REST_TOKEN}"
            }
            
            response = await self.http_client.get(url, headers=headers, timeout=5.0)
            
            if response.status_code == 200:
                data = response.json()
                result_value = data.get("result")
                
                # If result exists, parse it
                if result_value:
                    try:
                        if isinstance(result_value, str):
                            # Parse JSON string
                            parsed = json.loads(result_value)
                            logger.debug(f"NLP cache HIT  key={key}")
                            return parsed
                        elif isinstance(result_value, dict):
                            # Already a dict
                            logger.debug(f"NLP cache HIT  key={key}")
                            return result_value
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.warning(f"Could not parse cached JSON for {key}: {e}")
                        return None
                
                logger.debug(f"NLP cache MISS (empty) key={key}")
                return None
            else:
                logger.debug(f"NLP cache MISS (status {response.status_code}) key={key}")
                return None
                
        except asyncio.TimeoutError:
            logger.warning("NLP cache GET timeout")
            return None
        except Exception as e:
            logger.warning(f"NLP cache GET error: {e}")
            return None

    async def set(self, text: str, value: Dict[str, Any], ttl: int = 604800) -> bool:
        """
        Store NLP result in cache using Upstash REST API.
        
        Args:
            text: Input text
            value: NLP result dict
            ttl: Time to live in seconds (default 7 days = 604800)
            
        Returns:
            True if stored successfully
        """
        if not self.enabled or not self.http_client:
            return False
        
        try:
            key = self._get_cache_key(text)
            json_value = json.dumps(value)
            
            # URL-encode the JSON value for REST API
            encoded_value = quote(json_value)
            
            # Upstash REST API SET request
            # Format: /set/{key}/{value}?EX={ttl}
            url = f"{settings.UPSTASH_REDIS_REST_URL}/set/{key}/{encoded_value}"
            headers = {
                "Authorization": f"Bearer {settings.UPSTASH_REDIS_REST_TOKEN}"
            }
            
            params = {"EX": ttl}
            
            response = await self.http_client.get(
                url,
                headers=headers,
                params=params,
                timeout=5.0
            )
            
            if response.status_code == 200:
                logger.debug(f"NLP cache SET  key={key} ttl={ttl}s")
                return True
            else:
                logger.warning(f"NLP cache SET failed (status {response.status_code})")
                return False
                
        except asyncio.TimeoutError:
            logger.warning("NLP cache SET timeout")
            return False
        except Exception as e:
            logger.warning(f"NLP cache SET error: {e}")
            return False

    async def delete(self, text: str) -> bool:
        """
        Delete entry from cache.
        
        Args:
            text: Input text
            
        Returns:
            True if deleted successfully
        """
        if not self.enabled or not self.http_client:
            return False
        
        try:
            key = self._get_cache_key(text)
            
            # Upstash REST API DEL request
            url = f"{settings.UPSTASH_REDIS_REST_URL}/del/{key}"
            headers = {
                "Authorization": f"Bearer {settings.UPSTASH_REDIS_REST_TOKEN}"
            }
            
            response = await self.http_client.get(url, headers=headers, timeout=5.0)
            
            if response.status_code == 200:
                logger.debug(f"NLP cache DELETE  key={key}")
                return True
            else:
                logger.warning(f"NLP cache DELETE failed (status {response.status_code})")
                return False
                
        except Exception as e:
            logger.warning(f"NLP cache DELETE error: {e}")
            return False

    async def flush(self) -> bool:
        """
        Flush all cache entries (use with caution!).
        
        Returns:
            True if flushed successfully
        """
        if not self.enabled or not self.http_client:
            return False
        
        try:
            url = f"{settings.UPSTASH_REDIS_REST_URL}/flushdb"
            headers = {
                "Authorization": f"Bearer {settings.UPSTASH_REDIS_REST_TOKEN}"
            }
            
            response = await self.http_client.get(url, headers=headers, timeout=5.0)
            
            if response.status_code == 200:
                logger.info("NLP cache FLUSHED")
                return True
            else:
                logger.warning(f"NLP cache FLUSH failed (status {response.status_code})")
                return False
                
        except Exception as e:
            logger.warning(f"NLP cache FLUSH error: {e}")
            return False


# Module-level singleton
nlp_cache = NLPCache()