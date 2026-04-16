"""
services/department_service.py — Department taxonomy and routing.
Maps ticket categories to departments, supports cross-department tagging.
"""

from typing import Dict, List, Optional
from loguru import logger

from core.config import settings


class DepartmentService:
    """
    Manages department taxonomy and category-to-department routing.

    Departments:
    - NETWORK: Network, connectivity, firewall, VPN, email server issues
    - SOFTWARE: Software bugs, auth problems, access control, app crashes
    - DATABASE: Database issues, SQL, data recovery, backups
    - SECURITY: Security threats, compliance, data breaches
    - BILLING: Invoices, payments, subscriptions, refunds
    - HR_FACILITIES: Hardware, service requests, onboarding, physical access
    """

    # Cross-department keyword indicators (when a ticket touches multiple depts)
    CROSS_DEPARTMENT_KEYWORDS: Dict[str, List[str]] = {
        "NETWORK": [
            "network",
            "connectivity",
            "vpn",
            "firewall",
            "dns",
            "ip address",
            "bandwidth",
            "wifi",
            "ethernet",
            "proxy",
        ],
        "SOFTWARE": [
            "software",
            "application",
            "crash",
            "bug",
            "error",
            "update",
            "install",
            "login",
            "authentication",
            "api",
        ],
        "DATABASE": [
            "database",
            "sql",
            "query",
            "backup",
            "restore",
            "migration",
            "data loss",
            "table",
            "schema",
            "replication",
        ],
        "SECURITY": [
            "phishing",
            "malware",
            "breach",
            "unauthorized",
            "hack",
            "vulnerability",
            "exploit",
            "ransomware",
            "suspicious",
        ],
        "BILLING": [
            "invoice",
            "payment",
            "charge",
            "refund",
            "subscription",
            "billing",
            "credit",
            "discount",
            "pricing",
        ],
        "HR_FACILITIES": [
            "hardware",
            "laptop",
            "monitor",
            "keyboard",
            "printer",
            "desk",
            "office",
            "onboarding",
            "badge",
            "parking",
        ],
    }

    def get_primary_department(self, category: str) -> str:
        """
        Get the primary department for a category.
        Uses the CATEGORY_TO_DEPARTMENT mapping from config.
        """
        return settings.CATEGORY_TO_DEPARTMENT.get(category, "SOFTWARE")

    def get_cross_departments(self, text: str, primary_department: str) -> List[str]:
        """
        Detect if a ticket touches multiple departments based on keyword analysis.

        Returns:
            List of secondary departments (excluding primary).
        """
        text_lower = text.lower()
        scores: Dict[str, int] = {}

        for dept, keywords in self.CROSS_DEPARTMENT_KEYWORDS.items():
            if dept == primary_department:
                continue
            count = sum(1 for kw in keywords if kw in text_lower)
            if count >= 2:  # require at least 2 keyword matches for cross-dept
                scores[dept] = count

        # Sort by score descending and return top 2
        sorted_depts = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        secondary = [dept for dept, _ in sorted_depts[:2]]

        if secondary:
            logger.debug(
                f"Cross-department tagging: primary={primary_department}, "
                f"secondary={secondary}"
            )

        return secondary

    def route_ticket(self, category: str, text: str) -> Dict:
        """
        Full department routing for a ticket.

        Returns:
            Dict with primary_department, secondary_departments, and all_departments.
        """
        primary = self.get_primary_department(category)
        secondary = self.get_cross_departments(text, primary)

        return {
            "primary_department": primary,
            "secondary_departments": secondary,
            "all_departments": [primary] + secondary,
        }


# Module-level singleton
department_service = DepartmentService()
