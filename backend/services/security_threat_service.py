"""
services/security_threat_service.py — Security threat detection pipeline.
Analyses tickets for security threats using keyword detection + Ollama analysis.
"""

import re
import asyncio
from typing import Dict, Any, Optional, List
from loguru import logger

from services.llm_provider_factory import llm_provider as ollama_provider


class SecurityThreatService:
    """
    Multi-stage security threat detection pipeline.

    Stage 1: Keyword-based pre-filter (fast, runs on every ticket)
    Stage 2: Disguised attack detector (pattern matching for hidden threats)
    Stage 3: Ollama-based deep threat analysis (only for flagged tickets)
    """

    # ── Stage 1: Security keywords ────────────────────────────────────
    THREAT_KEYWORDS = {
        "phishing": ["phishing", "suspicious email", "fake login", "credential harvest",
                      "impersonation", "spoofed", "verify your account"],
        "malware": ["malware", "ransomware", "virus", "trojan", "crypto miner",
                     "encrypted files", "suspicious executable", "worm"],
        "data_breach": ["data breach", "leaked", "exposed", "compromised data",
                         "records accessed", "unauthorized download"],
        "unauthorized_access": ["unauthorized", "foreign ip", "unknown login",
                                 "privilege escalation", "root access", "admin takeover"],
        "social_engineering": ["pretexting", "baiting", "social engineering",
                                "impersonating", "pretending to be"],
        "insider_threat": ["exfiltration", "copied to usb", "personal email",
                           "policy violation", "sabotage", "unauthorized sharing"],
    }

    SEVERITY_KEYWORDS = {
        "critical": ["ransomware", "data breach", "production compromised",
                      "all records", "encrypted files", "ransom", "ddos"],
        "high": ["malware", "unauthorized access", "phishing", "hacked",
                  "stolen credentials", "trojan", "compromised"],
        "medium": ["suspicious", "potential threat", "security concern",
                    "unusual activity"],
    }

    # ── Stage 2: Disguised attack patterns ────────────────────────────
    DISGUISED_PATTERNS = [
        # URLs in seemingly innocent requests
        re.compile(r"(?:click|visit|go to|open)\s+(?:this\s+)?(?:link|url|site)[:\s]+\S+", re.I),
        # Credential harvesting disguised as help requests
        re.compile(r"(?:send|share|provide|give)\s+(?:me\s+)?(?:your\s+)?(?:password|credentials|login|api.?key)", re.I),
        # Social engineering indicators
        re.compile(r"(?:i'?m|this is)\s+(?:the\s+)?(?:ceo|cto|director|manager|admin)\s+(?:and\s+)?(?:i\s+)?need", re.I),
        # Urgency pressure tactics
        re.compile(r"(?:must|need to)\s+(?:immediately|right now|asap)\s+(?:transfer|send|wire|pay)", re.I),
        # Base64 encoded content
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}", re.I),
        # Suspicious file extensions
        re.compile(r"\.\s*(?:exe|bat|cmd|ps1|vbs|scr|pif|com)\b", re.I),
    ]

    def pre_filter(self, text: str) -> Dict[str, Any]:
        """
        Stage 1: Fast keyword-based security pre-filter.
        Runs on every ticket to detect obvious security threats.

        Returns:
            Dict with threat_detected, threat_types, severity, indicators
        """
        text_lower = text.lower()
        detected_types = []
        indicators = []

        for threat_type, keywords in self.THREAT_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    if threat_type not in detected_types:
                        detected_types.append(threat_type)
                    indicators.append(kw)

        # Determine severity
        severity = "none"
        for sev, keywords in self.SEVERITY_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                severity = sev
                break

        if not detected_types:
            severity = "none"

        return {
            "threat_detected": len(detected_types) > 0,
            "threat_types": detected_types,
            "primary_threat_type": detected_types[0] if detected_types else "none",
            "severity": severity,
            "indicators": indicators,
        }

    def detect_disguised_attacks(self, text: str) -> Dict[str, Any]:
        """
        Stage 2: Pattern-based detection of disguised/hidden attacks.
        Catches threats hidden inside normal-looking requests.

        Returns:
            Dict with disguised_threat_detected, patterns_matched, risk_score
        """
        patterns_matched = []
        for pattern in self.DISGUISED_PATTERNS:
            matches = pattern.findall(text)
            if matches:
                patterns_matched.extend(matches[:3])  # cap at 3 per pattern

        risk_score = min(1.0, len(patterns_matched) * 0.25)

        return {
            "disguised_threat_detected": len(patterns_matched) > 0,
            "patterns_matched": patterns_matched,
            "risk_score": risk_score,
        }

    async def analyze_threat(
        self,
        text: str,
        category: str,
        pre_filter_result: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Full threat analysis pipeline.

        Stage 1: Keyword pre-filter (always)
        Stage 2: Disguised attack check (always)
        Stage 3: Ollama deep analysis (only if pre-filter or disguised attack detected,
                  OR if category is 'Security')

        Returns:
            Complete threat analysis dict for storage in ticket.ai_analysis.threat_analysis
        """
        # Stage 1
        if pre_filter_result is None:
            pre_filter_result = self.pre_filter(text)

        # Stage 2
        disguised_result = self.detect_disguised_attacks(text)

        # Decide if Stage 3 (Ollama) is needed
        needs_deep_analysis = (
            pre_filter_result["threat_detected"]
            or disguised_result["disguised_threat_detected"]
            or category == "Security"
        )

        # Stage 3: Ollama deep analysis
        ollama_result = None
        if needs_deep_analysis:
            try:
                ollama_result = await asyncio.wait_for(
                    ollama_provider.analyze_threat(text),
                    timeout=20.0,
                )
            except Exception as e:
                logger.warning(f"Ollama threat analysis failed (non-fatal): {e}")

        # Merge results
        threat_detected = pre_filter_result["threat_detected"]
        threat_type = pre_filter_result["primary_threat_type"]
        severity = pre_filter_result["severity"]
        confidence = 0.0
        recommended_action = ""
        indicators = pre_filter_result.get("indicators", [])

        if ollama_result:
            # Ollama overrides if it provides higher confidence
            if ollama_result.get("threat_detected", False):
                threat_detected = True
            if ollama_result.get("confidence", 0) > 0.5:
                threat_type = ollama_result.get("threat_type", threat_type)
                severity = ollama_result.get("severity", severity)
                confidence = ollama_result.get("confidence", 0)
                recommended_action = ollama_result.get("recommended_action", "")
                indicators.extend(ollama_result.get("indicators", []))
        elif threat_detected:
            # Use pre-filter confidence based on indicator count
            confidence = min(1.0, len(indicators) * 0.2 + 0.3)

        if disguised_result["disguised_threat_detected"]:
            threat_detected = True
            if not threat_type or threat_type == "none":
                threat_type = "social_engineering"
            indicators.extend(disguised_result["patterns_matched"])
            confidence = max(confidence, disguised_result["risk_score"])

        # Determine escalation level
        escalation_level = None
        if threat_detected:
            if severity in ("critical", "high"):
                escalation_level = "L1"  # Immediate security agent
            elif severity == "medium":
                escalation_level = "L1"
            else:
                escalation_level = "L1"

        result = {
            "threat_detected": threat_detected,
            "threat_type": threat_type if threat_detected else "none",
            "severity": severity if threat_detected else "none",
            "confidence": round(confidence, 3),
            "recommended_action": recommended_action,
            "indicators": list(set(indicators))[:10],  # dedupe and cap
            "escalation_level": escalation_level,
            "escalation_timer_started": threat_detected and severity in ("critical", "high"),
            "pre_filter_flags": pre_filter_result["threat_types"],
            "disguised_attack_detected": disguised_result["disguised_threat_detected"],
        }

        if threat_detected:
            logger.warning(
                f"SECURITY THREAT: type={threat_type}, severity={severity}, "
                f"confidence={confidence:.2f}, indicators={indicators[:3]}"
            )

        return result


# Module-level singleton
security_threat_service = SecurityThreatService()
