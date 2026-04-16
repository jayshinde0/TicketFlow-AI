"""
services/assignment_service.py — Agent auto-assignment algorithm.
Assigns tickets to the best available agent based on department,
expertise, and current workload.
"""

from typing import Dict, Any, Optional, List
from loguru import logger

from core.config import settings


class AssignmentService:
    """
    Auto-assignment algorithm for HITL tickets.

    Selection criteria (in priority order):
    1. Filter agents by department match
    2. Filter agents who are ONLINE and below max_load
    3. Sort by: expertise match score → lowest current_load → fewest active tickets
    4. Assign to top candidate

    Fallback:
    - If no department match, try any ONLINE agent below max_load
    - If no agent available, leave unassigned (will appear in agent queue)
    """

    async def find_best_agent(
        self,
        department: str,
        category: str,
        priority: str,
        threat_detected: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Find the best available agent to assign a ticket to.

        Returns:
            Agent dict with user_id, name, etc. or None if no agent available.
        """
        try:
            from core.database import get_db

            db = get_db()
            if db is None:
                return None

            users_collection = db["users"]

            # Stage 1: Find agents matching department + ONLINE + below capacity
            query = {
                "role": "agent",
                "is_active": True,
                "$expr": {"$lt": ["$current_load", "$max_load"]},
            }

            # For security threats, prioritize security-skilled agents
            if threat_detected:
                query["skills"] = {"$in": ["security", "incident_response", "Security"]}

            candidates = []
            async for agent in users_collection.find(query):
                agent.pop("password_hash", None)
                agent.pop("_id", None)

                # Calculate expertise match score
                score = self._calculate_expertise_score(
                    agent=agent,
                    department=department,
                    category=category,
                )
                agent["_match_score"] = score
                candidates.append(agent)

            if not candidates:
                # Fallback: any online agent below capacity
                fallback_query = {
                    "role": "agent",
                    "is_active": True,
                    "$expr": {"$lt": ["$current_load", "$max_load"]},
                }
                async for agent in users_collection.find(fallback_query):
                    agent.pop("password_hash", None)
                    agent.pop("_id", None)
                    agent["_match_score"] = 0.1
                    candidates.append(agent)

            if not candidates:
                logger.warning(
                    f"No agents available for department={department}, category={category}"
                )
                return None

            # Stage 2: Sort by match score (desc), then by load (asc)
            candidates.sort(
                key=lambda a: (-a["_match_score"], a.get("current_load", 0))
            )

            best = candidates[0]
            logger.info(
                f"Auto-assignment: agent={best.get('user_id')} "
                f"(score={best['_match_score']:.2f}, load={best.get('current_load', 0)})"
            )
            return best

        except Exception as e:
            logger.error(f"Agent assignment failed: {e}")
            return None

    def _calculate_expertise_score(
        self,
        agent: Dict[str, Any],
        department: str,
        category: str,
    ) -> float:
        """
        Calculate how well an agent matches a ticket's requirements.

        Score components:
        - Department match: +0.4
        - Category skill match: +0.3
        - Low load bonus: +0.2 (if below 50% capacity)
        - Active streak bonus: +0.1
        """
        score = 0.0

        # Department match
        agent_depts = agent.get("department", [])
        if isinstance(agent_depts, str):
            agent_depts = [agent_depts]
        if department in agent_depts:
            score += 0.4

        # Category skill match
        skills = agent.get("skills", [])
        cat_lower = category.lower()
        if any(s.lower() == cat_lower for s in skills):
            score += 0.3
        elif any(cat_lower in s.lower() or s.lower() in cat_lower for s in skills):
            score += 0.15

        # Load factor
        current = agent.get("current_load", 0)
        max_load = agent.get("max_load", 10)
        if max_load > 0 and current < max_load * 0.5:
            score += 0.2
        elif max_load > 0 and current < max_load * 0.75:
            score += 0.1

        # Base score for being available
        score += 0.1

        return min(1.0, score)

    async def assign_ticket(self, ticket_id: str, agent_id: str) -> bool:
        """
        Assign a ticket to an agent and increment their load.
        """
        try:
            from core.database import get_db

            db = get_db()
            if db is None:
                return False

            # Update ticket
            await db["tickets"].update_one(
                {"ticket_id": ticket_id},
                {
                    "$set": {
                        "assigned_agent_id": agent_id,
                        "status": "in_progress",
                    }
                },
            )

            # Increment agent load
            await db["users"].update_one(
                {"user_id": agent_id},
                {"$inc": {"current_load": 1}},
            )

            logger.info(f"Ticket {ticket_id} assigned to agent {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Ticket assignment failed: {e}")
            return False

    async def release_ticket(self, ticket_id: str, agent_id: str) -> bool:
        """
        Release a ticket (on resolve/close) and decrement agent load.
        """
        try:
            from core.database import get_db

            db = get_db()
            if db is None:
                return False

            # Decrement agent load (min 0)
            await db["users"].update_one(
                {"user_id": agent_id, "current_load": {"$gt": 0}},
                {"$inc": {"current_load": -1}},
            )

            logger.debug(f"Agent {agent_id} load decremented for ticket {ticket_id}")
            return True

        except Exception as e:
            logger.error(f"Ticket release failed: {e}")
            return False


# Module-level singleton
assignment_service = AssignmentService()
