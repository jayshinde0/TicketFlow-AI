"""
routers/simulation.py — Simulation mode endpoints.
POST /api/simulation/start — start ticket generation simulation
POST /api/simulation/stop — stop simulation
GET /api/simulation/status — current simulation state and stats
"""

import asyncio
import random
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from loguru import logger

from core.security import require_role

router = APIRouter(prefix="/api/simulation", tags=["Simulation"])

# Module-level simulation state
_simulation_state = {
    "running": False,
    "task": None,
    "tickets_generated": 0,
    "start_time": None,
    "speed_multiplier": 1.0,
    "stats": {
        "auto_resolved": 0,
        "suggested_to_agent": 0,
        "escalated_to_human": 0,
        "avg_confidence": 0.0,
        "total_processing_ms": 0,
    },
}

# Sample ticket data for simulation
SAMPLE_SUBJECTS = [
    "VPN connection keeps dropping", "Cannot access shared drive",
    "Email not syncing on mobile", "Password reset not working",
    "Laptop running extremely slow", "Software license expired",
    "Suspicious email received", "New employee onboarding request",
    "Database backup failed", "Printer not connecting to network",
    "Two-factor auth not sending codes", "Application crashes on startup",
    "Network outage in Building 3", "Invoice discrepancy reported",
    "Unauthorized login attempt detected", "Cannot connect to WiFi",
    "Server disk space running low", "Antivirus scan found threats",
    "Request for new software installation", "Monitor flickering issues",
]

SAMPLE_DESCRIPTIONS = [
    "I've been experiencing this issue since yesterday morning. I've tried restarting but it didn't help. This is affecting my ability to work and I need it resolved urgently.",
    "Multiple users in our department are reporting the same issue. This seems to be a widespread problem that started after the recent system update.",
    "I noticed something unusual in my account activity. There are login attempts from locations I've never visited. I'm concerned about a potential security breach.",
    "The system shows an error message every time I try to perform this action. I've attached a screenshot. This is blocking a critical project deadline.",
    "This has been ongoing for about a week now and getting worse. Performance has degraded significantly and it's impacting our entire team's productivity.",
]


class SimulationConfig(BaseModel):
    speed_multiplier: float = Field(default=1.0, ge=0.1, le=10.0)
    max_tickets: int = Field(default=50, ge=1, le=500)


@router.post("/start")
async def start_simulation(
    config: SimulationConfig,
    current_user: dict = Depends(require_role("admin")),
):
    """Start a ticket generation simulation."""
    if _simulation_state["running"]:
        return {"status": "already_running", "tickets_generated": _simulation_state["tickets_generated"]}

    _simulation_state["running"] = True
    _simulation_state["tickets_generated"] = 0
    _simulation_state["start_time"] = datetime.now(timezone.utc).isoformat()
    _simulation_state["speed_multiplier"] = config.speed_multiplier
    _simulation_state["stats"] = {
        "auto_resolved": 0, "suggested_to_agent": 0,
        "escalated_to_human": 0, "avg_confidence": 0.0,
        "total_processing_ms": 0,
    }

    async def run_simulation():
        try:
            for i in range(config.max_tickets):
                if not _simulation_state["running"]:
                    break

                # Generate a simulated ticket
                subject = random.choice(SAMPLE_SUBJECTS)
                description = random.choice(SAMPLE_DESCRIPTIONS)

                try:
                    from routers.tickets import run_ai_pipeline
                    from utils.helpers import generate_ticket_id, utcnow
                    from core.database import get_tickets_collection

                    ticket_id = generate_ticket_id()
                    now = utcnow()

                    ai_result = await run_ai_pipeline(
                        ticket_id=ticket_id,
                        subject=subject,
                        description=description,
                        user_tier=random.choice(["Free", "Standard", "Premium", "Enterprise"]),
                        now=now,
                    )

                    # Update stats
                    _simulation_state["tickets_generated"] += 1
                    routing = ai_result.get("routing_decision", "")
                    if routing == "AUTO_RESOLVE":
                        _simulation_state["stats"]["auto_resolved"] += 1
                    elif routing == "SUGGEST_TO_AGENT":
                        _simulation_state["stats"]["suggested_to_agent"] += 1
                    else:
                        _simulation_state["stats"]["escalated_to_human"] += 1

                    total = _simulation_state["tickets_generated"]
                    prev_avg = _simulation_state["stats"]["avg_confidence"]
                    new_conf = ai_result.get("confidence_score", 0)
                    _simulation_state["stats"]["avg_confidence"] = (
                        (prev_avg * (total - 1) + new_conf) / total
                    )
                    _simulation_state["stats"]["total_processing_ms"] += (
                        ai_result.get("processing_time_ms", 0)
                    )

                    # Store the simulated ticket
                    ticket_doc = {
                        "ticket_id": ticket_id,
                        "subject": subject,
                        "description": description,
                        "status": "resolved" if routing == "AUTO_RESOLVE" else "open",
                        "ai_analysis": ai_result,
                        "created_at": now.isoformat(),
                        "updated_at": now.isoformat(),
                        "user_id": "simulation",
                        "is_simulation": True,
                    }
                    collection = get_tickets_collection()
                    await collection.insert_one(ticket_doc)

                except Exception as e:
                    logger.warning(f"Simulation ticket {i+1} failed: {e}")

                # Wait between tickets (adjusted by speed multiplier)
                delay = 2.0 / config.speed_multiplier
                await asyncio.sleep(delay)

        except Exception as e:
            logger.error(f"Simulation error: {e}")
        finally:
            _simulation_state["running"] = False
            logger.info(f"Simulation ended: {_simulation_state['tickets_generated']} tickets generated")

    # Run simulation in background
    asyncio.create_task(run_simulation())

    return {
        "status": "started",
        "speed_multiplier": config.speed_multiplier,
        "max_tickets": config.max_tickets,
    }


@router.post("/stop")
async def stop_simulation(
    current_user: dict = Depends(require_role("admin")),
):
    """Stop the running simulation."""
    _simulation_state["running"] = False
    return {
        "status": "stopped",
        "tickets_generated": _simulation_state["tickets_generated"],
        "stats": _simulation_state["stats"],
    }


@router.get("/status")
async def simulation_status(
    current_user: dict = Depends(require_role("admin")),
):
    """Get current simulation state and statistics."""
    total = _simulation_state["tickets_generated"]
    stats = _simulation_state["stats"]

    return {
        "running": _simulation_state["running"],
        "tickets_generated": total,
        "start_time": _simulation_state["start_time"],
        "speed_multiplier": _simulation_state["speed_multiplier"],
        "stats": {
            **stats,
            "avg_confidence": round(stats["avg_confidence"], 3),
            "avg_processing_ms": (
                int(stats["total_processing_ms"] / total) if total > 0 else 0
            ),
        },
    }
