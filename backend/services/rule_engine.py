"""
services/rule_engine.py — Security Rule Engine.

Step 5 of the AI Security Pipeline.
Detects: SQL Injection, XSS, Brute Force, Unauthorized Access, DDoS patterns.
If rules are triggered → override ML result → classify as Suspicious or Attack.
"""

import re
from typing import Dict, Any, List, Tuple
from loguru import logger

# ─── Rule Definitions ─────────────────────────────────────────────────

SQL_INJECTION_PATTERNS = [
    re.compile(r"'\s*or\s+\d+=\d+", re.I),  # ' OR 1=1
    re.compile(r"'\s*or\s+'[^']*'\s*=\s*'[^']*'", re.I),  # ' OR 'a'='a
    re.compile(r"drop\s+table", re.I),
    re.compile(r"drop\s+database", re.I),
    re.compile(r";\s*delete\s+from", re.I),
    re.compile(r";\s*insert\s+into", re.I),
    re.compile(r"union\s+select", re.I),
    re.compile(r"select\s+\*\s+from", re.I),
    re.compile(r"--\s*$", re.M),  # SQL comment at end
    re.compile(r"/\*.*?\*/", re.S),  # SQL block comment
    re.compile(r"exec\s*\(", re.I),
    re.compile(r"xp_cmdshell", re.I),
    re.compile(r"information_schema", re.I),
    re.compile(r"sleep\s*\(\s*\d+\s*\)", re.I),  # time-based blind
    re.compile(r"benchmark\s*\(", re.I),
    re.compile(r"load_file\s*\(", re.I),
    re.compile(r"into\s+outfile", re.I),
]

XSS_PATTERNS = [
    re.compile(r"<\s*script[^>]*>", re.I),
    re.compile(r"</\s*script\s*>", re.I),
    re.compile(r"javascript\s*:", re.I),
    re.compile(r"on\w+\s*=\s*['\"]", re.I),  # onerror=, onclick=
    re.compile(r"alert\s*\(", re.I),
    re.compile(r"document\s*\.\s*cookie", re.I),
    re.compile(r"document\s*\.\s*write\s*\(", re.I),
    re.compile(r"eval\s*\(", re.I),
    re.compile(r"<\s*iframe[^>]*>", re.I),
    re.compile(r"<\s*img[^>]+onerror", re.I),
    re.compile(r"src\s*=\s*['\"]javascript:", re.I),
    re.compile(r"&#x[0-9a-f]+;", re.I),  # hex encoding
    re.compile(r"%3c\s*script", re.I),  # URL-encoded <script
    re.compile(r"expression\s*\(", re.I),  # CSS expression
    re.compile(r"vbscript\s*:", re.I),
]

BRUTE_FORCE_PATTERNS = [
    re.compile(r"multiple\s+(failed\s+)?login\s+attempt", re.I),
    re.compile(r"repeated\s+(login|password|auth)", re.I),
    re.compile(r"account\s+(locked|blocked|suspended)\s+after", re.I),
    re.compile(r"too\s+many\s+(failed\s+)?(login|password|attempt)", re.I),
    re.compile(r"brute\s+force", re.I),
    re.compile(r"password\s+spray", re.I),
    re.compile(r"credential\s+stuff", re.I),
    re.compile(r"\d+\s+failed\s+(login|attempt|auth)", re.I),  # "50 failed logins"
    re.compile(r"login\s+attempt.{0,30}\d{2,}", re.I),  # login attempts + number
]

UNAUTHORIZED_ACCESS_PATTERNS = [
    re.compile(r"admin\s+access", re.I),
    re.compile(r"bypass\s+(auth|login|security|access|2fa|mfa)", re.I),
    re.compile(r"privilege\s+escalat", re.I),
    re.compile(r"root\s+access", re.I),
    re.compile(r"sudo\s+", re.I),
    re.compile(r"unauthorized\s+(access|login|entry)", re.I),
    re.compile(r"access\s+without\s+(permission|auth)", re.I),
    re.compile(r"override\s+(security|permission|access)", re.I),
    re.compile(r"disable\s+(firewall|antivirus|security|2fa|mfa)", re.I),
    re.compile(r"back\s*door", re.I),
    re.compile(r"exploit\s+(vuln|cve|zero.?day)", re.I),
    re.compile(r"cve-\d{4}-\d+", re.I),  # CVE reference
]

DDOS_PATTERNS = [
    re.compile(r"ddos", re.I),
    re.compile(r"denial\s+of\s+service", re.I),
    re.compile(r"flood(ing)?\s+(attack|request|traffic)", re.I),
    re.compile(r"(server|service|site)\s+(down|unavailable|overload)", re.I),
    re.compile(r"high\s+(traffic|load|request)\s+(volume|spike|surge)", re.I),
    re.compile(r"bandwidth\s+(exhaust|saturat|flood)", re.I),
    re.compile(r"syn\s+flood", re.I),
    re.compile(r"amplification\s+attack", re.I),
    re.compile(r"botnet", re.I),
    re.compile(r"thousands?\s+of\s+request", re.I),
]

# Keywords that bump Normal → Suspicious (hidden threat detection)
SUSPICIOUS_KEYWORDS = [
    "unusual activity",
    "strange behavior",
    "weird request",
    "slow after login",
    "system slow after",
    "performance drop after",
    "someone else",
    "not me",
    "wasn't me",
    "i didn't do",
    "account accessed",
    "unknown device",
    "unfamiliar location",
    "foreign ip",
    "different country",
    "vpn bypass",
    "need admin",
    "need root",
    "need superuser",
    "urgent access",
    "emergency access",
    "bypass verification",
]


class RuleEngine:
    """
    Security Rule Engine — Step 5 of the AI Security Pipeline.

    Evaluates text against rule sets and returns:
    - threat_level: normal | suspicious | attack
    - threat_type: sql_injection | xss | brute_force | unauthorized_access | ddos | none
    - triggered_rules: list of matched rule descriptions
    - detection_reason: human-readable explanation
    - override_ml: bool — whether to override the ML classification
    """

    def _check_patterns(
        self,
        text: str,
        patterns: List[re.Pattern],
        rule_name: str,
    ) -> Tuple[bool, List[str]]:
        """Run a list of regex patterns against text. Returns (matched, matched_strings)."""
        matched = []
        for pat in patterns:
            hits = pat.findall(text)
            if hits:
                matched.extend([str(h)[:80] for h in hits[:2]])  # cap per pattern
        return len(matched) > 0, matched

    def evaluate(self, text: str, ml_threat_level: str = "normal") -> Dict[str, Any]:
        """
        Evaluate text against all security rules.

        Args:
            text: Raw ticket text (subject + description).
            ml_threat_level: The ML model's initial classification.

        Returns:
            Dict with threat_level, threat_type, triggered_rules,
            detection_reason, override_ml, confidence_boost.
        """
        triggered_rules: List[str] = []
        matched_evidence: List[str] = []
        threat_type = "none"
        threat_level = ml_threat_level

        # ── SQL Injection ─────────────────────────────────────────────
        sql_hit, sql_evidence = self._check_patterns(
            text, SQL_INJECTION_PATTERNS, "sql_injection"
        )
        if sql_hit:
            triggered_rules.append("sql_injection")
            matched_evidence.extend(sql_evidence)
            threat_type = "sql_injection"
            threat_level = "attack"

        # ── XSS ──────────────────────────────────────────────────────
        xss_hit, xss_evidence = self._check_patterns(text, XSS_PATTERNS, "xss")
        if xss_hit:
            triggered_rules.append("xss")
            matched_evidence.extend(xss_evidence)
            if threat_type == "none":
                threat_type = "xss"
            threat_level = "attack"

        # ── Brute Force ───────────────────────────────────────────────
        bf_hit, bf_evidence = self._check_patterns(
            text, BRUTE_FORCE_PATTERNS, "brute_force"
        )
        if bf_hit:
            triggered_rules.append("brute_force")
            matched_evidence.extend(bf_evidence)
            if threat_type == "none":
                threat_type = "brute_force"
            # Brute force = suspicious unless already attack
            if threat_level == "normal":
                threat_level = "suspicious"

        # ── Unauthorized Access ───────────────────────────────────────
        ua_hit, ua_evidence = self._check_patterns(
            text, UNAUTHORIZED_ACCESS_PATTERNS, "unauthorized_access"
        )
        if ua_hit:
            triggered_rules.append("unauthorized_access")
            matched_evidence.extend(ua_evidence)
            if threat_type == "none":
                threat_type = "unauthorized_access"
            if threat_level == "normal":
                threat_level = "suspicious"
            # Multiple unauthorized patterns → escalate to attack
            if len(ua_evidence) >= 2:
                threat_level = "attack"

        # ── DDoS ─────────────────────────────────────────────────────
        ddos_hit, ddos_evidence = self._check_patterns(text, DDOS_PATTERNS, "ddos")
        if ddos_hit:
            triggered_rules.append("ddos")
            matched_evidence.extend(ddos_evidence)
            if threat_type == "none":
                threat_type = "ddos"
            threat_level = "attack"

        # ── Hidden Threat Detection (Normal → Suspicious) ─────────────
        # If ML says normal but suspicious keywords found → reclassify
        if threat_level == "normal":
            text_lower = text.lower()
            suspicious_hits = [kw for kw in SUSPICIOUS_KEYWORDS if kw in text_lower]
            if suspicious_hits:
                triggered_rules.append("suspicious_keywords")
                matched_evidence.extend(suspicious_hits[:3])
                threat_level = "suspicious"
                threat_type = "unauthorized_access"

        # ── Build result ──────────────────────────────────────────────
        override_ml = len(triggered_rules) > 0 and threat_level != ml_threat_level

        detection_reason = self._build_reason(
            triggered_rules, matched_evidence, threat_level
        )

        # Confidence boost based on number of triggered rules
        confidence_boost = min(0.4, len(triggered_rules) * 0.15)

        result = {
            "threat_level": threat_level,
            "threat_type": threat_type,
            "triggered_rules": triggered_rules,
            "matched_evidence": matched_evidence[:10],  # cap for storage
            "detection_reason": detection_reason,
            "override_ml": override_ml,
            "confidence_boost": round(confidence_boost, 3),
        }

        if triggered_rules:
            logger.warning(
                f"Rule engine triggered: level={threat_level}, "
                f"type={threat_type}, rules={triggered_rules}"
            )

        return result

    def _build_reason(
        self,
        triggered_rules: List[str],
        evidence: List[str],
        threat_level: str,
    ) -> str:
        """Build a human-readable detection reason string."""
        if not triggered_rules:
            return "No security rules triggered."

        rule_labels = {
            "sql_injection": "SQL Injection pattern",
            "xss": "Cross-Site Scripting (XSS) pattern",
            "brute_force": "Brute force / repeated login attempt",
            "unauthorized_access": "Unauthorized access attempt",
            "ddos": "DDoS / flooding pattern",
            "suspicious_keywords": "Suspicious activity keywords",
        }

        labels = [rule_labels.get(r, r) for r in triggered_rules]
        reason = f"Detected: {', '.join(labels)}."

        if evidence:
            sample = evidence[0][:60]
            reason += f' Evidence: "{sample}"'

        return reason


# Module-level singleton
rule_engine = RuleEngine()
