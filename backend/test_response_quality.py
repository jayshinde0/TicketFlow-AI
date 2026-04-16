# backend/test_response_quality.py (FIXED)

import requests
import json


def test_vpn_response_quality():
    """Test VPN response quality: Mistral vs Qwen"""

    ticket = {
        "subject": "VPN connection not working",
        "description": "I cannot connect to the company VPN. I get a timeout error after entering my credentials. This is blocking my work completely. I need this resolved ASAP.",
    }

    response = requests.post("http://localhost:8000/api/tickets/", json=ticket)

    data = response.json()
    ai_analysis = data["ai_analysis"]

    print("\n" + "=" * 70)
    print("RESPONSE QUALITY TEST: VPN Timeout Issue")
    print("=" * 70)

    print(f"\n📋 TICKET ID: {data['ticket_id']}")
    print(
        f"📁 Category: {ai_analysis['category']} (confidence: {ai_analysis['model_confidence']:.2f})"
    )
    print(f"🎯 Priority: {ai_analysis['priority']}")
    print(f"🚦 Routing: {ai_analysis['routing_decision']}")
    print(f"💯 Confidence Score: {ai_analysis['confidence_score']:.2f}")

    response_text = ai_analysis.get("generated_response") or "N/A"

    print(f"\n📝 GENERATED RESPONSE:")
    print("-" * 70)
    print(response_text)
    print("-" * 70)

    # Score the response
    score = score_response(response_text, "Network")

    print(f"\n📊 RESPONSE QUALITY SCORE: {score}/5")
    print(f"\n✓ Processing Time: {ai_analysis['processing_time_ms']}ms")
    print(f"✓ Hallucination Detected: {ai_analysis['hallucination_detected']}")
    print(f"✓ Model Used: {ai_analysis['model_used']}")
    print(f"✓ Similar Tickets: {len(ai_analysis.get('similar_tickets', []))}")

    return score


def score_response(response: str, category: str) -> float:
    """Score response quality 1-5"""

    # Handle None/empty responses
    if not response or response == "N/A":
        return 0.5

    score = 0.0
    response_lower = response.lower()

    # Category-specific scoring
    if category == "Network":
        # VPN-specific keywords
        vpn_keywords = [
            "firewall",
            "port",
            "gateway",
            "routing",
            "ping",
            "dns",
            "mtu",
            "ike",
            "ipsec",
        ]
        if any(kw in response_lower for kw in vpn_keywords):
            score += 2.0

        # Log/diagnostic keywords
        log_keywords = [
            "log",
            "event viewer",
            "appdata",
            "var/log",
            "command",
            "test",
            "check",
        ]
        if any(kw in response_lower for kw in log_keywords):
            score += 1.5

        # Generic keywords (negative)
        generic_keywords = ["restart", "contact support", "please try", "reinstall"]
        generic_count = sum(1 for kw in generic_keywords if kw in response_lower)
        score -= generic_count * 0.5

    # General scoring
    if "escalat" in response_lower:
        score -= 0.5

    # Bonus for structured format
    if response.count("\n") > 3:
        score += 0.5

    # Minimum 1, maximum 5
    return max(0.5, min(5.0, score))


if __name__ == "__main__":
    score = test_vpn_response_quality()

    if score >= 4.0:
        print("\n✅ RESPONSE QUALITY EXCELLENT")
    elif score >= 3.0:
        print("\n✓ RESPONSE QUALITY GOOD")
    else:
        print("\n⚠️ RESPONSE QUALITY NEEDS IMPROVEMENT")
