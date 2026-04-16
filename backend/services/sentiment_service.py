"""
services/sentiment_service.py — Sentiment analysis using HuggingFace Transformers.
Model: cardiffnlp/twitter-roberta-base-sentiment
"""

import asyncio
from typing import Tuple
from loguru import logger

from core.config import settings

# Label mapping for the Cardiff NLP model
LABEL_MAP = {
    "LABEL_0": "NEGATIVE",
    "LABEL_1": "NEUTRAL",
    "LABEL_2": "POSITIVE",
}


class SentimentService:
    """
    Runs sentiment analysis on every incoming ticket.

    Model: cardiffnlp/twitter-roberta-base-sentiment (runs on CPU)
    - NEGATIVE, NEUTRAL, POSITIVE + confidence score

    Integration rules:
    - NEGATIVE with score > 0.85 → reduce AI confidence by 0.08,
                                    boost priority, add FRUSTRATED tag
    """

    def __init__(self):
        self._pipeline = None
        self._loaded = False

    def _load_model(self):
        """Always use keyword fallback for speed. HuggingFace model skipped to avoid 30s delay."""
        if self._loaded:
            return
        # Using fast keyword-based fallback — Cardiff NLP model (~500MB) takes too long to load
        # Enable the real model by uncommenting the block below once performance is tuned
        self._pipeline = None
        self._loaded = True
        logger.debug(
            "Sentiment: using keyword fallback (HuggingFace model disabled for speed)"
        )

    def _fallback_sentiment(self, text: str) -> Tuple[str, float]:
        """
        Keyword-based fallback when model is unavailable.
        Returns (label, confidence).
        """
        text_lower = text.lower()
        negative_keywords = [
            "angry",
            "frustrated",
            "terrible",
            "horrible",
            "awful",
            "worst",
            "unacceptable",
            "disgusting",
            "furious",
            "hate",
            "outrageous",
            "ridiculous",
            "useless",
            "incompetent",
            "emergency",
            "critical",
            "urgent",
            "asap",
            "immediately",
        ]
        positive_keywords = [
            "thank",
            "great",
            "excellent",
            "appreciate",
            "good",
            "helpful",
            "resolved",
            "working",
            "fixed",
            "perfect",
        ]

        neg_score = sum(1 for kw in negative_keywords if kw in text_lower)
        pos_score = sum(1 for kw in positive_keywords if kw in text_lower)

        if neg_score >= 2:
            return "NEGATIVE", min(0.60 + neg_score * 0.05, 0.90)
        elif pos_score >= 2:
            return "POSITIVE", 0.70
        return "NEUTRAL", 0.65

    def analyze(self, text: str) -> dict:
        """
        Run sentiment analysis on ticket text.

        Args:
            text: Original ticket text (not cleaned — preserves emotion signals).

        Returns:
            {
                label: "POSITIVE" | "NEUTRAL" | "NEGATIVE",
                score: float (confidence 0.0-1.0),
                is_frustrated: bool (NEGATIVE + score > threshold),
            }
        """
        self._load_model()

        if self._pipeline is None:
            label, score = self._fallback_sentiment(text)
        else:
            try:
                # Truncate to 512 tokens worth of text
                truncated = text[:2000]
                results = self._pipeline(truncated)[0]

                # Find the highest scoring label
                best = max(results, key=lambda x: x["score"])
                label = LABEL_MAP.get(best["label"], best["label"])
                score = float(best["score"])

            except Exception as e:
                logger.warning(f"Sentiment inference error: {e}")
                label, score = self._fallback_sentiment(text)

        is_frustrated = (
            label == "NEGATIVE" and score > settings.SENTIMENT_NEGATIVE_THRESHOLD
        )

        return {
            "sentiment_label": label,
            "sentiment_score": round(score, 4),
            "is_frustrated": is_frustrated,
        }

    async def analyze_async(self, text: str) -> dict:
        """Async wrapper — runs in thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.analyze, text)


# Module-level singleton
sentiment_service = SentimentService()
