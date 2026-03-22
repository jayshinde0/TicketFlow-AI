"""
services/escalation_service.py — Timed escalation chain for security threats.
L1 → L2 (15 min) → L3 (30 min) with WebSocket notifications.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from loguru import logger

from core.config import settings


class EscalationService:
    """
    Manages timed escalation chain for security incidents.

    Levels:
    - L1: Security Agent (immediate assignment)
    - L2: Team Lead (after ESCALATION_L2_TIMEOUT_MINUTES minutes unacknowledged)
    - L3: Admin/CISO (after ESCALATION_L3_TIMEOUT_MINUTES minutes unacknowledged)
    """

    PLAYBOOKS = {
        "phishing": {
            "title": "Phishing Response Playbook",
            "steps": [
                "Isolate the affected user's email account",
                "Check if credentials were entered on the phishing page",
                "Force password reset for affected accounts",
                "Block the phishing domain on email gateway",
                "Notify all users of the phishing campaign",
                "Report the URL to Google Safe Browsing and VirusTotal",
                "Document the incident timeline",
            ],
        },
        "malware": {
            "title": "Malware Response Playbook",
            "steps": [
                "Immediately disconnect the infected machine from the network",
                "Do NOT power off — preserve memory for forensics",
                "Run full AV scan and capture the scan log",
                "Check if lateral movement occurred (review network logs)",
                "Identify the malware variant and vector of entry",
                "Restore from last known clean backup if needed",
                "Patch the vulnerability that allowed the infection",
                "Re-image the machine and restore user data from backup",
            ],
        },
        "data_breach": {
            "title": "Data Breach Response Playbook",
            "steps": [
                "Contain the breach: revoke compromised access immediately",
                "Identify scope: what data was accessed and how much",
                "Preserve all evidence and logs for forensics",
                "Notify legal and compliance teams",
                "Determine notification obligations (GDPR, CCPA, etc.)",
                "Prepare customer/user communication if required",
                "Engage third-party forensics team if severity is critical",
                "Implement corrective measures to prevent recurrence",
            ],
        },
        "unauthorized_access": {
            "title": "Unauthorized Access Response Playbook",
            "steps": [
                "Immediately revoke the unauthorized session/access",
                "Force password reset on the affected account",
                "Review access logs to determine scope of access",
                "Check for data exfiltration or modifications",
                "Enable MFA if not already enabled",
                "Review and tighten access permissions",
                "Document all findings and actions taken",
            ],
        },
        "social_engineering": {
            "title": "Social Engineering Response Playbook",
            "steps": [
                "Verify the identity of the requester through a separate channel",
                "Do NOT comply with any urgent requests without verification",
                "Document the social engineering attempt details",
                "Alert the security team and all potential targets",
                "Review if any actions were taken based on the attempt",
                "Update security awareness training materials",
            ],
        },
        "insider_threat": {
            "title": "Insider Threat Response Playbook",
            "steps": [
                "Do NOT alert the suspected insider directly",
                "Begin covert monitoring of their activities (with legal approval)",
                "Preserve all audit logs and evidence",
                "Restrict access to critical systems discreetly",
                "Engage HR and legal departments",
                "Prepare for account suspension and data recovery",
                "Conduct forensic analysis of recent activities",
            ],
        },
    }

    async def create_escalation(
        self,
        ticket_id: str,
        threat_analysis: Dict[str, Any],
        created_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Create an escalation record for a security threat.
        This starts the timed escalation chain.
        """
        now = created_at or datetime.now(timezone.utc)
        threat_type = threat_analysis.get("threat_type", "none")
        severity = threat_analysis.get("severity", "none")

        escalation = {
            "ticket_id": ticket_id,
            "threat_type": threat_type,
            "severity": severity,
            "current_level": "L1",
            "created_at": now.isoformat(),
            "l2_escalation_at": (
                now + timedelta(minutes=settings.ESCALATION_L2_TIMEOUT_MINUTES)
            ).isoformat(),
            "l3_escalation_at": (
                now + timedelta(minutes=settings.ESCALATION_L3_TIMEOUT_MINUTES)
            ).isoformat(),
            "acknowledged": False,
            "acknowledged_by": None,
            "acknowledged_at": None,
            "resolved": False,
            "resolved_at": None,
            "playbook": self.PLAYBOOKS.get(threat_type, {}).get("title", "General Security Response"),
            "playbook_steps_completed": [],
            "incident_report": None,
        }

        # Store in database
        try:
            from core.database import get_db
            db = get_db()
            if db is not None:
                await db["escalation_logs"].insert_one(escalation)
                logger.info(f"Escalation created for ticket {ticket_id}: L1, severity={severity}")
        except Exception as e:
            logger.warning(f"Failed to store escalation (non-fatal): {e}")

        # Send WebSocket notification
        try:
            from services.notification_service import notification_service
            await notification_service.notify_root_cause_alert({
                "type": "security_escalation",
                "ticket_id": ticket_id,
                "threat_type": threat_type,
                "severity": severity,
                "level": "L1",
                "message": f"Security threat detected: {threat_type} (severity: {severity})",
            })
        except Exception as e:
            logger.warning(f"Escalation notification failed (non-fatal): {e}")

        return escalation

    async def check_escalations(self) -> None:
        """
        Check all pending escalations and escalate if timeouts exceeded.
        Intended to be called by APScheduler every 5 minutes.
        """
        try:
            from core.database import get_db
            db = get_db()
            if db is None:
                return

            now = datetime.now(timezone.utc)
            now_iso = now.isoformat()

            # Find un-acknowledged L1 escalations past L2 timeout
            cursor = db["escalation_logs"].find({
                "acknowledged": False,
                "resolved": False,
                "current_level": "L1",
                "l2_escalation_at": {"$lte": now_iso},
            })
            async for esc in cursor:
                await db["escalation_logs"].update_one(
                    {"_id": esc["_id"]},
                    {"$set": {"current_level": "L2"}},
                )
                logger.warning(
                    f"Escalation L1→L2 for ticket {esc['ticket_id']} "
                    f"(unacknowledged for {settings.ESCALATION_L2_TIMEOUT_MINUTES} min)"
                )

            # Find un-acknowledged L2 escalations past L3 timeout
            cursor = db["escalation_logs"].find({
                "acknowledged": False,
                "resolved": False,
                "current_level": "L2",
                "l3_escalation_at": {"$lte": now_iso},
            })
            async for esc in cursor:
                await db["escalation_logs"].update_one(
                    {"_id": esc["_id"]},
                    {"$set": {"current_level": "L3"}},
                )
                logger.error(
                    f"Escalation L2→L3 (ADMIN) for ticket {esc['ticket_id']} "
                    f"(unacknowledged for {settings.ESCALATION_L3_TIMEOUT_MINUTES} min)"
                )

        except Exception as e:
            logger.error(f"Escalation check failed: {e}")

    async def acknowledge_escalation(
        self, ticket_id: str, agent_id: str
    ) -> bool:
        """Mark an escalation as acknowledged by an agent."""
        try:
            from core.database import get_db
            db = get_db()
            if db is None:
                return False

            result = await db["escalation_logs"].update_one(
                {"ticket_id": ticket_id, "resolved": False},
                {
                    "$set": {
                        "acknowledged": True,
                        "acknowledged_by": agent_id,
                        "acknowledged_at": datetime.now(timezone.utc).isoformat(),
                    }
                },
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Acknowledge escalation failed: {e}")
            return False

    async def submit_incident_report(
        self,
        ticket_id: str,
        report: Dict[str, Any],
    ) -> bool:
        """Submit a post-incident report for a security escalation."""
        try:
            from core.database import get_db
            db = get_db()
            if db is None:
                return False

            report["submitted_at"] = datetime.now(timezone.utc).isoformat()

            # Store report in both escalation log and dedicated collection
            await db["escalation_logs"].update_one(
                {"ticket_id": ticket_id},
                {"$set": {"incident_report": report, "resolved": True,
                          "resolved_at": datetime.now(timezone.utc).isoformat()}},
            )
            await db["incident_reports"].insert_one({
                "ticket_id": ticket_id,
                **report,
            })
            return True
        except Exception as e:
            logger.error(f"Incident report submission failed: {e}")
            return False

    def get_playbook(self, threat_type: str) -> Dict[str, Any]:
        """Get the response playbook for a given threat type."""
        return self.PLAYBOOKS.get(threat_type, {
            "title": "General Security Response Playbook",
            "steps": [
                "Assess the scope of the security incident",
                "Contain the threat to prevent further damage",
                "Preserve all evidence and logs",
                "Notify the security team lead",
                "Document all actions taken",
                "Implement corrective measures",
            ],
        })


# Module-level singleton
escalation_service = EscalationService()
