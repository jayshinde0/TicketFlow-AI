"""
routers/journey.py - Ticket journey tracking endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from routers.auth import get_current_user
from services.journey_service import journey_service
from core.database import get_db

router = APIRouter(prefix="/api/journey", tags=["Journey Tracking"])


@router.get("/ticket/{ticket_id}")
async def get_ticket_journey(
    ticket_id: str, current_user: dict = Depends(get_current_user)
):
    """
    Get the complete journey/timeline for a ticket.

    Shows all phases the ticket has gone through:
    - submitted
    - ai_processing
    - ai_resolved (if auto-resolved)
    - assigned_to_agent (if escalated)
    - in_progress
    - resolved
    - closed
    """
    journey = await journey_service.get_journey(ticket_id)

    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found for this ticket")

    # Get ticket details
    db = get_db()
    tickets_collection = db["tickets"]
    ticket = await tickets_collection.find_one({"ticket_id": ticket_id}, {"_id": 0})

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Check access permissions
    if current_user.get("role") == "user" and ticket.get("user_email") != current_user.get("email"):
        raise HTTPException(
            status_code=403, detail="You don't have access to this ticket"
        )

    # Get assigned agent details if available
    assigned_agent = None
    if journey.get("assigned_agent_email"):
        users_collection = db["users"]
        agent = await users_collection.find_one(
            {"email": journey["assigned_agent_email"]},
            {"_id": 0, "password_hash": 0}
        )
        if agent:
            assigned_agent = {
                "email": agent["email"],
                "full_name": agent["full_name"],
                "department": agent.get("department"),
                "specialization": agent.get("specialization"),
                "current_workload": agent.get("current_workload", 0),
                "max_concurrent_tickets": agent.get("max_concurrent_tickets", 10),
            }

    # Calculate total duration
    total_duration_ms = 0
    phases = []
    for step in journey.get("journey_steps", []):
        phase_data = {
            "phase": step["phase"],
            "entered_at": step["timestamp"],
            "duration_ms": step.get("duration_seconds", 0) * 1000 if step.get("duration_seconds") else None,
        }
        phases.append(phase_data)
        if step.get("duration_seconds"):
            total_duration_ms += step["duration_seconds"] * 1000

    return {
        "journey_id": f"JRN-{ticket_id}",
        "ticket_id": ticket_id,
        "current_phase": journey["current_phase"],
        "phases": phases,
        "assigned_agent": assigned_agent,
        "total_duration_ms": total_duration_ms,
        "created_at": journey["created_at"],
        "updated_at": journey["updated_at"],
    }


@router.get("/user/{user_id}")
async def get_user_journeys(
    user_id: str, current_user: dict = Depends(get_current_user)
):
    """
    Get all ticket journeys for a specific user.
    Users can only see their own journeys, admins/agents can see all.
    """
    # Check permissions
    if current_user.get("role") == "user" and current_user.get("user_id") != user_id:
        raise HTTPException(
            status_code=403, detail="You can only view your own ticket journeys"
        )

    db = get_db()
    tickets_collection = db["tickets"]
    journeys_collection = db["ticket_journeys"]
    users_collection = db["users"]

    # Get all tickets for this user
    tickets = await tickets_collection.find(
        {"user_id": user_id}
    ).to_list(length=1000)

    if not tickets:
        return {"user_id": user_id, "journeys": [], "total": 0}

    # Get journeys for all tickets
    ticket_ids = [t["ticket_id"] for t in tickets]
    journeys = await journeys_collection.find(
        {"ticket_id": {"$in": ticket_ids}}
    ).to_list(length=1000)

    # Build response with agent details
    result_journeys = []
    for journey in journeys:
        # Get assigned agent details if available
        assigned_agent = None
        if journey.get("assigned_agent_email"):
            agent = await users_collection.find_one(
                {"email": journey["assigned_agent_email"]},
                {"_id": 0, "password_hash": 0}
            )
            if agent:
                assigned_agent = {
                    "email": agent["email"],
                    "full_name": agent["full_name"],
                    "department": agent.get("department"),
                    "specialization": agent.get("specialization"),
                    "current_workload": agent.get("current_workload", 0),
                    "max_concurrent_tickets": agent.get("max_concurrent_tickets", 10),
                }

        # Calculate total duration
        total_duration_ms = 0
        phases = []
        for step in journey.get("journey_steps", []):
            phase_data = {
                "phase": step["phase"],
                "entered_at": step["timestamp"].isoformat() if hasattr(step["timestamp"], "isoformat") else step["timestamp"],
                "duration_ms": step.get("duration_seconds", 0) * 1000 if step.get("duration_seconds") else None,
            }
            phases.append(phase_data)
            if step.get("duration_seconds"):
                total_duration_ms += step["duration_seconds"] * 1000

        result_journeys.append({
            "journey_id": f"JRN-{journey['ticket_id']}",
            "ticket_id": journey["ticket_id"],
            "current_phase": journey["current_phase"],
            "phases": phases,
            "assigned_agent": assigned_agent,
            "total_duration_ms": total_duration_ms,
            "created_at": journey["created_at"].isoformat() if hasattr(journey["created_at"], "isoformat") else journey["created_at"],
            "updated_at": journey["updated_at"].isoformat() if hasattr(journey["updated_at"], "isoformat") else journey["updated_at"],
        })

    return {
        "user_id": user_id,
        "journeys": result_journeys,
        "total": len(result_journeys)
    }


@router.get("/{ticket_id}")
async def get_ticket_journey_legacy(
    ticket_id: str, current_user: dict = Depends(get_current_user)
):
    """Legacy endpoint - redirects to /ticket/{ticket_id}"""
    return await get_ticket_journey(ticket_id, current_user)


@router.post("/{ticket_id}/assign")
async def assign_ticket_to_agent(
    ticket_id: str,
    agent_email: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Assign a ticket to a specific agent.
    Only admins and agents can assign tickets.
    """
    if current_user.get("role") not in ["admin", "agent"]:
        raise HTTPException(
            status_code=403, detail="Only admins and agents can assign tickets"
        )

    # Get agent details
    db = get_db()
    users_collection = db["users"]
    agent = await users_collection.find_one({"email": agent_email, "role": "agent"})

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Assign ticket
    success = await journey_service.assign_to_agent(
        ticket_id=ticket_id,
        agent_email=agent["email"],
        agent_name=agent["full_name"],
        department=agent["department"],
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to assign ticket")

    return {
        "message": "Ticket assigned successfully",
        "ticket_id": ticket_id,
        "assigned_to": agent["full_name"],
        "department": agent["department"],
    }


@router.post("/{ticket_id}/start-work")
async def start_working_on_ticket(
    ticket_id: str, current_user: dict = Depends(get_current_user)
):
    """
    Mark that an agent has started working on the ticket.
    Only the assigned agent can start work.
    """
    if current_user.get("role") != "agent":
        raise HTTPException(status_code=403, detail="Only agents can start work")

    # Check if ticket is assigned to this agent
    db = get_db()
    tickets_collection = db["tickets"]
    ticket = await tickets_collection.find_one({"ticket_id": ticket_id})

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if ticket.get("assigned_agent_email") != current_user.get("email"):
        raise HTTPException(
            status_code=403, detail="This ticket is not assigned to you"
        )

    # Mark in progress
    success = await journey_service.mark_in_progress(
        ticket_id=ticket_id, notes=f"{current_user.get('full_name')} started working on this ticket"
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to update ticket status")

    return {"message": "Ticket marked as in progress", "ticket_id": ticket_id}


@router.get("/agent/{agent_email}/workload")
async def get_agent_workload(
    agent_email: str, current_user: dict = Depends(get_current_user)
):
    """Get current workload for an agent"""
    if current_user.get("role") not in ["admin", "agent"]:
        raise HTTPException(
            status_code=403, detail="Only admins and agents can view workload"
        )

    workload = await journey_service.get_agent_workload(agent_email)
    return workload


@router.get("/department/{department}/agents")
async def get_department_agents(
    department: str, current_user: dict = Depends(get_current_user)
):
    """Get all agents in a department with their workload"""
    if current_user.get("role") not in ["admin", "agent"]:
        raise HTTPException(
            status_code=403, detail="Only admins and agents can view agents"
        )

    db = get_db()
    users_collection = db["users"]

    # Get all agents in department
    agents = await users_collection.find(
        {"role": "agent", "department": department, "is_active": True}, {"_id": 0, "password_hash": 0}
    ).to_list(length=100)

    # Add workload info
    for agent in agents:
        workload = await journey_service.get_agent_workload(agent["email"])
        agent["current_workload"] = workload["current_workload"]

    return {"department": department, "agents": agents, "total_agents": len(agents)}
