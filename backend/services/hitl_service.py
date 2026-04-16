"""
services/hitl_service.py — Agent 3 (Part 2): Human-in-the-Loop routing orchestrator.

Orchestrates the full Agent 3 decision and annotates the ticket with
all HITL metadata (routing, priority boost, frustrated flag, etc.)
"""

from typing import Dict, Optional
from loguru import logger

from services.confidence_service import confidence_service
from utils.helpers import boost_priority
from core.config import settings


class HITLService:
    """
    Agent 3 Part 2 — Final routing decision with all override logic applied.

    Takes outputs from Agents 1, 2, and Sentiment service, applies
    confidence_service.compute(), then makes final HITL annotation.

    Returns the complete routing packet ready for ticket document storage.
    """

    def route(
        self,
        # Agent 1 outputs
        category: str,
        model_confidence: float,
        priority: str,
        priority_confidence: float,
        # Agent 2 outputs
        top_similarity_score: float,
        # Sentiment outputs
        sentiment_label: str,
        sentiment_score: float,
        is_frustrated: bool,
        # SLA output
        sla_breach_probability: float,
        # Ticket metadata
        ticket_text: str,
        user_tier: str = "Standard",
    ) -> dict:
        """
        Compute final routing decision with all adjustments.

        Returns:
            Complete HITL routing result dict.
        """
        # ── Run confidence computation (Agent 3 core) ─────────────────
        confidence_result = confidence_service.compute(
            model_confidence=model_confidence,
            similarity_score=top_similarity_score,
            ticket_text=ticket_text,
            category=category,
            sentiment_label=sentiment_label,
            sentiment_score=sentiment_score,
            sla_breach_probability=sla_breach_probability,
            user_tier=user_tier,
        )

        routing_decision = confidence_result["routing_decision"]
        confidence_score = confidence_result["confidence_score"]

        # ── Apply sentiment priority boost ────────────────────────────
        adjusted_priority = priority
        if is_frustrated:
            adjusted_priority = boost_priority(priority)
            if adjusted_priority != priority:
                logger.debug(
                    f"Sentiment priority boost: {priority} → {adjusted_priority}"
                )

        # ── Database domain fast-escalate ─────────────────────────────
        if category == "Database" and routing_decision == "AUTO_RESOLVE":
            routing_decision = "SUGGEST_TO_AGENT"
            logger.debug("Database ticket: downgrade AUTO_RESOLVE → SUGGEST_TO_AGENT")

        # ── Auto-resolve rate target check ────────────────────────────
        # Some domains have inherently low auto-resolve targets.
        # Never auto-resolve Network, Hardware if confidence < 0.90
        if routing_decision == "AUTO_RESOLVE":
            target = settings.AUTO_RESOLVE_TARGETS.get(category, 0.5)
            if target <= 0.25 and confidence_score < 0.90:
                routing_decision = "SUGGEST_TO_AGENT"
                logger.debug(
                    f"Low auto-resolve target domain ({category}, target={target:.0%}): "
                    f"upgrading to SUGGEST_TO_AGENT"
                )

        return {
            "confidence_score": confidence_score,
            "routing_decision": routing_decision,
            "confidence_breakdown": confidence_result["confidence_breakdown"],
            "sla_override": confidence_result.get("sla_override", False),
            "security_override": confidence_result.get("security_override", False),
            "sentiment_adjusted": confidence_result.get("sentiment_adjusted", False),
            "priority": adjusted_priority,
            "priority_boosted": adjusted_priority != priority,
            "is_frustrated": is_frustrated,
            "routing_reason": confidence_result.get("reason", ""),
        }


# Module-level singleton
hitl_service = HITLService()
