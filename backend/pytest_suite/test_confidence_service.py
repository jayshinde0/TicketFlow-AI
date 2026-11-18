"""
test_confidence_service.py - Test confidence scoring logic
Tests the multi-factor confidence calculation and routing decisions
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.confidence_service import confidence_service


class TestConfidenceCalculation:
    """Test confidence score calculation"""

    def test_high_confidence_all_factors(self):
        """Test high confidence when all factors are strong"""
        result = confidence_service.compute(
            model_confidence=0.95,
            similarity_score=0.90,
            ticket_text="VPN connection timeout error",
            category="Network",
            sentiment_label="NEUTRAL",
            sentiment_score=0.5,
            sla_breach_probability=0.1,
            user_tier="Standard",
        )

        assert result["confidence_score"] >= 0.85
        assert result["routing_decision"] == "AUTO_RESOLVE"

    def test_medium_confidence_mixed_factors(self):
        """Test medium confidence with mixed factor strengths"""
        result = confidence_service.compute(
            model_confidence=0.75,
            similarity_score=0.70,
            ticket_text="Some issue with system",
            category="Software",
            sentiment_label="NEUTRAL",
            sentiment_score=0.5,
            sla_breach_probability=0.3,
            user_tier="Standard",
        )

        assert 0.60 <= result["confidence_score"] < 0.85
        assert result["routing_decision"] in ["SUGGEST_TO_AGENT", "ESCALATE_TO_AGENT"]

    def test_low_confidence_weak_factors(self):
        """Test low confidence when all factors are weak"""
        result = confidence_service.compute(
            model_confidence=0.45,
            similarity_score=0.40,
            ticket_text="Something broken help",
            category="Other",
            sentiment_label="NEGATIVE",
            sentiment_score=0.2,
            sla_breach_probability=0.7,
            user_tier="Standard",
        )

        assert result["confidence_score"] < 0.60
        assert result["routing_decision"] in ["ESCALATE_TO_AGENT", "ESCALATE_TO_HUMAN"]


class TestSecurityOverrides:
    """Test security-related routing overrides"""

    def test_security_category_override(self):
        """Security tickets should escalate regardless of confidence"""
        result = confidence_service.compute(
            model_confidence=0.95,
            similarity_score=0.90,
            ticket_text="Phishing email detected",
            category="Security",
            sentiment_label="NEUTRAL",
            sentiment_score=0.5,
            sla_breach_probability=0.1,
            user_tier="Standard",
        )

        # Security should escalate even with high confidence
        assert result["routing_decision"] in ["ESCALATE_TO_AGENT", "ESCALATE_TO_HUMAN"]
        assert result.get("security_override") == True

    def test_non_security_no_override(self):
        """Non-security tickets should not trigger security override"""
        result = confidence_service.compute(
            model_confidence=0.90,
            similarity_score=0.85,
            ticket_text="Password reset needed",
            category="Auth",
            sentiment_label="NEUTRAL",
            sentiment_score=0.5,
            sla_breach_probability=0.2,
            user_tier="Standard",
        )

        assert result.get("security_override") != True


class TestSLAOverrides:
    """Test SLA-based routing overrides"""

    def test_high_sla_breach_risk_escalation(self):
        """High SLA breach probability should escalate"""
        result = confidence_service.compute(
            model_confidence=0.80,
            similarity_score=0.75,
            ticket_text="System down for 3 hours",
            category="Network",
            sentiment_label="NEGATIVE",
            sentiment_score=0.2,
            sla_breach_probability=0.85,  # Very high risk
            user_tier="Standard",
        )

        # Should escalate due to SLA risk
        assert result["routing_decision"] in ["ESCALATE_TO_AGENT", "ESCALATE_TO_HUMAN"]

    def test_low_sla_breach_no_override(self):
        """Low SLA breach probability should not affect routing"""
        result = confidence_service.compute(
            model_confidence=0.90,
            similarity_score=0.85,
            ticket_text="Minor UI glitch",
            category="Software",
            sentiment_label="NEUTRAL",
            sentiment_score=0.5,
            sla_breach_probability=0.1,  # Low risk
            user_tier="Standard",
        )

        # Should auto-resolve with low SLA risk
        assert result["routing_decision"] == "AUTO_RESOLVE"


class TestConfidenceBreakdown:
    """Test confidence score component breakdown"""

    def test_confidence_components_exist(self):
        """Confidence breakdown should have all components"""
        result = confidence_service.compute(
            model_confidence=0.85,
            similarity_score=0.80,
            ticket_text="Test ticket",
            category="Software",
            sentiment_label="NEUTRAL",
            sentiment_score=0.5,
            sla_breach_probability=0.3,
            user_tier="Standard",
        )

        assert "confidence_breakdown" in result
        breakdown = result["confidence_breakdown"]

        # Check all components are present
        assert "model_prob_component" in breakdown
        assert "similarity_component" in breakdown
        assert "keyword_component" in breakdown

    def test_confidence_components_sum_correctly(self):
        """Confidence components should roughly sum to total"""
        result = confidence_service.compute(
            model_confidence=0.80,
            similarity_score=0.75,
            ticket_text="Database connection timeout",
            category="Database",
            sentiment_label="NEUTRAL",
            sentiment_score=0.5,
            sla_breach_probability=0.2,
            user_tier="Standard",
        )

        breakdown = result["confidence_breakdown"]
        component_sum = sum(breakdown.values())

        # Total confidence should be close to sum of components
        # (allowing small difference due to overrides/adjustments)
        assert abs(result["confidence_score"] - component_sum) < 0.15


class TestRoutingDecisions:
    """Test routing decision logic"""

    def test_auto_resolve_threshold(self):
        """Test AUTO_RESOLVE decision at threshold"""
        result = confidence_service.compute(
            model_confidence=0.90,
            similarity_score=0.88,
            ticket_text="Standard password reset",
            category="Auth",
            sentiment_label="NEUTRAL",
            sentiment_score=0.5,
            sla_breach_probability=0.1,
            user_tier="Standard",
        )

        assert result["confidence_score"] >= 0.85
        assert result["routing_decision"] == "AUTO_RESOLVE"

    def test_suggest_to_agent_range(self):
        """Test SUGGEST_TO_AGENT in medium confidence range"""
        result = confidence_service.compute(
            model_confidence=0.75,
            similarity_score=0.72,
            ticket_text="Application not responding",
            category="Software",
            sentiment_label="NEUTRAL",
            sentiment_score=0.5,
            sla_breach_probability=0.3,
            user_tier="Standard",
        )

        # Should be in suggest range (0.65-0.85)
        assert 0.65 <= result["confidence_score"] < 0.85
        assert result["routing_decision"] == "SUGGEST_TO_AGENT"

    def test_escalate_low_confidence(self):
        """Test escalation for low confidence"""
        result = confidence_service.compute(
            model_confidence=0.50,
            similarity_score=0.45,
            ticket_text="Complex technical issue",
            category="Other",
            sentiment_label="NEGATIVE",
            sentiment_score=0.3,
            sla_breach_probability=0.6,
            user_tier="Standard",
        )

        assert result["confidence_score"] < 0.65
        assert result["routing_decision"] in ["ESCALATE_TO_AGENT", "ESCALATE_TO_HUMAN"]


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_zero_confidence(self):
        """Test handling of zero confidence"""
        result = confidence_service.compute(
            model_confidence=0.0,
            similarity_score=0.0,
            ticket_text="asdfasdf random text",
            category="Other",
            sentiment_label="NEUTRAL",
            sentiment_score=0.5,
            sla_breach_probability=0.5,
            user_tier="Standard",
        )

        assert result["confidence_score"] >= 0.0
        assert result["routing_decision"] == "ESCALATE_TO_HUMAN"

    def test_perfect_confidence(self):
        """Test handling of perfect confidence"""
        result = confidence_service.compute(
            model_confidence=1.0,
            similarity_score=1.0,
            ticket_text="Exact duplicate ticket match",
            category="Network",
            sentiment_label="NEUTRAL",
            sentiment_score=0.5,
            sla_breach_probability=0.0,
            user_tier="Standard",
        )

        assert result["confidence_score"] <= 1.0
        assert result["routing_decision"] == "AUTO_RESOLVE"

    def test_empty_ticket_text(self):
        """Test handling of empty ticket text"""
        result = confidence_service.compute(
            model_confidence=0.70,
            similarity_score=0.65,
            ticket_text="",
            category="Other",
            sentiment_label="NEUTRAL",
            sentiment_score=0.5,
            sla_breach_probability=0.3,
            user_tier="Standard",
        )

        # Should handle gracefully
        assert "confidence_score" in result
        assert "routing_decision" in result


# Parametrized test for multiple scenarios
@pytest.mark.parametrize(
    "model_conf,sim_score,category,expected_decision",
    [
        (0.95, 0.92, "Network", "AUTO_RESOLVE"),
        (0.75, 0.70, "Software", "SUGGEST_TO_AGENT"),
        (0.50, 0.45, "Other", "ESCALATE_TO_AGENT"),
        (0.90, 0.85, "Security", "ESCALATE_TO_AGENT"),  # Security override
    ],
)
def test_routing_scenarios(model_conf, sim_score, category, expected_decision):
    """Test multiple routing scenarios"""
    result = confidence_service.compute(
        model_confidence=model_conf,
        similarity_score=sim_score,
        ticket_text="Test ticket",
        category=category,
        sentiment_label="NEUTRAL",
        sentiment_score=0.5,
        sla_breach_probability=0.3,
        user_tier="Standard",
    )

    assert result["routing_decision"] == expected_decision
