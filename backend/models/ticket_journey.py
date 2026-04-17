"""
models/ticket_journey.py - Ticket journey tracking model
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class JourneyStep(BaseModel):
    """Single step in the ticket journey"""

    step_id: str
    phase: str  # "submitted", "ai_processing", "ai_resolved", "assigned_to_agent", "in_progress", "resolved", "closed"
    status: str  # "completed", "current", "pending"
    timestamp: datetime
    duration_seconds: Optional[int] = None
    assigned_agent: Optional[str] = None  # Agent email
    assigned_agent_name: Optional[str] = None
    department: Optional[str] = None
    notes: Optional[str] = None
    metadata: Optional[dict] = None


class TicketJourney(BaseModel):
    """Complete ticket journey tracking"""

    ticket_id: str
    current_phase: str
    current_status: str  # "open", "in_progress", "resolved", "closed"
    assigned_agent_email: Optional[str] = None
    assigned_agent_name: Optional[str] = None
    assigned_department: Optional[str] = None
    journey_steps: List[JourneyStep] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "ticket_id": "TKT-ABC123",
                "current_phase": "assigned_to_agent",
                "current_status": "in_progress",
                "assigned_agent_email": "john.network@ticketflow.ai",
                "assigned_agent_name": "John Network",
                "assigned_department": "NETWORK",
                "journey_steps": [
                    {
                        "step_id": "1",
                        "phase": "submitted",
                        "status": "completed",
                        "timestamp": "2024-01-01T10:00:00Z",
                        "duration_seconds": 5,
                    },
                    {
                        "step_id": "2",
                        "phase": "ai_processing",
                        "status": "completed",
                        "timestamp": "2024-01-01T10:00:05Z",
                        "duration_seconds": 15,
                    },
                    {
                        "step_id": "3",
                        "phase": "assigned_to_agent",
                        "status": "current",
                        "timestamp": "2024-01-01T10:00:20Z",
                        "assigned_agent": "john.network@ticketflow.ai",
                        "assigned_agent_name": "John Network",
                        "department": "NETWORK",
                    },
                ],
            }
        }
