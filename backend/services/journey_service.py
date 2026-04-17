"""
services/journey_service.py - Ticket journey tracking service
"""
from datetime import datetime, timezone
from typing import Optional, List
from loguru import logger

from core.database import get_db


class JourneyService:
    """Service for tracking ticket journey and agent assignments"""

    async def create_journey(
        self, ticket_id: str, initial_phase: str = "submitted"
    ) -> dict:
        """Create initial journey for a new ticket"""
        db = get_db()
        journey_collection = db["ticket_journeys"]

        journey = {
            "ticket_id": ticket_id,
            "current_phase": initial_phase,
            "current_status": "open",
            "assigned_agent_email": None,
            "assigned_agent_name": None,
            "assigned_department": None,
            "journey_steps": [
                {
                    "step_id": "1",
                    "phase": "submitted",
                    "status": "completed",
                    "timestamp": datetime.now(timezone.utc),
                    "duration_seconds": 0,
                    "notes": "Ticket submitted by user",
                }
            ],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        await journey_collection.insert_one(journey)
        logger.info(f"Created journey for ticket {ticket_id}")
        return journey

    async def add_journey_step(
        self,
        ticket_id: str,
        phase: str,
        status: str = "current",
        assigned_agent_email: Optional[str] = None,
        assigned_agent_name: Optional[str] = None,
        department: Optional[str] = None,
        notes: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> bool:
        """Add a new step to the ticket journey"""
        db = get_db()
        journey_collection = db["ticket_journeys"]

        # Get current journey
        journey = await journey_collection.find_one({"ticket_id": ticket_id})
        if not journey:
            logger.warning(f"Journey not found for ticket {ticket_id}")
            return False

        # Calculate duration of previous step
        if journey["journey_steps"]:
            last_step = journey["journey_steps"][-1]
            if last_step["status"] == "current":
                # Mark previous step as completed
                duration = (
                    datetime.now(timezone.utc) - last_step["timestamp"]
                ).total_seconds()
                last_step["status"] = "completed"
                last_step["duration_seconds"] = int(duration)

        # Add new step
        new_step = {
            "step_id": str(len(journey["journey_steps"]) + 1),
            "phase": phase,
            "status": status,
            "timestamp": datetime.now(timezone.utc),
            "duration_seconds": None if status == "current" else 0,
            "assigned_agent": assigned_agent_email,
            "assigned_agent_name": assigned_agent_name,
            "department": department,
            "notes": notes,
            "metadata": metadata,
        }

        # Update journey
        update_data = {
            "current_phase": phase,
            "journey_steps": journey["journey_steps"] + [new_step],
            "updated_at": datetime.now(timezone.utc),
        }

        # Update agent assignment if provided
        if assigned_agent_email:
            update_data["assigned_agent_email"] = assigned_agent_email
            update_data["assigned_agent_name"] = assigned_agent_name
            update_data["assigned_department"] = department

        await journey_collection.update_one(
            {"ticket_id": ticket_id}, {"$set": update_data}
        )

        logger.info(f"Added journey step '{phase}' for ticket {ticket_id}")
        return True

    async def assign_to_agent(
        self, ticket_id: str, agent_email: str, agent_name: str, department: str
    ) -> bool:
        """Assign ticket to a specific agent"""
        success = await self.add_journey_step(
            ticket_id=ticket_id,
            phase="assigned_to_agent",
            status="current",
            assigned_agent_email=agent_email,
            assigned_agent_name=agent_name,
            department=department,
            notes=f"Ticket assigned to {agent_name} ({department})",
        )

        if success:
            # Update ticket status
            db = get_db()
            tickets_collection = db["tickets"]
            await tickets_collection.update_one(
                {"ticket_id": ticket_id},
                {
                    "$set": {
                        "assigned_agent_email": agent_email,
                        "assigned_agent_name": agent_name,
                        "assigned_department": department,
                        "status": "in_progress",
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )

            # Update journey status
            db = get_db()
            journey_collection = db["ticket_journeys"]
            await journey_collection.update_one(
                {"ticket_id": ticket_id}, {"$set": {"current_status": "in_progress"}}
            )

        return success

    async def mark_in_progress(self, ticket_id: str, notes: Optional[str] = None):
        """Mark ticket as in progress"""
        return await self.add_journey_step(
            ticket_id=ticket_id,
            phase="in_progress",
            status="current",
            notes=notes or "Agent started working on the ticket",
        )

    async def mark_resolved(
        self, ticket_id: str, resolution: str, resolved_by: Optional[str] = None
    ):
        """Mark ticket as resolved"""
        notes = f"Ticket resolved"
        if resolved_by:
            notes += f" by {resolved_by}"

        success = await self.add_journey_step(
            ticket_id=ticket_id,
            phase="resolved",
            status="completed",
            notes=notes,
            metadata={"resolution": resolution},
        )

        if success:
            # Update journey status
            db = get_db()
            journey_collection = db["ticket_journeys"]
            await journey_collection.update_one(
                {"ticket_id": ticket_id}, {"$set": {"current_status": "resolved"}}
            )

        return success

    async def get_journey(self, ticket_id: str) -> Optional[dict]:
        """Get complete journey for a ticket"""
        db = get_db()
        journey_collection = db["ticket_journeys"]

        journey = await journey_collection.find_one(
            {"ticket_id": ticket_id}, {"_id": 0}
        )

        if journey:
            # Convert datetime objects to ISO strings
            journey["created_at"] = journey["created_at"].isoformat()
            journey["updated_at"] = journey["updated_at"].isoformat()

            for step in journey["journey_steps"]:
                step["timestamp"] = step["timestamp"].isoformat()

        return journey

    async def get_agent_workload(self, agent_email: str) -> dict:
        """Get current workload for an agent"""
        db = get_db()
        tickets_collection = db["tickets"]

        # Count open and in-progress tickets
        open_count = await tickets_collection.count_documents(
            {"assigned_agent_email": agent_email, "status": {"$in": ["open", "in_progress"]}}
        )

        return {"agent_email": agent_email, "current_workload": open_count}

    async def find_available_agent(self, department: str) -> Optional[dict]:
        """Find an available agent in the specified department"""
        db = get_db()
        users_collection = db["users"]

        # Get all agents in the department
        agents = await users_collection.find(
            {"role": "agent", "department": department, "is_active": True}
        ).to_list(length=100)

        if not agents:
            logger.warning(f"No agents found for department {department}")
            return None

        # Find agent with lowest workload
        best_agent = None
        min_workload = float("inf")

        for agent in agents:
            workload_info = await self.get_agent_workload(agent["email"])
            current_workload = workload_info["current_workload"]

            if current_workload < min_workload:
                min_workload = current_workload
                best_agent = agent

        return best_agent


# Module-level singleton
journey_service = JourneyService()
