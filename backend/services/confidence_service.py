"""
services/confidence_service.py — Agent 3 (Part 1): Composite confidence scoring.

Computes the final confidence score from 3 weighted components:
  - Model probability (50%)
  - Vector similarity (35%)
  - Domain keyword boost (15%)

Then applies:
  - Sentiment adjustment (-0.08 if very negative)
  - SLA override (force escalate if breach risk > 75%)
  - Security override (always escalate)
"""

from typing import Dict, Optional
from loguru import logger

from core.config import settings
from utils.helpers import clamp


class ConfidenceService:
    """
    Agent 3 Part 1: Computes composite confidence and routing decision.

    Formula:
        confidence = (0.5 × model_confidence)
                   + (0.35 × similarity_score)
                   + (0.15 × keyword_boost)

    Sentiment adjustment:
        if NEGATIVE and score > 0.85: confidence -= 0.08

    Override logic (takes priority over confidence):
        Security category → always ESCALATE_TO_HUMAN
        SLA breach probability > 0.75 → ESCALATE_TO_HUMAN

    Routing based on confidence:
        >= 0.85 → AUTO_RESOLVE
        >= 0.60 → SUGGEST_TO_AGENT
        <  0.60 → ESCALATE_TO_HUMAN
    """

    def _compute_keyword_boost(
        self,
        text: str,
        category: str,
    ) -> float:
        """
        Compute domain keyword boost (0.0 to 1.0).

        Logic:
        - Get the keyword list for predicted category
        - Count how many appear in the ticket text
        - Normalize: min(count / 5, 1.0)
        """
        domain_keywords = settings.DOMAIN_KEYWORDS.get(category, [])
        if not domain_keywords:
            return 0.0

        text_lower = text.lower()
        matches = sum(1 for kw in domain_keywords if kw in text_lower)
        boost = min(matches / 5.0, 1.0)
        return round(boost, 4)

    def compute(
        self,
        model_confidence: float,
        similarity_score: float,
        ticket_text: str,
        category: str,
        sentiment_label: str,
        sentiment_score: float,
        sla_breach_probability: float,
        user_tier: str = "Standard",
    ) -> dict:
        """
        Compute composite confidence and routing decision.

        Args:
            model_confidence: Classifier softmax probability for top class.
            similarity_score: Top cosine similarity from ChromaDB retrieval.
            ticket_text: Original or lightly-cleaned ticket text.
            category: Predicted category (for Security override + keyword boost).
            sentiment_label: "POSITIVE" | "NEUTRAL" | "NEGATIVE"
            sentiment_score: Confidence of sentiment prediction.
            sla_breach_probability: From SLA predictor (0.0-1.0).
            user_tier: User subscription tier.

        Returns:
            Agent 3 output dict with confidence_score, routing_decision,
            confidence_breakdown, and override flags.
        """
        # ── Step 1: Security override ─────────────────────────────────
        if category == "Security":
            logger.debug(f"Security override: ESCALATE_TO_HUMAN")
            return {
                "confidence_score": 0.0,
                "routing_decision": "ESCALATE_TO_HUMAN",
                "confidence_breakdown": {
                    "model_prob_component": 0.0,
                    "similarity_component": 0.0,
                    "keyword_component": 0.0,
                },
                "sla_override": False,
                "security_override": True,
                "reason": "Security tickets always require human review",
            }

        # ── Step 2: Keyword boost ─────────────────────────────────────
        keyword_boost = self._compute_keyword_boost(ticket_text, category)

        # ── Step 3: Composite confidence ─────────────────────────────
        model_component    = 0.50 * model_confidence
        similarity_component = 0.35 * similarity_score
        keyword_component  = 0.15 * keyword_boost

        confidence = model_component + similarity_component + keyword_component

        # ── Step 4: Sentiment adjustment ──────────────────────────────
        sentiment_reduced = False
        if (
            sentiment_label == "NEGATIVE"
            and sentiment_score > settings.SENTIMENT_NEGATIVE_THRESHOLD
        ):
            confidence -= 0.08
            sentiment_reduced = True
            logger.debug(
                f"Sentiment adjustment: -0.08 for frustrated user "
                f"(score={sentiment_score:.2f})"
            )

        confidence = clamp(confidence, 0.0, 1.0)

        # ── Step 5: SLA override ──────────────────────────────────────
        sla_override = sla_breach_probability > settings.SLA_BREACH_THRESHOLD
        if sla_override:
            logger.debug(
                f"SLA override triggered: breach_prob={sla_breach_probability:.2f}"
            )
            return {
                "confidence_score": round(confidence, 4),
                "routing_decision": "ESCALATE_TO_HUMAN",
                "confidence_breakdown": {
                    "model_prob_component": round(model_component, 4),
                    "similarity_component": round(similarity_component, 4),
                    "keyword_component": round(keyword_component, 4),
                },
                "sla_override": True,
                "security_override": False,
                "sentiment_adjusted": sentiment_reduced,
                "reason": f"SLA breach probability {sla_breach_probability:.0%} exceeds threshold",
            }

        # ── Step 6: Standard routing ──────────────────────────────────
        if confidence >= settings.CONFIDENCE_HIGH_THRESHOLD:
            routing = "AUTO_RESOLVE"
        elif confidence >= settings.CONFIDENCE_LOW_THRESHOLD:
            routing = "SUGGEST_TO_AGENT"
        else:
            routing = "ESCALATE_TO_HUMAN"

        logger.debug(
            f"Confidence: {confidence:.3f} → routing: {routing} "
            f"(model={model_component:.3f}, sim={similarity_component:.3f}, "
            f"kw={keyword_component:.3f})"
        )

        # ── Enterprise users get slightly better auto-resolve chance ──
        if user_tier == "Enterprise" and routing == "SUGGEST_TO_AGENT":
            if confidence >= (settings.CONFIDENCE_LOW_THRESHOLD + 0.10):
                routing = "AUTO_RESOLVE"
                logger.debug("Enterprise tier upgrade: SUGGEST → AUTO_RESOLVE")

        return {
            "confidence_score": round(confidence, 4),
            "routing_decision": routing,
            "confidence_breakdown": {
                "model_prob_component": round(model_component, 4),
                "similarity_component": round(similarity_component, 4),
                "keyword_component": round(keyword_component, 4),
            },
            "sla_override": False,
            "security_override": False,
            "sentiment_adjusted": sentiment_reduced,
            "reason": f"Confidence {confidence:.0%} → {routing}",
        }


# Module-level singleton
confidence_service = ConfidenceService()
