"""
test_sla_service.py - Test SLA prediction and deadline calculation
Tests SLA time limits, breach prediction, and urgency levels
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.sla_service import sla_service


class TestSLALookup:
    """Test SLA time limit lookups"""

    def test_security_critical_sla(self):
        """Security + Critical should have shortest SLA (5 minutes)"""
        sla_minutes = sla_service.get_sla_minutes("Security", "Critical")
        assert sla_minutes == 5

    def test_network_high_sla(self):
        """Network + High should have 120 minutes SLA"""
        sla_minutes = sla_service.get_sla_minutes("Network", "High")
        assert sla_minutes == 120

    def test_software_low_sla(self):
        """Software + Low should have longest SLA (4320 minutes = 3 days)"""
        sla_minutes = sla_service.get_sla_minutes("Software", "Low")
        assert sla_minutes == 4320

    def test_database_critical_sla(self):
        """Database + Critical should have 5 minutes SLA"""
        sla_minutes = sla_service.get_sla_minutes("Database", "Critical")
        assert sla_minutes == 5

    def test_unknown_category_default(self):
        """Unknown category should return default SLA"""
        sla_minutes = sla_service.get_sla_minutes("UnknownCategory", "Medium")
        assert sla_minutes > 0  # Should have some default


class TestSLADeadlineCalculation:
    """Test SLA deadline timestamp calculation"""

    def test_deadline_calculation_network_high(self):
        """Test deadline calculation for Network + High (120 min)"""
        created_at = datetime(2026, 7, 30, 10, 0, 0, tzinfo=timezone.utc)
        info = sla_service.get_sla_info("Network", "High", created_at)

        expected_deadline = created_at + timedelta(minutes=120)
        assert info["sla_deadline"] == expected_deadline
        assert info["sla_minutes"] == 120

    def test_deadline_calculation_security_critical(self):
        """Test deadline calculation for Security + Critical (5 min)"""
        created_at = datetime(2026, 7, 30, 14, 30, 0, tzinfo=timezone.utc)
        info = sla_service.get_sla_info("Security", "Critical", created_at)

        expected_deadline = created_at + timedelta(minutes=5)
        assert info["sla_deadline"] == expected_deadline
        assert info["sla_minutes"] == 5

    def test_minutes_remaining_not_breached(self):
        """Test minutes remaining when not breached"""
        # Ticket created 30 minutes ago
        created_at = datetime.now(timezone.utc) - timedelta(minutes=30)
        info = sla_service.get_sla_info("Network", "High", created_at)

        # Should have ~90 minutes left (120 - 30)
        assert info["minutes_remaining"] > 80
        assert info["is_breached"] == False

    def test_sla_already_breached(self):
        """Test detection of already breached SLA"""
        # Ticket created 3 hours ago
        created_at = datetime.now(timezone.utc) - timedelta(hours=3)
        info = sla_service.get_sla_info("Network", "High", created_at)

        # SLA is 120 minutes, should be breached
        assert info["is_breached"] == True
        assert info["minutes_remaining"] < 0


class TestUrgencyLevels:
    """Test urgency level calculation"""

    def test_urgency_ok(self):
        """Test OK urgency level (>50% time remaining)"""
        # Ticket just created
        created_at = datetime.now(timezone.utc)
        info = sla_service.get_sla_info("Software", "Low", created_at)

        # Just created, plenty of time
        assert info["urgency_level"] == "ok"

    def test_urgency_warning(self):
        """Test WARNING urgency level (20-50% time remaining)"""
        # Network High = 120 minutes SLA
        # Create ticket 80 minutes ago (40 minutes left = 33%)
        created_at = datetime.now(timezone.utc) - timedelta(minutes=80)
        info = sla_service.get_sla_info("Network", "High", created_at)

        assert info["urgency_level"] in ["warning", "critical"]

    def test_urgency_critical(self):
        """Test CRITICAL urgency level (<20% time remaining)"""
        # Network High = 120 minutes SLA
        # Create ticket 110 minutes ago (10 minutes left = 8%)
        created_at = datetime.now(timezone.utc) - timedelta(minutes=110)
        info = sla_service.get_sla_info("Network", "High", created_at)

        assert info["urgency_level"] == "critical"


class TestBreachProbability:
    """Test SLA breach probability prediction"""

    def test_low_breach_probability(self):
        """Test low breach probability for simple, low-priority tickets"""
        prob = sla_service.predict_breach_probability(
            category="Software",
            priority="Low",
            user_tier="Standard",
            submission_hour=10,
            submission_day=2,  # Wednesday
            word_count=15,
            urgency_keyword_count=0,
            sentiment_score=0.6,  # Positive
            current_queue_length=3,
            similar_ticket_avg_hours=1.5,
        )

        assert 0.0 <= prob <= 1.0
        assert prob < 0.5  # Should be low risk

    def test_high_breach_probability(self):
        """Test high breach probability for complex, urgent tickets"""
        prob = sla_service.predict_breach_probability(
            category="Security",
            priority="Critical",
            user_tier="Premium",
            submission_hour=22,  # Late night (after hours)
            submission_day=6,  # Sunday
            word_count=150,  # Long description
            urgency_keyword_count=5,
            sentiment_score=0.2,  # Frustrated
            current_queue_length=25,  # Long queue
            similar_ticket_avg_hours=8.0,  # Historically slow
        )

        assert 0.0 <= prob <= 1.0
        assert prob > 0.5  # Should be high risk

    def test_breach_probability_medium_case(self):
        """Test medium breach probability"""
        prob = sla_service.predict_breach_probability(
            category="Network",
            priority="Medium",
            user_tier="Standard",
            submission_hour=14,
            submission_day=3,
            word_count=50,
            urgency_keyword_count=2,
            sentiment_score=0.5,
            current_queue_length=10,
            similar_ticket_avg_hours=2.5,
        )

        assert 0.0 <= prob <= 1.0
        # Should be moderate risk
        assert 0.2 <= prob <= 0.8


class TestSLAMatrix:
    """Test complete SLA matrix coverage"""

    @pytest.mark.parametrize(
        "category,priority,expected_range",
        [
            ("Security", "Critical", (1, 10)),
            ("Database", "High", (30, 120)),
            ("Network", "Medium", (240, 600)),
            ("Software", "Low", (2880, 5000)),
        ],
    )
    def test_sla_matrix_values(self, category, priority, expected_range):
        """Test SLA values are within expected ranges"""
        sla_minutes = sla_service.get_sla_minutes(category, priority)
        min_expected, max_expected = expected_range
        assert min_expected <= sla_minutes <= max_expected


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_future_created_at(self):
        """Test handling of future timestamp"""
        # Ticket "created" 1 hour in the future (clock skew)
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        info = sla_service.get_sla_info("Network", "High", future_time)

        # Should handle gracefully, not crash
        assert "sla_deadline" in info
        assert "minutes_remaining" in info

    def test_very_old_ticket(self):
        """Test handling of very old ticket"""
        # Ticket created 1 year ago
        old_time = datetime.now(timezone.utc) - timedelta(days=365)
        info = sla_service.get_sla_info("Software", "Low", old_time)

        # Should be breached
        assert info["is_breached"] == True
        assert info["minutes_remaining"] < 0

    def test_invalid_priority(self):
        """Test handling of invalid priority"""
        # Should not crash, should use default
        try:
            sla_minutes = sla_service.get_sla_minutes("Network", "InvalidPriority")
            assert sla_minutes > 0
        except Exception as e:
            # Or should raise clear error
            assert "Invalid" in str(e) or "priority" in str(e).lower()

    def test_zero_queue_length(self):
        """Test breach prediction with zero queue"""
        prob = sla_service.predict_breach_probability(
            category="Network",
            priority="Medium",
            user_tier="Standard",
            submission_hour=10,
            submission_day=2,
            word_count=20,
            urgency_keyword_count=1,
            sentiment_score=0.5,
            current_queue_length=0,  # Empty queue
            similar_ticket_avg_hours=1.0,
        )

        # Empty queue should lower breach probability
        assert prob < 0.5


class TestTimeRemaining:
    """Test time remaining calculations"""

    def test_full_time_remaining(self):
        """Test just-created ticket has full time remaining"""
        created_at = datetime.now(timezone.utc)
        info = sla_service.get_sla_info("Network", "High", created_at)

        # Should have close to full SLA time (120 minutes)
        assert info["minutes_remaining"] >= 119
        assert info["minutes_remaining"] <= 121

    def test_half_time_remaining(self):
        """Test ticket with half time elapsed"""
        # Network High = 120 minutes, create 60 minutes ago
        created_at = datetime.now(timezone.utc) - timedelta(minutes=60)
        info = sla_service.get_sla_info("Network", "High", created_at)

        # Should have ~60 minutes remaining
        assert 55 <= info["minutes_remaining"] <= 65

    def test_time_remaining_calculation_accuracy(self):
        """Test accuracy of time remaining calculation"""
        # Create ticket exactly 30 minutes ago
        created_at = datetime.now(timezone.utc) - timedelta(minutes=30)
        info = sla_service.get_sla_info("Network", "High", created_at)

        # Should have 90 minutes remaining (120 - 30)
        # Allow 1 minute tolerance for test execution time
        assert 89 <= info["minutes_remaining"] <= 91
