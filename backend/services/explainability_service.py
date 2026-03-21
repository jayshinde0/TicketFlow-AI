"""
services/explainability_service.py — LIME explanations for ticket classifications.
Uses LIME to explain which words drove the AI's category prediction.
"""

import asyncio
import numpy as np
from typing import List, Dict, Optional
from loguru import logger


class ExplainabilityService:
    """
    Generates LIME explanations for category classifier predictions.

    Uses LimeTextExplainer with the classifier's predict_proba method.
    Output is a list of (word, importance_weight) tuples, split into
    positive (supporting) and negative (opposing) features.
    """

    ALL_CATEGORIES = [
        "Network", "Auth", "Software", "Hardware", "Access",
        "Billing", "Email", "Security", "ServiceRequest", "Database"
    ]

    def __init__(self):
        self._explainer = None
        self._loaded = False

    def _load_explainer(self):
        """Lazy-load LIME text explainer."""
        if not self._loaded:
            try:
                from lime.lime_text import LimeTextExplainer
                self._explainer = LimeTextExplainer(
                    class_names=self.ALL_CATEGORIES
                )
                logger.info("LIME explainer initialized.")
            except ImportError:
                logger.warning("LIME not installed. pip install lime")
            self._loaded = True

    def explain(
        self,
        cleaned_text: str,
        classifier_service,   # injected to avoid circular import
        num_features: int = 8,
        num_samples: int = 300,  # reduced from 500 for speed
    ) -> Optional[dict]:
        """
        Generate LIME explanation for a ticket classification.

        Args:
            cleaned_text: Preprocessed ticket text.
            classifier_service: ClassifierService instance with predict_proba.
            num_features: Number of words to include in explanation.
            num_samples: LIME perturbation samples (higher = more accurate, slower).

        Returns:
            LIME explanation dict with positive and negative word features.
        """
        self._load_explainer()

        if self._explainer is None:
            return None

        try:
            # Run LIME explanation
            explanation = self._explainer.explain_instance(
                cleaned_text,
                classifier_service.predict_proba_for_lime,
                num_features=num_features,
                num_samples=num_samples,
            )

            # Get predicted class
            predicted_class_idx = np.argmax(
                classifier_service.predict_proba_for_lime([cleaned_text])[0]
            )
            predicted_class = self.ALL_CATEGORIES[
                min(predicted_class_idx, len(self.ALL_CATEGORIES) - 1)
            ]

            # Get explanation confidence for the predicted class
            exp_map = explanation.as_map()
            class_idx = list(exp_map.keys())[0] if exp_map else 0
            feature_weights = exp_map.get(class_idx, [])

            # Build feature name lookup
            feature_names = explanation.domain_mapper.indexed_string.word_list

            positive_features = []
            negative_features = []

            for feat_idx, weight in feature_weights:
                if feat_idx >= len(feature_names):
                    continue
                word = feature_names[feat_idx]
                feature = {"word": word, "weight": round(float(weight), 4)}
                if weight >= 0:
                    positive_features.append(feature)
                else:
                    negative_features.append(feature)

            # Sort by absolute weight
            positive_features.sort(key=lambda x: abs(x["weight"]), reverse=True)
            negative_features.sort(key=lambda x: abs(x["weight"]), reverse=True)

            # Explanation confidence = score of predicted class
            score_map = dict(explanation.local_pred if hasattr(explanation, "local_pred") else [])

            return {
                "predicted_class": predicted_class,
                "explanation_confidence": round(
                    float(
                        classifier_service.predict_proba_for_lime(
                            [cleaned_text]
                        )[0][predicted_class_idx]
                    ),
                    4,
                ),
                "top_positive_features": positive_features[:5],
                "top_negative_features": negative_features[:3],
            }

        except Exception as e:
            logger.warning(f"LIME explanation failed: {e}")
            return None

    async def explain_async(
        self,
        cleaned_text: str,
        classifier_service,
        num_features: int = 8,
        num_samples: int = 300,
    ) -> Optional[dict]:
        """Async wrapper — LIME is CPU-bound, run in thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.explain(
                cleaned_text, classifier_service, num_features, num_samples
            )
        )


# Module-level singleton
explainability_service = ExplainabilityService()
