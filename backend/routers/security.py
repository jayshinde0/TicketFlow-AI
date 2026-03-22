"""
routers/security.py — Security threat management endpoints.
GET /api/security/threats — list all security threats
GET /api/security/stats — threat statistics
GET /api/security/playbook/{threat_type} — get response playbook
POST /api/security/{ticket_id}/acknowledge — acknowledge a threat
POST /api/security/{ticket_id}/incident-report — submit post-incident form
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field
from loguru import logger

from core.database import get_db
from core.security import get_current_user, require_role
from services.escalation_service import escalation_service

router = APIRouter(prefix="/api/security", tags=["Security"])


class IncidentReportBody(BaseModel):
    root_cause: str = Field(min_length=10, max_length=2000)
    affected_users_count: int = Field(ge=0)
    data_compromised: bool = False
    containment_actions: str = Field(min_length=10, max_length=2000)
    prevention_measures: str = Field(min_length=10, max_length=2000)
    notes: Optional[str] = Field(default=None, max_length=2000)


@router.get("/threats")
async def list_threats(
    status_filter: Optional[str] = Query(None, alias="status"),
    severity: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_role("admin", "agent")),
):
    """
    List all security threats/escalations.
    Filterable by status (pending/acknowledged/resolved) and severity.
    """
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    query = {}
    if status_filter == "pending":
        query["acknowledged"] = False
        query["resolved"] = False
    elif status_filter == "acknowledged":
        query["acknowledged"] = True
        query["resolved"] = False
    elif status_filter == "resolved":
        query["resolved"] = True

    if severity:
        query["severity"] = severity

    total = await db["escalation_logs"].count_documents(query)
    skip = (page - 1) * page_size

    cursor = db["escalation_logs"].find(query).sort("created_at", -1).skip(skip).limit(page_size)
    items = []
    async for doc in cursor:
        doc.pop("_id", None)
        items.append(doc)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/stats")
async def threat_stats(
    current_user: dict = Depends(require_role("admin", "agent")),
):
    """
    Get aggregated security threat statistics.
    """
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    total = await db["escalation_logs"].count_documents({})
    pending = await db["escalation_logs"].count_documents({"acknowledged": False, "resolved": False})
    acknowledged = await db["escalation_logs"].count_documents({"acknowledged": True, "resolved": False})
    resolved = await db["escalation_logs"].count_documents({"resolved": True})

    # Threat type breakdown
    pipeline = [
        {"$group": {"_id": "$threat_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    type_breakdown = {}
    async for doc in db["escalation_logs"].aggregate(pipeline):
        type_breakdown[doc["_id"]] = doc["count"]

    # Severity breakdown
    sev_pipeline = [
        {"$group": {"_id": "$severity", "count": {"$sum": 1}}},
    ]
    severity_breakdown = {}
    async for doc in db["escalation_logs"].aggregate(sev_pipeline):
        severity_breakdown[doc["_id"]] = doc["count"]

    # Current escalation levels
    level_pipeline = [
        {"$match": {"resolved": False}},
        {"$group": {"_id": "$current_level", "count": {"$sum": 1}}},
    ]
    level_breakdown = {}
    async for doc in db["escalation_logs"].aggregate(level_pipeline):
        level_breakdown[doc["_id"]] = doc["count"]

    return {
        "total": total,
        "pending": pending,
        "acknowledged": acknowledged,
        "resolved": resolved,
        "type_breakdown": type_breakdown,
        "severity_breakdown": severity_breakdown,
        "active_escalation_levels": level_breakdown,
    }


@router.get("/playbook/{threat_type}")
async def get_playbook(
    threat_type: str,
    current_user: dict = Depends(require_role("admin", "agent")),
):
    """Get the response playbook for a specific threat type."""
    playbook = escalation_service.get_playbook(threat_type)
    return {"threat_type": threat_type, "playbook": playbook}


@router.post("/{ticket_id}/acknowledge")
async def acknowledge_threat(
    ticket_id: str,
    current_user: dict = Depends(require_role("admin", "agent")),
):
    """Acknowledge a security threat escalation."""
    success = await escalation_service.acknowledge_escalation(
        ticket_id, current_user["user_id"]
    )
    if not success:
        raise HTTPException(
            status_code=404,
            detail="No active escalation found for this ticket",
        )
    return {"status": "acknowledged", "ticket_id": ticket_id}


@router.post("/{ticket_id}/incident-report")
async def submit_incident_report(
    ticket_id: str,
    body: IncidentReportBody,
    current_user: dict = Depends(require_role("admin", "agent")),
):
    """Submit a post-incident report for a security threat."""
    report = {
        "root_cause": body.root_cause,
        "affected_users_count": body.affected_users_count,
        "data_compromised": body.data_compromised,
        "containment_actions": body.containment_actions,
        "prevention_measures": body.prevention_measures,
        "notes": body.notes,
        "submitted_by": current_user["user_id"],
    }
    success = await escalation_service.submit_incident_report(ticket_id, report)
    if not success:
        raise HTTPException(
            status_code=500, detail="Failed to submit incident report"
        )
    return {"status": "submitted", "ticket_id": ticket_id}
