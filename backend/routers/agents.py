"""
routers/agents.py — Agent workload and queue management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger

from core.database import get_tickets_collection, get_users_collection
from core.security import get_current_user, require_role
from utils.helpers import paginate

router = APIRouter(prefix="/api/agents", tags=["Agents"])


@router.get("/queue")
async def get_agent_queue(
    current_user: dict = Depends(require_role("agent", "admin", "senior_engineer")),
):
    """Get tickets pending agent review (routing=SUGGEST or ESCALATE)."""
    collection = get_tickets_collection()

    cursor = collection.find({
        "status": "open",
        "ai_analysis.routing_decision": {
            "$in": ["SUGGEST_TO_AGENT", "ESCALATE_TO_HUMAN"]
        },
    }).sort("created_at", 1)  # oldest first

    docs = await cursor.to_list(length=100)
    for doc in docs:
        doc.pop("_id", None)

    return {
        "items": docs,
        "total": len(docs),
    }


@router.get("/workload")
async def get_agent_workload(
    current_user: dict = Depends(require_role("admin")),
):
    """Get all active agents with their current load stats."""
    users = get_users_collection()
    tickets = get_tickets_collection()

    agents_cursor = users.find({
        "role": {"$in": ["agent", "senior_engineer"]},
        "is_active": True,
    })
    agents = await agents_cursor.to_list(length=100)

    result = []
    for agent in agents:
        uid = agent["user_id"]
        open_count = await tickets.count_documents({
            "resolution.agent_id": uid,
            "status": "open",
        })
        resolved_count = await tickets.count_documents({
            "resolution.agent_id": uid,
            "status": "resolved",
        })
        result.append({
            "user_id": uid,
            "name": agent["name"],
            "skills": agent.get("skills", []),
            "open_tickets": open_count,
            "resolved_total": resolved_count,
            "max_load": agent.get("max_load", 10),
            "avg_resolution_time": agent.get("avg_resolution_time"),
            "approval_rate": agent.get("approval_rate"),
        })

    return {"agents": result, "total": len(result)}


@router.post("/{ticket_id}/assign")
async def assign_ticket(
    ticket_id: str,
    agent_id: str,
    current_user: dict = Depends(require_role("admin")),
):
    """Assign a ticket to a specific agent."""
    from utils.helpers import utcnow
    collection = get_tickets_collection()
    result = await collection.update_one(
        {"ticket_id": ticket_id},
        {
            "$set": {
                "resolution.agent_id": agent_id,
                "updated_at": utcnow(),
            }
        },
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return {"ticket_id": ticket_id, "assigned_to": agent_id}


@router.post("/{ticket_id}/auto-assign")
async def auto_assign_ticket(
    ticket_id: str,
    current_user: dict = Depends(require_role("admin")),
):
    """
    Auto-assign a ticket to the best available agent using the assignment algorithm.
    """
    from services.assignment_service import assignment_service

    collection = get_tickets_collection()
    ticket = await collection.find_one({"ticket_id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ai = ticket.get("ai_analysis", {})
    category = ai.get("category", "Software")
    department = ai.get("department", "SOFTWARE")
    priority = ai.get("priority", "Medium")
    threat = ai.get("threat_analysis", {})

    agent = await assignment_service.find_best_agent(
        department=department,
        category=category,
        priority=priority,
        threat_detected=threat.get("threat_detected", False),
    )

    if not agent:
        return {"ticket_id": ticket_id, "assigned": False, "reason": "No agents available"}

    await assignment_service.assign_ticket(ticket_id, agent["user_id"])
    return {
        "ticket_id": ticket_id,
        "assigned": True,
        "agent_id": agent["user_id"],
        "agent_name": agent.get("name", ""),
        "match_score": agent.get("_match_score", 0),
    }


@router.patch("/me/availability")
async def update_availability(
    status: str = Query(..., regex="^(ONLINE|BUSY|OFFLINE)$"),
    current_user: dict = Depends(require_role("agent", "admin")),
):
    """Update the current agent's availability status."""
    from core.database import get_db
    from utils.helpers import utcnow
    db = get_db()
    await db["users"].update_one(
        {"user_id": current_user["user_id"]},
        {"$set": {"availability_status": status, "updated_at": utcnow()}},
    )
    return {"user_id": current_user["user_id"], "availability_status": status}
