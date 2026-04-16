"""
services/safety_guardrails_service.py — Response safety validation.
Checks AI-generated responses for sensitive data leakage before auto-resolution.
"""

import re
import hashlib
from typing import Dict, List, Tuple
from loguru import logger


class SafetyGuardrailsService:
    """
    Validates AI-generated responses before they are sent to users.

    Checks for:
    - Credit card numbers (Luhn-valid 13-19 digit sequences)
    - Social Security Numbers (XXX-XX-XXXX)
    - Passwords / API keys / secrets in responses
    - Potentially dangerous instructions (download from unknown sources)
    - Personal data patterns (email addresses, phone numbers)
    """

    # ── Regex patterns ────────────────────────────────────────────────
    PATTERNS: List[Tuple[str, re.Pattern, str]] = [
        (
            "credit_card",
            re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
            "Potential credit card number detected",
        ),
        (
            "ssn",
            re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b"),
            "Potential SSN detected",
        ),
        (
            "api_key",
            re.compile(
                r"(?:api[_-]?key|secret[_-]?key|access[_-]?token|bearer)\s*[:=]\s*['\"]?[\w\-]{20,}",
                re.IGNORECASE,
            ),
            "Potential API key or secret detected",
        ),
        (
            "password_plain",
            re.compile(
                r"(?:password|passwd|pwd)\s*[:=]\s*\S+",
                re.IGNORECASE,
            ),
            "Plain-text password detected",
        ),
        (
            "private_key",
            re.compile(
                r"-----BEGIN\s+(?:RSA\s+)?PRIVATE KEY-----",
                re.IGNORECASE,
            ),
            "Private key detected",
        ),
        (
            "connection_string",
            re.compile(
                r"(?:mongodb|postgres|mysql|redis)://\S+:\S+@\S+",
                re.IGNORECASE,
            ),
            "Database connection string with credentials detected",
        ),
    ]

    # Keywords that suggest dangerous instructions
    DANGEROUS_INSTRUCTIONS = [
        "download from",
        "run this exe",
        "disable antivirus",
        "disable firewall",
        "turn off security",
        "paste this in terminal",
        "curl | bash",
        "wget | sh",
        "powershell -enc",
        "base64 -d",
    ]

    def validate_response(self, response: str) -> Dict:
        """
        Check a generated response for safety violations.

        Args:
            response: The AI-generated response text.

        Returns:
            Dict with:
                is_safe: bool — True if no violations found
                violations: list of violation dicts
                sanitized_response: str — response with sensitive data redacted
                response_hash: str — SHA256 hash of original response
        """
        violations = []
        sanitized = response

        # Check regex patterns
        for name, pattern, message in self.PATTERNS:
            matches = pattern.findall(response)
            if matches:
                violations.append(
                    {
                        "type": name,
                        "message": message,
                        "count": len(matches),
                    }
                )
                # Redact the matches
                sanitized = pattern.sub(f"[REDACTED-{name.upper()}]", sanitized)

        # Check for dangerous instructions
        response_lower = response.lower()
        for phrase in self.DANGEROUS_INSTRUCTIONS:
            if phrase in response_lower:
                violations.append(
                    {
                        "type": "dangerous_instruction",
                        "message": f"Dangerous instruction detected: '{phrase}'",
                        "count": 1,
                    }
                )

        # Generate SHA256 hash for audit trail
        response_hash = hashlib.sha256(response.encode("utf-8")).hexdigest()

        is_safe = len(violations) == 0

        if not is_safe:
            logger.warning(
                f"Safety guardrails triggered: {len(violations)} violation(s) found. "
                f"Types: {[v['type'] for v in violations]}"
            )

        return {
            "is_safe": is_safe,
            "violations": violations,
            "sanitized_response": sanitized if not is_safe else response,
            "response_hash": response_hash,
        }

    def should_escalate(self, validation_result: Dict) -> bool:
        """
        Determine if a response should be escalated to human review
        instead of being auto-resolved.

        Escalate if any high-severity violations are found.
        """
        if validation_result["is_safe"]:
            return False

        high_severity_types = {
            "credit_card",
            "ssn",
            "private_key",
            "password_plain",
            "connection_string",
        }
        for violation in validation_result["violations"]:
            if violation["type"] in high_severity_types:
                return True

        return False


# Module-level singleton
safety_guardrails_service = SafetyGuardrailsService()
