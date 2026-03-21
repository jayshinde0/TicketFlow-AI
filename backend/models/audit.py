"""
models/audit.py — Pydantic models for immutable AI audit trail.
Every ticket processed by the AI pipeline gets a full audit log entry.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


# ─── Database document ────────────────────────────────────────────────

class AuditLogDocument(BaseModel):
    """
    Immutable record of a single AI pipeline run for a ticket.
    Written once; never updated (append-only audit trail).
    """
    ticket_id: str
    timestamp: datetime

    # Model version used for this classification
    model_version: str

    # ── Agent 1 (Classifier) output ───────────────────────────────────
    predicted_category: str
    category_probabilities: Dict[str, float] = {}
    model_confidence: float
    predicted_priority: str
    priority_confidence: Optional[float] = None

    # ── Agent 2 (Retriever) output ─────────────────────────────────────
    top_similarity_score: float = 0.0
    retrieved_ticket_ids: List[str] = []

    # ── Agent 3 (Decision) output ──────────────────────────────────────
    composite_confidence: float
    confidence_breakdown: Optional[Dict[str, float]] = None
    routing_decision: str
    sla_override: bool = False
    security_override: bool = False
    sla_breach_probability: float = 0.0

    # ── Sentiment ─────────────────────────────────────────────────────
    sentiment_label: str
    sentiment_score: float

    # ── Agent 4 (Response / LLM) output ──────────────────────────────
    generated_response_preview: Optional[str] = None   # first 200 chars
    hallucination_detected: bool = False
    fallback_used: bool = False
    generation_time_ms: Optional[int] = None

    # ── Validation ────────────────────────────────────────────────────
    response_validation_passed: bool = True
    validation_details: Optional[str] = None

    # ── Explainability ────────────────────────────────────────────────
    lime_top_features: Optional[List[Dict]] = None

    # ── Duplicate detection ───────────────────────────────────────────
    duplicate_check_performed: bool = False
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None

    # ── Agent action (set after agent review) ─────────────────────────
    agent_action: Optional[str] = None
    final_outcome: Optional[str] = None  # e.g. "resolved via AI response"

    # ── Processing performance ───────────────────────────────────────
    processing_time_ms: Optional[int] = None   # total pipeline time

    class Config:
        populate_by_name = True


# ─── Request schemas ──────────────────────────────────────────────────

class AuditLogFilter(BaseModel):
    """Query parameters for GET /api/admin/audit-logs."""
    ticket_id: Optional[str] = None
    routing_decision: Optional[str] = None
    model_version: Optional[str] = None
    hallucination_detected: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)


# ─── Response schemas ─────────────────────────────────────────────────

class AuditLogResponse(BaseModel):
    """Single audit log entry in API response."""
    ticket_id: str
    timestamp: datetime
    model_version: str
    predicted_category: str
    model_confidence: float
    routing_decision: str
    sla_breach_probability: float
    sentiment_label: str
    hallucination_detected: bool
    agent_action: Optional[str]
    final_outcome: Optional[str]
    processing_time_ms: Optional[int]


class AuditLogListResponse(BaseModel):
    """Paginated audit log response."""
    logs: List[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
