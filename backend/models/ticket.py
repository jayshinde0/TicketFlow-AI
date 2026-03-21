"""
models/ticket.py — Pydantic models for ticket creation, storage, and API responses.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ─── Enums ────────────────────────────────────────────────────────────

class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    DUPLICATE = "duplicate"


class TicketPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class TicketCategory(str, Enum):
    NETWORK = "Network"
    AUTH = "Auth"
    SOFTWARE = "Software"
    HARDWARE = "Hardware"
    ACCESS = "Access"
    BILLING = "Billing"
    EMAIL = "Email"
    SECURITY = "Security"
    SERVICE_REQUEST = "ServiceRequest"
    DATABASE = "Database"


class RoutingDecision(str, Enum):
    AUTO_RESOLVE = "AUTO_RESOLVE"
    SUGGEST_TO_AGENT = "SUGGEST_TO_AGENT"
    ESCALATE_TO_HUMAN = "ESCALATE_TO_HUMAN"


class SentimentLabel(str, Enum):
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"


class AgentAction(str, Enum):
    APPROVED = "approved"
    EDITED = "edited"
    REJECTED = "rejected"
    ESCALATED = "escalated"


# ─── Nested schemas (used inside TicketDocument) ──────────────────────

class ConfidenceBreakdown(BaseModel):
    """Detailed decomposition of the composite confidence score."""
    model_prob_component: float = Field(ge=0.0, le=1.0)
    similarity_component: float = Field(ge=0.0, le=1.0)
    keyword_component: float = Field(ge=0.0, le=1.0)


class SimilarTicket(BaseModel):
    """A past resolved ticket retrieved from ChromaDB."""
    ticket_id: str
    summary: str
    solution: str
    similarity_score: float = Field(ge=0.0, le=1.0)
    resolution_time_hours: Optional[float] = None
    category: str


class LIMEFeature(BaseModel):
    """A single word and its importance weight from LIME."""
    word: str
    weight: float  # positive = supports, negative = opposes


class LIMEExplanation(BaseModel):
    """Full LIME explanation for a ticket classification."""
    predicted_class: str
    explanation_confidence: float
    top_positive_features: List[LIMEFeature]
    top_negative_features: List[LIMEFeature]


class AIAnalysis(BaseModel):
    """Complete output of the AI pipeline for a ticket."""
    # Classification agent output
    category: str
    category_probabilities: Dict[str, float] = {}
    model_confidence: float = Field(ge=0.0, le=1.0)

    # Priority
    priority: TicketPriority
    priority_confidence: Optional[float] = None

    # Sentiment agent
    sentiment_label: SentimentLabel = SentimentLabel.NEUTRAL
    sentiment_score: float = Field(default=0.0, ge=0.0, le=1.0)
    is_frustrated: bool = False

    # Decision agent
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_breakdown: Optional[ConfidenceBreakdown] = None
    routing_decision: RoutingDecision

    # Override flags
    sla_override: bool = False
    security_override: bool = False
    sla_breach_probability: float = Field(default=0.0, ge=0.0, le=1.0)
    estimated_resolution_hours: Optional[float] = None

    # Duplicate detection
    duplicate_of: Optional[str] = None  # parent ticket_id
    is_possible_duplicate: bool = False
    possible_duplicate_id: Optional[str] = None

    # Retriever agent output
    similar_tickets: List[SimilarTicket] = []
    top_similarity_score: float = 0.0

    # Response agent output
    generated_response: Optional[str] = None
    hallucination_detected: bool = False
    fallback_used: bool = False
    model_used: Optional[str] = None
    generation_time_ms: Optional[int] = None

    # Explainability
    lime_explanation: Optional[LIMEExplanation] = None

    # Processing metadata
    processing_time_ms: Optional[int] = None
    model_version: Optional[str] = None


class ResolutionData(BaseModel):
    """Data filled in when a ticket is resolved."""
    agent_id: Optional[str] = None
    action: Optional[AgentAction] = None
    final_response: Optional[str] = None
    resolution_time_hours: Optional[float] = None
    sla_breached: bool = False
    resolved_at: Optional[datetime] = None
    notes: Optional[str] = None


class TicketMetadata(BaseModel):
    """Derived metadata used for ML features."""
    user_tier: str = "Standard"   # Free / Standard / Premium / Enterprise
    submission_hour: int = 0       # 0-23
    submission_day: int = 0        # 0=Monday, 6=Sunday
    word_count: int = 0
    urgency_keyword_count: int = 0
    question_mark_count: int = 0
    exclamation_count: int = 0
    all_caps_word_count: int = 0
    duplicate_count: int = 0       # how many dupes linked to this ticket
    root_cause_group_id: Optional[str] = None


# ─── Request schemas ──────────────────────────────────────────────────

class TicketCreate(BaseModel):
    """Body of POST /api/tickets/ from the user."""
    subject: str = Field(
        min_length=5, max_length=200,
        description="Brief subject line for the ticket"
    )
    description: str = Field(
        min_length=20, max_length=5000,
        description="Detailed description of the issue (min 20 chars)"
    )
    # Optional — AI will predict if not given
    category: Optional[TicketCategory] = None
    # Optional attachment (base64 encoded image or plain text)
    attachment_text: Optional[str] = Field(default=None, max_length=10000)

    @field_validator("subject")
    @classmethod
    def subject_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Subject cannot be blank")
        return v.strip()

    @field_validator("description")
    @classmethod
    def description_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Description cannot be blank")
        return v.strip()


class TicketStatusUpdate(BaseModel):
    """Body of PATCH /api/tickets/{id}/status."""
    status: TicketStatus
    notes: Optional[str] = None


# ─── Database document schema ─────────────────────────────────────────

class TicketDocument(BaseModel):
    """
    Full ticket document as stored in MongoDB.
    The _id field is excluded since Motor handles it.
    """
    ticket_id: str                      # TKT-XXXX
    user_id: str
    subject: str
    description: str
    cleaned_text: Optional[str] = None  # spaCy-preprocessed version
    attachment_text: Optional[str] = None
    language: str = "en"

    created_at: datetime
    updated_at: datetime
    status: TicketStatus = TicketStatus.OPEN

    ai_analysis: Optional[AIAnalysis] = None
    resolution: Optional[ResolutionData] = None
    metadata: Optional[TicketMetadata] = None

    class Config:
        use_enum_values = True
        populate_by_name = True


# ─── Response schemas ─────────────────────────────────────────────────

class TicketResponse(BaseModel):
    """API response for a single ticket with full AI analysis."""
    ticket_id: str
    subject: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime
    ai_analysis: Optional[AIAnalysis] = None
    resolution: Optional[ResolutionData] = None
    metadata: Optional[TicketMetadata] = None


class TicketListItem(BaseModel):
    """Condensed ticket for list views (agent queue, tracking)."""
    ticket_id: str
    subject: str
    status: str
    created_at: datetime

    # AI highlights only (not full analysis)
    category: Optional[str] = None
    priority: Optional[str] = None
    confidence_score: Optional[float] = None
    routing_decision: Optional[str] = None
    sentiment_label: Optional[str] = None
    sla_breach_probability: Optional[float] = None
    is_frustrated: Optional[bool] = None


class TicketSubmitResponse(BaseModel):
    """Response immediately after ticket submission with AI result."""
    ticket_id: str
    message: str
    status: str
    ai_analysis: Optional[AIAnalysis] = None
    estimated_resolution_hours: Optional[float] = None


class TicketListResponse(BaseModel):
    """Paginated list of tickets."""
    tickets: List[TicketListItem]
    total: int
    page: int
    page_size: int
    total_pages: int
