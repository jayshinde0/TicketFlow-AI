"""
services/audit_service.py — Immutable audit trail for all AI decisions.
Writes one audit log per ticket pipeline run.
"""

from datetime import datetime, timezone
from typing import Optional
from loguru import logger

from core.database import get_audit_logs_collection
from models.audit import AuditLogDocument


class AuditService:
    """
    Writes append-only audit log entries for every AI pipeline run.
    Audit logs are NEVER updated after creation.
    """

    async def log_pipeline_run(
        self,
        ticket_id: str,
        model_version: str,
        # Agent 1
        predicted_category: str,
        category_probabilities: dict,
        model_confidence: float,
        predicted_priority: str,
        priority_confidence: Optional[float],
        # Agent 2
        top_similarity_score: float,
        retrieved_ticket_ids: list,
        # Agent 3
        composite_confidence: float,
        confidence_breakdown: Optional[dict],
        routing_decision: str,
        sla_override: bool,
        security_override: bool,
        sla_breach_probability: float,
        # Sentiment
        sentiment_label: str,
        sentiment_score: float,
        # Agent 4
        generated_response_preview: Optional[str],
        hallucination_detected: bool,
        fallback_used: bool,
        generation_time_ms: Optional[int],
        # Explainability
        lime_top_features: Optional[list],
        # Duplicate detection
        duplicate_check_performed: bool,
        is_duplicate: bool,
        duplicate_of: Optional[str],
        # Performance
        processing_time_ms: Optional[int],
    ) -> bool:
        """
        Write an immutable audit log entry to MongoDB.

        Returns:
            True if written successfully.
        """
        try:
            audit_doc = AuditLogDocument(
                ticket_id=ticket_id,
                timestamp=datetime.now(timezone.utc),
                model_version=model_version,
                predicted_category=predicted_category,
                category_probabilities=category_probabilities,
                model_confidence=model_confidence,
                predicted_priority=predicted_priority,
                priority_confidence=priority_confidence,
                top_similarity_score=top_similarity_score,
                retrieved_ticket_ids=retrieved_ticket_ids,
                composite_confidence=composite_confidence,
                confidence_breakdown=confidence_breakdown,
                routing_decision=routing_decision,
                sla_override=sla_override,
                security_override=security_override,
                sla_breach_probability=sla_breach_probability,
                sentiment_label=sentiment_label,
                sentiment_score=sentiment_score,
                generated_response_preview=(
                    generated_response_preview[:200]
                    if generated_response_preview
                    else None
                ),
                hallucination_detected=hallucination_detected,
                fallback_used=fallback_used,
                generation_time_ms=generation_time_ms,
                lime_top_features=lime_top_features,
                duplicate_check_performed=duplicate_check_performed,
                is_duplicate=is_duplicate,
                duplicate_of=duplicate_of,
                processing_time_ms=processing_time_ms,
            )

            collection = get_audit_logs_collection()
            await collection.insert_one(audit_doc.model_dump())
            return True

        except Exception as e:
            logger.error(f"Failed to write audit log for {ticket_id}: {e}")
            return False

    async def update_agent_action(
        self,
        ticket_id: str,
        agent_action: str,
        final_outcome: str,
    ) -> bool:
        """
        Update the audit log with the agent's post-review action.
        This is the ONLY allowed mutation of an audit log.
        """
        try:
            collection = get_audit_logs_collection()
            # Motor's update_one doesn't support sort — find latest first
            latest = await collection.find_one(
                {"ticket_id": ticket_id},
                sort=[("timestamp", -1)],
            )
            if not latest:
                return False
            result = await collection.update_one(
                {"_id": latest["_id"]},
                {
                    "$set": {
                        "agent_action": agent_action,
                        "final_outcome": final_outcome,
                    }
                },
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update audit log for {ticket_id}: {e}")
            return False


# Module-level singleton
audit_service = AuditService()
