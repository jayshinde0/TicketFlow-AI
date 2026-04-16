"""
ml/models/sla_predictor.py — Random Forest SLA breach prediction model.
Predicts probability that a ticket will breach its SLA deadline.
"""

import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
from loguru import logger

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
from scipy.sparse import hstack, csr_matrix

ARTIFACT_DIR = Path(__file__).parent.parent / "artifacts"

ALL_CATEGORIES = [
    "Network",
    "Auth",
    "Software",
    "Hardware",
    "Access",
    "Billing",
    "Email",
    "Security",
    "ServiceRequest",
    "Database",
]

# ─── SLA limit lookup (minutes) ───────────────────────────────────────
# category → priority → minutes before breach
SLA_MINUTES = {
    "Network": {"Low": 2880, "Medium": 480, "High": 120, "Critical": 30},
    "Auth": {"Low": 1440, "Medium": 240, "High": 60, "Critical": 15},
    "Software": {"Low": 4320, "Medium": 1440, "High": 240, "Critical": 60},
    "Hardware": {"Low": 4320, "Medium": 1440, "High": 240, "Critical": 120},
    "Access": {"Low": 2880, "Medium": 480, "High": 120, "Critical": 30},
    "Billing": {"Low": 2880, "Medium": 1440, "High": 240, "Critical": 60},
    "Email": {"Low": 2880, "Medium": 480, "High": 120, "Critical": 60},
    "Security": {"Low": 30, "Medium": 30, "High": 30, "Critical": 5},
    "ServiceRequest": {"Low": 2880, "Medium": 480, "High": 120, "Critical": 30},
    "Database": {"Low": 1440, "Medium": 240, "High": 60, "Critical": 5},
}


def get_sla_minutes(category: str, priority: str) -> int:
    """Return SLA limit in minutes for given category+priority combination."""
    cat_limits = SLA_MINUTES.get(category, SLA_MINUTES["Software"])
    return cat_limits.get(priority, 240)  # 4 hours default


class SLAPredictor:
    """
    Random Forest binary classifier:
      1 = ticket will breach SLA
      0 = ticket will be resolved within SLA

    Features (11 total):
      - category_encoded (one-hot, 10 dims)
      - priority_encoded (ordinal 0-3)
      - user_tier_encoded (ordinal 0-3)
      - submission_hour (0-23)
      - submission_day_of_week (0-6)
      - word_count
      - urgency_keyword_count
      - sentiment_score (0.0-1.0, higher=more negative)
      - current_queue_length (at submission time)
      - similar_ticket_avg_resolution_hours (from ChromaDB)
      - is_weekend (binary)
      - is_outside_business_hours (binary)
    """

    def __init__(self):
        self.classifier = RandomForestClassifier(
            n_estimators=200,
            class_weight="balanced",
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        )
        self.category_encoder = OneHotEncoder(
            categories=[ALL_CATEGORIES],
            handle_unknown="ignore",
            sparse_output=True,
        )
        self._trained = False

    def _build_feature_matrix(self, tickets: List[Dict]) -> csr_matrix:
        """
        Build the (n_samples, n_features) feature matrix from ticket dicts.

        Each dict should have keys:
            category, priority, user_tier, submission_hour,
            submission_day_of_week, word_count, urgency_keyword_count,
            sentiment_score, current_queue_length,
            similar_ticket_avg_resolution_hours
        """
        from utils.helpers import tier_to_int, priority_to_int

        categories = [[t.get("category", "Software")] for t in tickets]
        cat_encoded = self.category_encoder.transform(categories)

        scalar_rows = []
        for t in tickets:
            hour = int(t.get("submission_hour", 12))
            day = int(t.get("submission_day_of_week", 0))
            row = [
                priority_to_int(t.get("priority", "Medium")),
                tier_to_int(t.get("user_tier", "Standard")),
                hour,
                day,
                int(t.get("word_count", 20)),
                int(t.get("urgency_keyword_count", 0)),
                float(t.get("sentiment_score", 0.0)),
                int(t.get("current_queue_length", 5)),
                float(t.get("similar_ticket_avg_resolution_hours", 2.0)),
                int(day >= 5),  # is_weekend
                int(hour < 8 or hour >= 18),  # is_outside_business_hours
            ]
            scalar_rows.append(row)

        scalar_matrix = csr_matrix(np.array(scalar_rows, dtype=np.float32))
        return hstack([cat_encoded, scalar_matrix])

    def train(
        self,
        tickets: List[Dict],
        labels: List[int],  # 1=breach, 0=no breach
    ) -> "SLAPredictor":
        """
        Train SLA breach predictor.

        Args:
            tickets: List of ticket feature dicts.
            labels: Binary SLA breach labels (1=breached, 0=ok).

        Returns:
            self
        """
        logger.info(
            f"Training SLAPredictor on {len(tickets)} samples | "
            f"Breach rate: {sum(labels)/len(labels):.1%}"
        )

        # Fit category encoder first
        self.category_encoder.fit([[t.get("category", "Software")] for t in tickets])

        X = self._build_feature_matrix(tickets)
        self.classifier.fit(X, labels)
        self._trained = True

        logger.info("SLAPredictor training complete.")
        return self

    def predict_breach_probability(self, ticket: Dict) -> float:
        """
        Predict the probability that a ticket will breach its SLA.

        Security tickets always get high breach probability (treated as urgent).

        Args:
            ticket: Feature dict with all required keys.

        Returns:
            Float 0.0-1.0 indicating breach probability.
        """
        # Security is always treated as imminent SLA risk
        if ticket.get("category") == "Security":
            return 0.95

        if not self._trained:
            # Heuristic fallback based on priority
            priority_risk = {
                "Critical": 0.85,
                "High": 0.55,
                "Medium": 0.30,
                "Low": 0.10,
            }
            return priority_risk.get(ticket.get("priority", "Medium"), 0.30)

        X = self._build_feature_matrix([ticket])
        proba = self.classifier.predict_proba(X)[0]

        # Class 1 = breach; handle case where class_1 might be index 0 or 1
        classes = list(self.classifier.classes_)
        if 1 in classes:
            breach_prob = float(proba[classes.index(1)])
        else:
            breach_prob = float(proba[-1])

        return round(breach_prob, 4)

    def estimate_resolution_hours(
        self,
        category: str,
        priority: str,
        breach_probability: float,
    ) -> float:
        """
        Estimate realistic resolution time in hours.
        Adjusts upward when breach risk is high.
        """
        sla_minutes = get_sla_minutes(category, priority)
        base_hours = sla_minutes / 60 * 0.6  # typically resolved at 60% of SLA

        # If breach is likely, expected resolution exceeds SLA
        if breach_probability > 0.75:
            return round(base_hours * 1.6, 1)
        elif breach_probability > 0.50:
            return round(base_hours * 1.2, 1)
        return round(base_hours, 1)

    def save(self, path: Optional[Path] = None) -> Path:
        """Save model and encoder to disk."""
        save_path = path or (ARTIFACT_DIR / "sla_model.pkl")
        save_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "classifier": self.classifier,
                "category_encoder": self.category_encoder,
            },
            save_path,
        )
        logger.info(f"SLAPredictor saved to {save_path}")
        return save_path

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "SLAPredictor":
        """Load a previously saved SLA predictor."""
        load_path = path or (ARTIFACT_DIR / "sla_model.pkl")
        if not load_path.exists():
            raise FileNotFoundError(
                f"No saved model at {load_path}. Run training first."
            )
        instance = cls()
        data = joblib.load(load_path)
        instance.classifier = data["classifier"]
        instance.category_encoder = data["category_encoder"]
        instance._trained = True
        logger.info(f"SLAPredictor loaded from {load_path}")
        return instance
