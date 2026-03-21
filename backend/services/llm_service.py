"""
services/llm_service.py — Agent 4: Ollama Mistral response generation.

Implements RAG (Retrieval-Augmented Generation) using retrieved solutions
as context. Includes hallucination detection via cosine similarity check.
"""

import asyncio
import time
import httpx
from typing import Optional, Dict
from loguru import logger

from core.config import settings
from services.embedding_service import embedding_service


# ─── Prompt template ──────────────────────────────────────────────────
RAG_PROMPT_TEMPLATE = """\
You are a professional IT support specialist.

User ticket: {ticket_text}
Category: {category}

Similar resolved ticket solution: {retrieved_solution}

Write a professional support response in 3-4 sentences.
Be specific and actionable. Use numbered steps if needed.
Do not add disclaimers or say 'I hope this helps'.
Do not start with 'I' or greetings.
"""

KNOWLEDGE_ARTICLE_PROMPT = """\
Convert this resolved support ticket into a knowledge base article.

Original issue: {ticket_text}
Category: {category}
Resolution applied: {solution}
Resolution time: {resolution_hours} hours

Output ONLY valid JSON in this exact format:
{{
  "title": "concise issue title",
  "problem_description": "one sentence",
  "likely_cause": "one sentence",
  "solution_steps": ["step 1", "step 2", "step 3"],
  "prevention": "one sentence",
  "tags": ["tag1", "tag2", "tag3"],
  "difficulty": "Easy",
  "estimated_resolution_time": "X minutes"
}}
"""

ROOT_CAUSE_PROMPT = """\
Multiple support tickets report issues with: {keywords}
Category: {category}
Ticket count in last {window} minutes: {count}

What is the most likely root cause? Answer in one concise sentence.
"""


class LLMService:
    """
    Agent 4 of the TicketFlow pipeline.

    Responsibilities:
    - Call Ollama (Mistral-Nemo) for response generation
    - Build RAG prompt from retrieved solution context
    - Detect hallucination via cosine similarity check
    - Fall back to retrieved solution if hallucination detected
    - Generate knowledge base articles from resolved tickets
    - Generate root cause hypotheses for spike incidents
    """

    def __init__(self):
        self._client = None
        self.ollama_url = settings.OLLAMA_URL
        self.model = settings.OLLAMA_MODEL

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client for Ollama API."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=5.0)
            )
        return self._client

    async def _call_ollama(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 250,
    ) -> Optional[str]:
        """
        Call Ollama API to generate text.

        Args:
            prompt: Input prompt string.
            temperature: Sampling temperature (lower = more deterministic).
            max_tokens: Maximum tokens to generate.

        Returns:
            Generated text string, or None on error.
        """
        try:
            client = self._get_client()
            response = await client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                        "stop": ["\n\n\n"],
                    },
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()

        except httpx.ConnectError:
            logger.warning(
                f"Ollama not reachable at {self.ollama_url}. "
                f"Is Ollama running? (ollama serve)"
            )
            return None
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            return None

    async def generate_response(
        self,
        ticket_text: str,
        category: str,
        retrieved_solution: str,
        routing_decision: str,
    ) -> dict:
        """
        Agent 4 main method: Generate a support response via RAG.

        Only called when routing != ESCALATE_TO_HUMAN.

        Args:
            ticket_text: Original ticket text.
            category: Predicted category.
            retrieved_solution: Best solution from ChromaDB.
            routing_decision: Current routing decision.

        Returns:
            Agent 4 output dict per spec.
        """
        # Step 1: Only call LLM for AUTO_RESOLVE or SUGGEST paths
        if routing_decision == "ESCALATE_TO_HUMAN":
            return {
                "generated_response": None,
                "generation_time_ms": 0,
                "hallucination_detected": False,
                "fallback_used": False,
                "model_used": None,
            }

        start_time = time.time()

        # Step 2: Build RAG prompt
        prompt = RAG_PROMPT_TEMPLATE.format(
            ticket_text=ticket_text[:800],   # truncate long tickets
            category=category,
            retrieved_solution=retrieved_solution[:600],
        )

        # Step 3: Call Ollama
        generated_text = await self._call_ollama(prompt)
        generation_time_ms = int((time.time() - start_time) * 1000)

        hallucination_detected = False
        fallback_used = False

        if generated_text is None:
            # Ollama unavailable — use retrieved solution directly
            generated_text = retrieved_solution
            fallback_used = True
        else:
            # Step 4: Hallucination detection
            similarity = await self._check_hallucination(
                generated_text,
                retrieved_solution,
            )
            if similarity < settings.HALLUCINATION_SIM_THRESHOLD:
                hallucination_detected = True
                fallback_used = True
                generated_text = retrieved_solution
                logger.warning(
                    f"Hallucination detected (similarity={similarity:.3f} < "
                    f"{settings.HALLUCINATION_SIM_THRESHOLD}). "
                    f"Falling back to retrieved solution."
                )

        return {
            "generated_response": generated_text,
            "generation_time_ms": generation_time_ms,
            "hallucination_detected": hallucination_detected,
            "fallback_used": fallback_used,
            "model_used": self.model if not fallback_used else "fallback",
        }

    async def _check_hallucination(
        self,
        generated_text: str,
        reference_text: str,
    ) -> float:
        """
        Compare response embedding with reference solution embedding.
        If cosine similarity < HALLUCINATION_SIM_THRESHOLD, flag as hallucinated.

        Returns:
            Cosine similarity (0.0-1.0).
        """
        try:
            similarity = await embedding_service.cosine_similarity_async(
                generated_text, reference_text
            )
            return similarity
        except Exception as e:
            logger.warning(f"Hallucination check error: {e}. Assuming ok.")
            return 1.0  # assume ok on error

    async def generate_knowledge_article(
        self,
        ticket_text: str,
        category: str,
        solution: str,
        resolution_hours: float,
    ) -> Optional[dict]:
        """
        Generate a structured KB article from a resolved ticket.

        Returns:
            Parsed JSON dict or None on failure.
        """
        import json

        prompt = KNOWLEDGE_ARTICLE_PROMPT.format(
            ticket_text=ticket_text[:500],
            category=category,
            solution=solution[:500],
            resolution_hours=round(resolution_hours, 1),
        )

        response = await self._call_ollama(prompt, temperature=0.2, max_tokens=400)

        if response is None:
            return None

        # Extract JSON from response (handle markdown code blocks)
        json_text = response
        if "```" in json_text:
            start = json_text.find("{")
            end = json_text.rfind("}") + 1
            json_text = json_text[start:end]

        try:
            article_data = json.loads(json_text)
            return article_data
        except json.JSONDecodeError as e:
            logger.warning(f"Knowledge article JSON parse error: {e}")
            return None

    async def generate_root_cause_hypothesis(
        self,
        keywords: list,
        category: str,
        ticket_count: int,
        window_minutes: int,
    ) -> str:
        """
        Generate a one-sentence root cause hypothesis for an incident spike.

        Returns:
            Hypothesis string, or generic fallback.
        """
        prompt = ROOT_CAUSE_PROMPT.format(
            keywords=", ".join(keywords[:5]),
            category=category,
            count=ticket_count,
            window=window_minutes,
        )

        response = await self._call_ollama(
            prompt, temperature=0.1, max_tokens=100
        )

        if response:
            # Take only the first sentence
            first_sentence = response.split(".")[0].strip()
            return first_sentence + "."

        # Fallback hypothesis
        return (
            f"Possible {category.lower()} system issue affecting multiple users, "
            f"related to: {', '.join(keywords[:3])}."
        )


# Module-level singleton
llm_service = LLMService()
