"""
services/classifier_service.py — Agent 1: Category + Priority Classifier.

Loads pre-trained models and runs inference on cleaned ticket text.
Returns category, priority, confidence, and full probability distributions.
"""

import asyncio
import numpy as np
from typing import Optional
from pathlib import Path
from loguru import logger

from core.config import settings
from utils.text_cleaner import count_urgency_keywords


class ClassifierService:
    """
    Agent 1 of the TicketFlow pipeline.

    Responsibilities:
    - Load FeatureEngineer (TF-IDF + scalar features) from disk
    - Load CategoryClassifier (Logistic Regression) from disk
    - Load PriorityClassifier (Random Forest) from disk
    - Run inference on preprocessed ticket text
    - Return structured output with confidences

    Thread-safe; models loaded once on first use (lazy loading).
    """

    def __init__(self):
        self._feature_engineer = None
        self._category_clf = None
        self._priority_clf = None
        self._loaded = False
        self._artifact_dir = Path(__file__).parent.parent / "ml" / "artifacts"

    def _load_models(self):
        """Load all ML artifacts from disk. Called once lazily."""
        if self._loaded:
            return

        try:
            import joblib
            from ml.models.category_classifier import CategoryClassifier
            from ml.models.priority_classifier import PriorityClassifier

            tfidf_path = self._artifact_dir / "tfidf_vectorizer.pkl"
            if tfidf_path.exists():
                self._feature_engineer = joblib.load(tfidf_path)
                logger.info(f"FeatureEngineer loaded from {tfidf_path}")
            else:
                logger.warning(
                    f"TF-IDF vectorizer not found at {tfidf_path}. "
                    f"Run ml/train.py first."
                )

            cat_path = self._artifact_dir / "category_model.pkl"
            if cat_path.exists():
                self._category_clf = CategoryClassifier.load(cat_path)
            else:
                logger.warning("Category model not found. Using fallback.")

            pri_path = self._artifact_dir / "priority_model.pkl"
            if pri_path.exists():
                self._priority_clf = PriorityClassifier.load(pri_path)
            else:
                logger.warning("Priority model not found. Using fallback.")

            self._loaded = True

        except Exception as e:
            logger.error(f"Error loading classifier models: {e}")

    def _keyword_fallback_category(self, text: str) -> str:
        """
        Simple keyword-based category fallback when ML models are unavailable.
        Used during development before training is complete.
        """
        text_lower = text.lower()
        keyword_map = {
            "Network": [
                "vpn",
                "wifi",
                "internet",
                "ping",
                "dns",
                "firewall",
                "network",
                "connection",
            ],
            "Auth": [
                "password",
                "login",
                "locked",
                "otp",
                "2fa",
                "token",
                "sso",
                "authentication",
            ],
            "Security": [
                "phishing",
                "malware",
                "virus",
                "ransomware",
                "breach",
                "hack",
                "suspicious",
            ],
            "Database": [
                "database",
                "sql",
                "query",
                "server",
                "disk",
                "backup",
                "mysql",
                "postgres",
            ],
            "Billing": [
                "invoice",
                "payment",
                "charge",
                "refund",
                "subscription",
                "billing",
            ],
            "Software": [
                "crash",
                "error",
                "install",
                "update",
                "freeze",
                "exception",
                "bug",
            ],
            "Hardware": [
                "laptop",
                "screen",
                "keyboard",
                "printer",
                "battery",
                "usb",
                "monitor",
            ],
            "Email": [
                "email",
                "inbox",
                "attachment",
                "spam",
                "mailbox",
                "smtp",
                "calendar",
            ],
            "Access": [
                "access",
                "permission",
                "grant",
                "revoke",
                "role",
                "admin",
                "restricted",
            ],
            "ServiceRequest": [
                "request",
                "new",
                "setup",
                "provision",
                "create",
                "onboarding",
            ],
        }
        scores = {}
        for category, keywords in keyword_map.items():
            scores[category] = sum(1 for kw in keywords if kw in text_lower)

        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "Software"

    def classify(
        self,
        cleaned_text: str,
        user_tier: str = "Standard",
        submission_hour: int = 12,
        word_count: int = 20,
        urgency_keyword_count: Optional[int] = None,
        sentiment_score: float = 0.0,
    ) -> dict:
        """
        Run Agent 1 classification on a preprocessed ticket.

        Args:
            cleaned_text: spaCy-processed ticket text.
            user_tier: User's subscription tier (Free/Standard/Premium/Enterprise).
            submission_hour: Hour of day (0-23).
            word_count: Word count from original text.
            urgency_keyword_count: Override; calculated from text if None.
            sentiment_score: 0.0-1.0 negative sentiment score.

        Returns:
            Dict matching the Agent 1 output specification.
        """
        self._load_models()

        if urgency_keyword_count is None:
            urgency_keyword_count = count_urgency_keywords(cleaned_text)

        # ── Build feature matrix ──────────────────────────────────────
        if self._feature_engineer and self._category_clf:
            import pandas as pd

            meta = pd.DataFrame(
                [
                    {
                        "user_tier": user_tier,
                        "submission_hour": submission_hour,
                        "submission_day": 0,
                    }
                ]
            )
            X = self._feature_engineer.transform([cleaned_text], meta)

            # ── Category prediction ──────────────────────────────────
            category, model_confidence, category_probs = self._category_clf.predict(X)

            # ── Priority prediction ──────────────────────────────────
            if self._priority_clf:
                priority, priority_confidence = self._priority_clf.predict(
                    X, category=category
                )
            else:
                priority = settings.DOMAIN_KEYWORDS and "Medium"
                priority_confidence = 0.5

        else:
            # Fallback when models not yet trained
            category = self._keyword_fallback_category(cleaned_text)
            model_confidence = 0.65  # moderate confidence for keyword fallback
            category_probs = {category: 0.65}
            priority = "Medium"
            priority_confidence = 0.5

        # ── Security always Critical ──────────────────────────────────
        if category == "Security":
            priority = "Critical"
            priority_confidence = 1.0

        return {
            "category": category,
            "category_probabilities": category_probs,
            "model_confidence": round(float(model_confidence), 4),
            "priority": priority,
            "priority_confidence": round(float(priority_confidence), 4),
        }

    async def classify_async(self, cleaned_text: str, **kwargs) -> dict:
        """Async wrapper for classify() — runs in thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self.classify(cleaned_text, **kwargs)
        )

    def predict_proba_for_lime(self, texts: list) -> np.ndarray:
        """
        Raw probability predictions for LIME explain_instance().
        Accepts a list of texts (LIME's API requirement).

        Returns:
            np.ndarray shape (n_texts, n_classes)
        """
        self._load_models()
        if not (self._feature_engineer and self._category_clf):
            n_classes = len(settings.DOMAIN_KEYWORDS)
            return np.full((len(texts), n_classes), 1.0 / n_classes)

        X = self._feature_engineer.transform(texts)
        return self._category_clf.predict_proba_raw(X)


# Module-level singleton
classifier_service = ClassifierService()
