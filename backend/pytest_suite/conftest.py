"""
conftest.py - Pytest configuration and shared fixtures
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


@pytest.fixture
def sample_tickets():
    """Sample tickets for testing"""
    return {
        "network": "Cannot connect to VPN. Getting timeout error 800.",
        "auth": "Forgot my password. Cannot login to system.",
        "security": "URGENT: Phishing email detected. Suspicious link clicked.",
        "database": "Database query taking 45 seconds. Performance issue.",
        "billing": "Charged twice for subscription. Need refund.",
        "software": "Application crashes when opening PDF files.",
        "hardware": "Laptop screen flickering. Display malfunction.",
        "email": "Emails not sending. SMTP timeout error.",
        "access": "Cannot access Finance folder. Permission denied.",
        "service_request": "Please setup new email account for John Doe.",
    }


@pytest.fixture
def nlp_features():
    """Sample NLP features for testing"""
    return {
        "word_count": 15,
        "char_count": 80,
        "urgency_keyword_count": 1,
        "question_mark_count": 0,
        "exclamation_mark_count": 1,
        "avg_word_length": 5.3,
        "sentence_count": 2,
    }


@pytest.fixture
def classification_result():
    """Sample classification result"""
    return {
        "category": "Network",
        "model_confidence": 0.92,
        "priority": "High",
        "priority_confidence": 0.85,
        "category_probabilities": {
            "Network": 0.92,
            "Software": 0.04,
            "Hardware": 0.02,
        },
    }


@pytest.fixture
def sentiment_result():
    """Sample sentiment analysis result"""
    return {
        "sentiment_label": "NEGATIVE",
        "sentiment_score": 0.23,
        "is_frustrated": True,
    }


@pytest.fixture
def confidence_thresholds():
    """Confidence thresholds from config"""
    return {
        "high": 0.85,
        "low": 0.60,
        "auto_resolve": 0.85,
        "suggest_to_agent": 0.65,
    }
