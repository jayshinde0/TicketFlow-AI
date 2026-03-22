"""
services/ollama_provider.py — Clean Ollama abstraction layer.
Centralises all Ollama HTTP calls with retry logic and structured responses.
"""

import asyncio
import json
from typing import Optional, Dict, Any, List
from loguru import logger
import httpx

from core.config import settings


class OllamaProvider:
    """
    Abstraction layer for all Ollama LLM interactions.

    Features:
    - 30 s timeout per request
    - 2 automatic retries on timeout / connection error
    - Structured JSON parsing with fallback
    - Centralised error handling
    """

    def __init__(self):
        self._base_url: str = settings.OLLAMA_URL
        self._model: str = settings.OLLAMA_MODEL
        self._timeout: float = 30.0
        self._max_retries: int = 2
        self._prompts: Dict[str, str] = {}

    # ── prompt template loading ───────────────────────────────────────
    def load_prompt(self, name: str) -> str:
        """Load a prompt template from the prompts/ directory."""
        if name in self._prompts:
            return self._prompts[name]

        from pathlib import Path
        prompt_dir = Path(__file__).parent.parent / "prompts"
        prompt_path = prompt_dir / f"{name}.txt"

        if not prompt_path.exists():
            logger.warning(f"Prompt template '{name}' not found at {prompt_path}")
            return ""

        text = prompt_path.read_text(encoding="utf-8")
        self._prompts[name] = text
        return text

    # ── core generation with retry ────────────────────────────────────
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        model: Optional[str] = None,
    ) -> str:
        """
        Send a generation request to Ollama with retry logic.

        Args:
            prompt: The full prompt string.
            temperature: Sampling temperature (0.0–1.0).
            max_tokens: Maximum tokens in response.
            model: Override default model.

        Returns:
            Generated text string. Empty string on total failure.
        """
        target_model = model or self._model
        payload = {
            "model": target_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        last_error = None
        for attempt in range(1, self._max_retries + 2):  # 1 initial + 2 retries
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    resp = await client.post(
                        f"{self._base_url}/api/generate",
                        json=payload,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    return data.get("response", "").strip()

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                if attempt <= self._max_retries:
                    wait = 2 ** attempt
                    logger.warning(
                        f"Ollama attempt {attempt}/{self._max_retries + 1} failed "
                        f"({type(e).__name__}). Retrying in {wait}s..."
                    )
                    await asyncio.sleep(wait)
                else:
                    logger.error(
                        f"Ollama generation failed after {self._max_retries + 1} attempts: {e}"
                    )
            except Exception as e:
                logger.error(f"Ollama generation unexpected error: {e}")
                last_error = e
                break

        return ""

    # ── structured JSON generation ────────────────────────────────────
    async def generate_json(
        self,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a response and parse it as JSON.
        Returns None if generation fails or JSON is invalid.
        """
        raw = await self.generate(prompt, temperature=temperature, max_tokens=max_tokens)
        if not raw:
            return None

        # Try to extract JSON from the response
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # Try to find JSON block in markdown fences
        import re
        json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Try to find first { and last }
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(raw[start:end + 1])
            except json.JSONDecodeError:
                pass

        logger.warning(f"Could not parse Ollama response as JSON: {raw[:200]}")
        return None

    # ── zero-shot classification ──────────────────────────────────────
    async def classify_zero_shot(
        self,
        text: str,
        categories: List[str],
    ) -> Optional[Dict[str, Any]]:
        """
        Use Ollama for zero-shot classification when ML confidence is low.

        Returns:
            Dict with 'category' and 'confidence' keys, or None on failure.
        """
        template = self.load_prompt("zero_shot_category")
        if not template:
            # Inline fallback prompt
            template = (
                "You are a support ticket classifier. Classify the following ticket "
                "into exactly ONE of these categories: {categories}\n\n"
                "Ticket: {text}\n\n"
                "Respond with ONLY a JSON object: {{\"category\": \"<category>\", \"confidence\": <0.0-1.0>}}"
            )

        prompt = template.format(
            categories=", ".join(categories),
            text=text[:1000],
        )

        result = await self.generate_json(prompt, temperature=0.1)
        if result and "category" in result:
            # Validate category is in the allowed list
            if result["category"] in categories:
                return result
            # Try case-insensitive match
            for cat in categories:
                if cat.lower() == result["category"].lower():
                    result["category"] = cat
                    return result

        return None

    # ── threat analysis ───────────────────────────────────────────────
    async def analyze_threat(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Analyse a ticket for security threats using Ollama.

        Returns:
            Structured dict with threat_detected, threat_type, severity,
            recommended_action, or None on failure.
        """
        template = self.load_prompt("threat_analysis")
        if not template:
            template = (
                "You are a cybersecurity analyst. Analyse this support ticket for security threats.\n\n"
                "Ticket: {text}\n\n"
                "Respond with ONLY a JSON object:\n"
                "{{\n"
                '  "threat_detected": true/false,\n'
                '  "threat_type": "phishing|malware|data_breach|unauthorized_access|social_engineering|insider_threat|none",\n'
                '  "severity": "critical|high|medium|low|none",\n'
                '  "confidence": 0.0-1.0,\n'
                '  "recommended_action": "brief action description",\n'
                '  "indicators": ["list", "of", "threat", "indicators"]\n'
                "}}"
            )

        prompt = template.format(text=text[:2000])
        return await self.generate_json(prompt, temperature=0.1, max_tokens=512)

    # ── health check ──────────────────────────────────────────────────
    async def is_available(self) -> bool:
        """Check if Ollama is reachable."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False


# Module-level singleton
ollama_provider = OllamaProvider()
