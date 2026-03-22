"""
services/time_sensitivity_service.py — Time sensitivity classification.
Assigns IMMEDIATE / SAME_DAY / STANDARD labels to tickets.
"""

from loguru import logger


class TimeSensitivityService:
    """
    Classifies ticket time sensitivity based on category, priority,
    and urgency keyword density.

    Rules (in order of precedence):
    1. CRITICAL priority + Security category      → IMMEDIATE
    2. CRITICAL priority (any category)            → IMMEDIATE
    3. HIGH priority + technical categories         → SAME_DAY
    4. HIGH priority + SLA breach probability >0.7  → SAME_DAY
    5. LOW priority + ServiceRequest category       → STANDARD
    6. All others                                   → SAME_DAY (default)
    """

    IMMEDIATE_CATEGORIES = {"Security"}
    TECHNICAL_CATEGORIES = {"Network", "Database", "Software", "Auth", "Hardware"}
    LOW_URGENCY_CATEGORIES = {"ServiceRequest", "Email"}

    URGENCY_KEYWORDS = {
        "urgent", "asap", "immediately", "critical", "emergency",
        "production down", "system down", "outage", "data loss",
        "ransomware", "breach", "hacked", "all users", "whole team",
        "cannot work", "completely down",
    }

    def classify(
        self,
        category: str,
        priority: str,
        text: str = "",
        sla_breach_probability: float = 0.0,
    ) -> str:
        """
        Determine time sensitivity label.

        Returns:
            One of: "IMMEDIATE", "SAME_DAY", "STANDARD"
        """
        text_lower = text.lower() if text else ""
        urgency_count = sum(1 for kw in self.URGENCY_KEYWORDS if kw in text_lower)

        # Rule 1: Critical + Security → IMMEDIATE
        if priority == "Critical" and category in self.IMMEDIATE_CATEGORIES:
            logger.debug(f"Time sensitivity: IMMEDIATE (Critical + {category})")
            return "IMMEDIATE"

        # Rule 2: Critical priority → IMMEDIATE
        if priority == "Critical":
            logger.debug("Time sensitivity: IMMEDIATE (Critical priority)")
            return "IMMEDIATE"

        # Rule 3: High urgency keyword density → IMMEDIATE
        if urgency_count >= 3:
            logger.debug(f"Time sensitivity: IMMEDIATE ({urgency_count} urgency keywords)")
            return "IMMEDIATE"

        # Rule 4: High + technical → SAME_DAY
        if priority == "High" and category in self.TECHNICAL_CATEGORIES:
            logger.debug(f"Time sensitivity: SAME_DAY (High + {category})")
            return "SAME_DAY"

        # Rule 5: High + SLA at risk → SAME_DAY
        if priority == "High" and sla_breach_probability > 0.7:
            logger.debug("Time sensitivity: SAME_DAY (High + SLA risk)")
            return "SAME_DAY"

        # Rule 6: High priority (any) → SAME_DAY
        if priority == "High":
            logger.debug("Time sensitivity: SAME_DAY (High priority)")
            return "SAME_DAY"

        # Rule 7: Medium + moderate urgency → SAME_DAY
        if priority == "Medium" and urgency_count >= 1:
            logger.debug("Time sensitivity: SAME_DAY (Medium + urgency keywords)")
            return "SAME_DAY"

        # Rule 8: Low + low-urgency category → STANDARD
        if priority == "Low" and category in self.LOW_URGENCY_CATEGORIES:
            logger.debug(f"Time sensitivity: STANDARD (Low + {category})")
            return "STANDARD"

        # Rule 9: Low priority → STANDARD
        if priority == "Low":
            logger.debug("Time sensitivity: STANDARD (Low priority)")
            return "STANDARD"

        # Default: SAME_DAY
        logger.debug("Time sensitivity: SAME_DAY (default)")
        return "SAME_DAY"


# Module-level singleton
time_sensitivity_service = TimeSensitivityService()
