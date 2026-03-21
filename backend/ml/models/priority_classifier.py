"""
ml/models/priority_classifier.py — Random Forest priority prediction model.
Used by Agent 1 of the TicketFlow pipeline alongside CategoryClassifier.
"""

import joblib
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from loguru import logger

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder


ARTIFACT_DIR = Path(__file__).parent.parent / "artifacts"

ALL_PRIORITIES = ["Low", "Medium", "High", "Critical"]

# Default priority per category when model is unavailable
CATEGORY_DEFAULT_PRIORITY = {
    "Network":        "High",
    "Auth":           "High",
    "Software":       "Medium",
    "Hardware":       "Medium",
    "Access":         "Medium",
    "Billing":        "High",
    "Email":          "Medium",
    "Security":       "Critical",   # always critical
    "ServiceRequest": "Low",
    "Database":       "Critical",
}


class PriorityClassifier:
    """
    Random Forest Classifier for ticket priority prediction.

    Input features (combined matrix):
      - TF-IDF features from cleaned ticket text
      - user_tier_encoded (0=Free to 3=Enterprise)
      - submission_hour (0-23)
      - word_count
      - urgency_keyword_count
      - sentiment_score (0.0-1.0, higher=more negative)

    Output: predicted priority + confidence score
    """

    def __init__(self):
        self.classifier = RandomForestClassifier(
            n_estimators=200,
            class_weight="balanced",   # handle class imbalance
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        )
        self.label_encoder = LabelEncoder()
        self._trained = False
        self.classes_: Optional[np.ndarray] = None

    def train(
        self,
        X_train,
        y_train: List[str],
        # Security category override — always Critical
        security_mask: Optional[np.ndarray] = None,
    ) -> "PriorityClassifier":
        """
        Train the Random Forest priority classifier.

        Args:
            X_train: Feature matrix (sparse or dense).
            y_train: List of priority labels (Low/Medium/High/Critical).
            security_mask: Boolean array; Security tickets forced to Critical.

        Returns:
            self
        """
        y_encoded = self.label_encoder.fit_transform(y_train)
        self.classes_ = self.label_encoder.classes_

        logger.info(
            f"Training PriorityClassifier on {len(y_train)} samples | "
            f"Class distribution: "
            f"{dict(zip(*np.unique(y_train, return_counts=True)))}"
        )

        self.classifier.fit(X_train, y_encoded)
        self._trained = True

        # Compute feature importances
        self._feature_importances = self.classifier.feature_importances_
        logger.info(
            f"PriorityClassifier trained | OOB metric unavailable without oob_score=True"
        )
        return self

    def predict(
        self,
        X,
        category: Optional[str] = None,
    ) -> Tuple[str, float]:
        """
        Predict priority for a single sample.

        Security tickets are always forced to Critical regardless of model output.

        Args:
            X: Feature matrix shape (1, n_features).
            category: Predicted category (used for Security override).

        Returns:
            Tuple of (priority_label, confidence)
        """
        # Security override — never auto-predict below Critical
        if category == "Security":
            return "Critical", 1.0

        if not self._trained:
            # Fall back to category defaults
            default = CATEGORY_DEFAULT_PRIORITY.get(category, "Medium")
            logger.warning(
                f"PriorityClassifier not trained; using default: {default}"
            )
            return default, 0.5

        probs = self.classifier.predict_proba(X)[0]
        predicted_idx = np.argmax(probs)
        predicted_class = self.label_encoder.inverse_transform([predicted_idx])[0]
        confidence = float(probs[predicted_idx])

        return str(predicted_class), confidence

    def get_feature_importance(
        self,
        feature_names: Optional[List[str]] = None,
        top_n: int = 20
    ) -> List[Dict]:
        """
        Return top-N feature importances for the Random Forest model.

        Returns:
            List of {feature, importance} dicts sorted descending.
        """
        if not self._trained or not hasattr(self, "_feature_importances"):
            return []

        importances = self._feature_importances
        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(len(importances))]

        # Sort by importance descending
        pairs = sorted(
            zip(feature_names, importances),
            key=lambda x: x[1],
            reverse=True,
        )

        return [
            {"feature": name, "importance": round(float(imp), 6)}
            for name, imp in pairs[:top_n]
        ]

    def save(self, path: Optional[Path] = None) -> Path:
        """Persist model and label encoder to disk."""
        save_path = path or (ARTIFACT_DIR / "priority_model.pkl")
        save_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {"classifier": self.classifier, "label_encoder": self.label_encoder},
            save_path
        )
        logger.info(f"PriorityClassifier saved to {save_path}")
        return save_path

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "PriorityClassifier":
        """Load a previously saved model."""
        load_path = path or (ARTIFACT_DIR / "priority_model.pkl")
        if not load_path.exists():
            raise FileNotFoundError(
                f"No saved model at {load_path}. Run training first."
            )
        instance = cls()
        data = joblib.load(load_path)
        instance.classifier = data["classifier"]
        instance.label_encoder = data["label_encoder"]
        instance.classes_ = instance.label_encoder.classes_
        instance._trained = True
        logger.info(f"PriorityClassifier loaded from {load_path}")
        return instance
