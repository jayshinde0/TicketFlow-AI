"""
models/feedback.py — Pydantic models for agent feedback on AI decisions.
Feedback is used by the Learning Agent (Agent 5) to retrain models.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class FeedbackAction(str, Enum):
    APPROVED = "approved"
    EDITED = "edited"
    REJECTED = "rejected"
    ESCALATED = "escalated"


# ─── Request schemas ──────────────────────────────────────────────────


class FeedbackApprove(BaseModel):
    """Agent approves AI suggestion as-is."""

    note: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional explanation for the learning agent",
    )


class FeedbackEdit(BaseModel):
    """Agent edits the AI response and/or corrections to category/priority."""

    corrected_response: str = Field(
        min_length=10,
        max_length=2000,
        description="The corrected final response sent to the user",
    )
    corrected_category: Optional[str] = Field(
        default=None, description="If the category was wrong, provide the correct one"
    )
    corrected_priority: Optional[str] = Field(
        default=None, description="If the priority was wrong, provide the correct one"
    )
    note: Optional[str] = Field(default=None, max_length=500)


class FeedbackReject(BaseModel):
    """Agent rejects AI response and writes a manual resolution."""

    manual_response: str = Field(
        min_length=10, max_length=2000, description="The manually crafted response"
    )
    corrected_category: Optional[str] = None
    corrected_priority: Optional[str] = None
    rejection_reason: Optional[str] = Field(
        default=None, max_length=500, description="Why the AI suggestion was rejected"
    )


class FeedbackEscalate(BaseModel):
    """Agent escalates to a senior engineer."""

    escalation_reason: str = Field(min_length=10, max_length=500)
    senior_engineer_id: Optional[str] = None


# ─── Database document ────────────────────────────────────────────────


class FeedbackDocument(BaseModel):
    """Full feedback document stored in MongoDB feedback collection."""

    ticket_id: str
    agent_id: str
    timestamp: datetime

    # What the AI predicted
    original_category: str
    original_priority: str
    original_response: Optional[str] = None

    # What the agent corrected it to (null if approved as-is)
    corrected_category: Optional[str] = None
    corrected_priority: Optional[str] = None
    corrected_response: Optional[str] = None

    action: FeedbackAction
    correction_note: Optional[str] = None
    used_for_retraining: bool = False  # flipped to True after retrain

    class Config:
        use_enum_values = True


# ─── Response schemas ─────────────────────────────────────────────────


class FeedbackResponse(BaseModel):
    """Response after feedback submission."""

    success: bool
    message: str
    ticket_id: str
    action: str


class FeedbackStats(BaseModel):
    """GET /api/feedback/stats — aggregate feedback metrics."""

    total_feedback: int
    approved_count: int
    edited_count: int
    rejected_count: int
    escalated_count: int
    approval_rate: float  # approved / total
    edit_rate: float  # edited / total
    rejection_rate: float  # rejected / total
    pending_retraining: int  # feedback not yet used for retraining
    category_correction_rate: float  # % where category was wrong
    priority_correction_rate: float  # % where priority was wrong
