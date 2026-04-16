"""
routers/security.py — Security threat management endpoints.

Endpoints:
  POST /api/security/analyze-ticket       — run full AI security pipeline on a ticket
  POST /api/security/escalate-ticket      — manually escalate a ticket to security queue
  GET  /api/security/threats              — list all security threats (filterable)
  GET  /api/security/stats                — aggregated threat statistics
  GET  /api/security/playbook/{type}      — get response playbook
  POST /api/security/{ticket_id}/acknowledge     — acknowledge a threat
  POST /api/security/{ticket_id}/resolve         — mark threat resolved
  POST /api/security/{ticket_id}/incident-report — submit post-incident form
  GET  /api/security/{ticket_id}/logs     — get security logs for a ticket
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
from loguru import logger

from core.database import get_db, get_tickets_collection
from core.security import get_current_user, require_role
from core.websocket_manager import ws_manager
from services.escalation_service import escalation_service
from services.ai_pipeline import security_pipeline
from utils.helpers import utcnow

router = APIRouter(prefix="/api/security", tags=["Security"])


# ─── Request / Response models ────────────────────────────────────────


class AnalyzeTicketRequest(BaseModel):
    ticket_id: str
    subject: str = Field(min_length=1, max_length=500)
    description: str = Field(min_length=1, max_length=10000)
    ml_category: Optional[str] = "Software"
    ml_confidence: Optional[float] = Field(default=0.5, ge=0.0, le=1.0)


class EscalateTicketRequest(BaseModel):
    ticket_id: str
    reason: str = Field(min_length=5, max_length=1000)
    threat_type: Optional[str] = "unauthorized_access"
    severity: Optional[str] = "high"


class IncidentReportBody(BaseModel):
    root_cause: str = Field(min_length=10, max_length=2000)
    affected_users_count: int = Field(ge=0)
    data_compromised: bool = False
    containment_actions: str = Field(min_length=10, max_length=2000)
    prevention_measures: str = Field(min_length=10, max_length=2000)
    notes: Optional[str] = Field(default=None, max_length=2000)


# ─── Helper: broadcast security alert via WebSocket ──────────────────


async def _broadcast_security_alert(
    ticket_id: str, threat_level: str, threat_type: str, details: dict
):
    """Broadcast a real-time security alert to all connected admin/agent clients."""
    try:
        await ws_manager.broadcast_security_alert(
            {
                "ticket_id": ticket_id,
                "threat_level": threat_level,
                "threat_type": threat_type,
                **details,
            }
        )
    except Exception as e:
        logger.warning(f"Security WebSocket broadcast failed (non-fatal): {e}")


# ─── Helper: append to ticket security_logs ──────────────────────────


async def _append_security_log(ticket_id: str, action: str, actor: str, details: dict):
    """Append an entry to the ticket's security_logs array in MongoDB."""
    try:
        db = get_db()
        if db is None:
            return
        log_entry = {
            "action": action,
            "actor": actor,
            "timestamp": utcnow().isoformat(),
            **details,
        }
        await db["tickets"].update_one(
            {"ticket_id": ticket_id},
            {
                "$push": {"security_logs": log_entry},
                "$set": {"updated_at": utcnow()},
            },
        )
    except Exception as e:
        logger.warning(f"Failed to append security log: {e}")


# ─── POST /analyze-ticket ─────────────────────────────────────────────


@router.post("/analyze-ticket")
async def analyze_ticket(
    body: AnalyzeTicketRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_role("admin", "agent")),
):
    """
    Run the full AI security pipeline on a ticket and return classification + threat info.
    Stores results in MongoDB and triggers escalation if threat_level == attack.
    """
    result = await security_pipeline.run(
        ticket_id=body.ticket_id,
        subject=body.subject,
        description=body.description,
        ml_category=body.ml_category or "Software",
        ml_confidence=body.ml_confidence or 0.5,
    )

    threat_level = result["threat_level"]
    threat_type = result["threat_type"]
    confidence = result["confidence_score"]

    # ── Persist threat metadata to ticket document ────────────────────
    db = get_db()
    if db is not None:
        update_fields = {
            "ai_analysis.threat_level": threat_level,
            "ai_analysis.threat_type": threat_type,
            "ai_analysis.threat_confidence": confidence,
            "ai_analysis.triggered_rules": result["triggered_rules"],
            "ai_analysis.detection_reason": result["detection_reason"],
            "is_escalated": result["auto_escalate"],
            "updated_at": utcnow(),
        }
        if result["disable_auto_resolve"]:
            update_fields["ai_analysis.routing_decision"] = "ESCALATE_TO_HUMAN"
            update_fields["ai_analysis.priority"] = (
                "High" if threat_level == "suspicious" else "Critical"
            )

        await db["tickets"].update_one(
            {"ticket_id": body.ticket_id},
            {"$set": update_fields},
        )

    # ── Auto-escalate attacks ─────────────────────────────────────────
    if result["auto_escalate"]:
        threat_analysis_for_escalation = {
            "threat_detected": True,
            "threat_type": threat_type,
            "severity": "critical" if threat_level == "attack" else "high",
            "confidence": confidence,
            "recommended_action": result["detection_reason"],
            "indicators": result["triggered_rules"],
        }
        background_tasks.add_task(
            escalation_service.create_escalation,
            ticket_id=body.ticket_id,
            threat_analysis=threat_analysis_for_escalation,
        )

    # ── Log the analysis action ───────────────────────────────────────
    background_tasks.add_task(
        _append_security_log,
        ticket_id=body.ticket_id,
        action="security_analysis",
        actor=current_user["user_id"],
        details={
            "threat_level": threat_level,
            "threat_type": threat_type,
            "confidence": confidence,
            "triggered_rules": result["triggered_rules"],
        },
    )

    # ── Real-time broadcast for attacks/suspicious ────────────────────
    if threat_level in ("attack", "suspicious"):
        background_tasks.add_task(
            _broadcast_security_alert,
            ticket_id=body.ticket_id,
            threat_level=threat_level,
            threat_type=threat_type,
            details={
                "confidence": confidence,
                "detection_reason": result["detection_reason"],
                "triggered_rules": result["triggered_rules"],
            },
        )

    return {
        "ticket_id": body.ticket_id,
        "threat_level": threat_level,
        "threat_type": threat_type,
        "confidence_score": confidence,
        "detection_reason": result["detection_reason"],
        "triggered_rules": result["triggered_rules"],
        "auto_escalated": result["auto_escalate"],
        "disable_auto_resolve": result["disable_auto_resolve"],
        "safe_response": result.get("safe_response"),
        "stage_timings": result.get("stage_timings"),
    }


# ─── POST /escalate-ticket ────────────────────────────────────────────


@router.post("/escalate-ticket")
async def escalate_ticket(
    body: EscalateTicketRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_role("admin", "agent")),
):
    """
    Manually escalate a ticket to the security admin queue.
    Sets priority=HIGH, routing=ESCALATE_TO_HUMAN, disables auto-resolve.
    """
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    ticket = await db["tickets"].find_one({"ticket_id": body.ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    now = utcnow()

    # Update ticket
    await db["tickets"].update_one(
        {"ticket_id": body.ticket_id},
        {
            "$set": {
                "ai_analysis.routing_decision": "ESCALATE_TO_HUMAN",
                "ai_analysis.priority": "Critical",
                "ai_analysis.threat_level": "attack",
                "ai_analysis.threat_type": body.threat_type,
                "is_escalated": True,
                "updated_at": now,
            },
            "$push": {
                "security_logs": {
                    "action": "manual_escalation",
                    "actor": current_user["user_id"],
                    "reason": body.reason,
                    "timestamp": now.isoformat(),
                }
            },
        },
    )

    # Create escalation record
    threat_analysis = {
        "threat_detected": True,
        "threat_type": body.threat_type,
        "severity": body.severity,
        "confidence": 1.0,
        "recommended_action": body.reason,
        "indicators": ["manual_escalation"],
    }
    background_tasks.add_task(
        escalation_service.create_escalation,
        ticket_id=body.ticket_id,
        threat_analysis=threat_analysis,
    )

    # Broadcast
    background_tasks.add_task(
        _broadcast_security_alert,
        ticket_id=body.ticket_id,
        threat_level="attack",
        threat_type=body.threat_type,
        details={"reason": body.reason, "escalated_by": current_user["user_id"]},
    )

    return {
        "status": "escalated",
        "ticket_id": body.ticket_id,
        "escalated_by": current_user["user_id"],
        "threat_type": body.threat_type,
    }


# ─── GET /threats ─────────────────────────────────────────────────────


@router.get("/threats")
async def list_threats(
    status_filter: Optional[str] = Query(None, alias="status"),
    severity: Optional[str] = Query(None),
    threat_level: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_role("admin", "agent")),
):
    """
    List all security threats/escalations.
    Filterable by status (pending/acknowledged/resolved), severity, threat_level.
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

    cursor = (
        db["escalation_logs"]
        .find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(page_size)
    )
    items = []
    async for doc in cursor:
        doc.pop("_id", None)

        # Enrich with ticket threat metadata if available
        ticket = await db["tickets"].find_one(
            {"ticket_id": doc.get("ticket_id")},
            {
                "ai_analysis.threat_level": 1,
                "ai_analysis.threat_type": 1,
                "ai_analysis.threat_confidence": 1,
                "ai_analysis.triggered_rules": 1,
                "ai_analysis.detection_reason": 1,
                "subject": 1,
            },
        )
        if ticket:
            ai = ticket.get("ai_analysis") or {}
            doc["threat_level"] = ai.get("threat_level", "attack")
            doc["ai_confidence"] = ai.get("threat_confidence", doc.get("confidence", 0))
            doc["triggered_rules"] = ai.get("triggered_rules", [])
            doc["detection_reason"] = ai.get("detection_reason", "")
            doc["subject"] = ticket.get("subject", "")

        items.append(doc)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


# ─── GET /stats ───────────────────────────────────────────────────────


@router.get("/stats")
async def threat_stats(
    current_user: dict = Depends(require_role("admin", "agent")),
):
    """
    Get aggregated security threat statistics including threat_level breakdown.
    """
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    total = await db["escalation_logs"].count_documents({})
    pending = await db["escalation_logs"].count_documents(
        {"acknowledged": False, "resolved": False}
    )
    acknowledged = await db["escalation_logs"].count_documents(
        {"acknowledged": True, "resolved": False}
    )
    resolved = await db["escalation_logs"].count_documents({"resolved": True})

    # Threat type breakdown
    type_pipeline = [
        {"$group": {"_id": "$threat_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    type_breakdown = {}
    async for doc in db["escalation_logs"].aggregate(type_pipeline):
        type_breakdown[doc["_id"] or "unknown"] = doc["count"]

    # Severity breakdown
    sev_pipeline = [
        {"$group": {"_id": "$severity", "count": {"$sum": 1}}},
    ]
    severity_breakdown = {}
    async for doc in db["escalation_logs"].aggregate(sev_pipeline):
        severity_breakdown[doc["_id"] or "unknown"] = doc["count"]

    # Active escalation levels
    level_pipeline = [
        {"$match": {"resolved": False}},
        {"$group": {"_id": "$current_level", "count": {"$sum": 1}}},
    ]
    level_breakdown = {}
    async for doc in db["escalation_logs"].aggregate(level_pipeline):
        level_breakdown[doc["_id"] or "L1"] = doc["count"]

    # Threat level breakdown from tickets collection
    threat_level_pipeline = [
        {"$match": {"ai_analysis.threat_level": {"$exists": True}}},
        {"$group": {"_id": "$ai_analysis.threat_level", "count": {"$sum": 1}}},
    ]
    threat_level_breakdown = {"normal": 0, "suspicious": 0, "attack": 0}
    async for doc in db["tickets"].aggregate(threat_level_pipeline):
        key = doc["_id"] or "normal"
        threat_level_breakdown[key] = doc["count"]

    # Counts for the stat cards
    suspicious_count = threat_level_breakdown.get("suspicious", 0)
    attack_count = threat_level_breakdown.get("attack", 0)

    return {
        "total": total,
        "pending": pending,
        "acknowledged": acknowledged,
        "resolved": resolved,
        # New fields for enhanced UI
        "total_threats": suspicious_count + attack_count,
        "suspicious_count": suspicious_count,
        "attack_count": attack_count,
        "resolved_count": resolved,
        "type_breakdown": type_breakdown,
        "severity_breakdown": severity_breakdown,
        "active_escalation_levels": level_breakdown,
        "threat_level_breakdown": threat_level_breakdown,
    }


# ─── GET /playbook/{threat_type} ──────────────────────────────────────


@router.get("/playbook/{threat_type}")
async def get_playbook(
    threat_type: str,
    current_user: dict = Depends(require_role("admin", "agent")),
):
    """Get the response playbook for a specific threat type."""
    playbook = escalation_service.get_playbook(threat_type)
    return {"threat_type": threat_type, "playbook": playbook}


# ─── POST /{ticket_id}/acknowledge ───────────────────────────────────


@router.post("/{ticket_id}/acknowledge")
async def acknowledge_threat(
    ticket_id: str,
    background_tasks: BackgroundTasks,
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

    background_tasks.add_task(
        _append_security_log,
        ticket_id=ticket_id,
        action="acknowledged",
        actor=current_user["user_id"],
        details={},
    )

    return {"status": "acknowledged", "ticket_id": ticket_id}


# ─── POST /{ticket_id}/resolve ────────────────────────────────────────


@router.post("/{ticket_id}/resolve")
async def resolve_threat(
    ticket_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_role("admin", "agent")),
):
    """Mark a security threat as resolved."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    now = utcnow()
    result = await db["escalation_logs"].update_one(
        {"ticket_id": ticket_id, "resolved": False},
        {"$set": {"resolved": True, "resolved_at": now.isoformat()}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="No active escalation found")

    # Update ticket status
    await db["tickets"].update_one(
        {"ticket_id": ticket_id},
        {"$set": {"status": "resolved", "updated_at": now}},
    )

    background_tasks.add_task(
        _append_security_log,
        ticket_id=ticket_id,
        action="resolved",
        actor=current_user["user_id"],
        details={},
    )

    return {"status": "resolved", "ticket_id": ticket_id}


# ─── GET /{ticket_id}/logs ────────────────────────────────────────────


@router.get("/{ticket_id}/logs")
async def get_security_logs(
    ticket_id: str,
    current_user: dict = Depends(require_role("admin", "agent")),
):
    """Get the security action log for a specific ticket."""
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    ticket = await db["tickets"].find_one(
        {"ticket_id": ticket_id},
        {
            "security_logs": 1,
            "ai_analysis.threat_level": 1,
            "ai_analysis.threat_type": 1,
            "ai_analysis.triggered_rules": 1,
            "ai_analysis.detection_reason": 1,
        },
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ai = ticket.get("ai_analysis") or {}
    return {
        "ticket_id": ticket_id,
        "threat_level": ai.get("threat_level", "normal"),
        "threat_type": ai.get("threat_type", "none"),
        "triggered_rules": ai.get("triggered_rules", []),
        "detection_reason": ai.get("detection_reason", ""),
        "security_logs": ticket.get("security_logs", []),
    }


# ─── POST /{ticket_id}/incident-report ───────────────────────────────


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
        raise HTTPException(status_code=500, detail="Failed to submit incident report")
    return {"status": "submitted", "ticket_id": ticket_id}
