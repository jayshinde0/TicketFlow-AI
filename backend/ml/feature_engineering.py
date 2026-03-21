"""
ml/feature_engineering.py — TF-IDF pipeline and extra feature extraction.
Produces the joint feature matrix used by all classifiers.
"""

import numpy as np
import pandas as pd
from typing import List, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from scipy.sparse import hstack, csr_matrix
from loguru import logger

from utils.text_cleaner import extract_text_features
from utils.helpers import tier_to_int, priority_to_int


# ─── TF-IDF configuration ─────────────────────────────────────────────
TFIDF_PARAMS = {
    "max_features": 10_000,
    "ngram_range": (1, 2),
    "sublinear_tf": True,       # log-scale TF, helps with frequent terms
    "min_df": 2,                # ignore terms appearing in < 2 docs
    "max_df": 0.95,             # ignore terms appearing in > 95% docs
    "strip_accents": "unicode",
    "analyzer": "word",
    "token_pattern": r"(?u)\b\w\w+\b",  # at least 2-char words
}


class FeatureEngineer:
    """
    Builds the feature matrix:
      - TF-IDF on cleaned text (sparse, 10k dims)
      - Scalar features: word_count, urgency_keywords, etc. (dense)
    
    Fit on training data; transform on validation/test/inference.
    """

    def __init__(self):
        self.tfidf = TfidfVectorizer(**TFIDF_PARAMS)
        self.scaler = StandardScaler()
        self._fitted = False

    def _build_scalar_features(
        self,
        texts: List[str],
        metadata: Optional[pd.DataFrame] = None,
    ) -> np.ndarray:
        """
        Build the dense scalar feature matrix from text + optional metadata.

        Scalar features:
          From text: word_count, char_count, question_mark_count,
                     exclamation_count, all_caps_word_count,
                     urgency_keyword_count, avg_word_length, sentence_count
          From metadata (if provided):
                     user_tier_int, submission_hour, submission_day,
                     is_weekend, is_outside_business_hours

        Returns:
            np.ndarray of shape (n_samples, n_scalar_features)
        """
        rows = []
        for i, text in enumerate(texts):
            features = extract_text_features(text)
            row = [
                features["word_count"],
                features["char_count"],
                features["question_mark_count"],
                features["exclamation_count"],
                features["all_caps_word_count"],
                features["urgency_keyword_count"],
                features["avg_word_length"],
                features["sentence_count"],
            ]

            # Add metadata features if available
            if metadata is not None and i < len(metadata):
                meta_row = metadata.iloc[i]
                tier = meta_row.get("user_tier", "Standard")
                hour = int(meta_row.get("submission_hour", 12))
                day = int(meta_row.get("submission_day", 0))

                row += [
                    tier_to_int(tier),
                    hour,
                    day,
                    int(day >= 5),                    # is_weekend
                    int(hour < 8 or hour >= 18),      # outside business hours
                ]
            else:
                row += [1, 12, 0, 0, 0]  # defaults

            rows.append(row)

        return np.array(rows, dtype=np.float32)

    def fit(
        self,
        texts: List[str],
        metadata: Optional[pd.DataFrame] = None
    ) -> "FeatureEngineer":
        """Fit TF-IDF and scalar scaler on training data."""
        logger.info("Fitting TF-IDF vectorizer...")
        self.tfidf.fit(texts)

        scalar = self._build_scalar_features(texts, metadata)
        logger.info(f"Fitting scaler on {scalar.shape[1]} scalar features...")
        self.scaler.fit(scalar)

        self._fitted = True
        logger.info(
            f"FeatureEngineer fitted. "
            f"Vocab size: {len(self.tfidf.vocabulary_)}"
        )
        return self

    def transform(
        self,
        texts: List[str],
        metadata: Optional[pd.DataFrame] = None
    ) -> csr_matrix:
        """
        Transform texts into the joint feature matrix.

        Returns:
            Sparse matrix of shape (n_samples, 10000 + n_scalar)
        """
        if not self._fitted:
            raise RuntimeError("FeatureEngineer must be fitted before transform")

        tfidf_features = self.tfidf.transform(texts)
        scalar = self._build_scalar_features(texts, metadata)
        scalar_scaled = self.scaler.transform(scalar)

        # Horizontally stack sparse TF-IDF + dense scalar
        return hstack([tfidf_features, csr_matrix(scalar_scaled)])

    def fit_transform(
        self,
        texts: List[str],
        metadata: Optional[pd.DataFrame] = None
    ) -> csr_matrix:
        """Fit and transform in one step (for training)."""
        return self.fit(texts, metadata).transform(texts, metadata)

    def get_feature_names(self) -> List[str]:
        """Return all feature names (TF-IDF vocab + scalar names)."""
        tfidf_names = self.tfidf.get_feature_names_out().tolist()
        scalar_names = [
            "word_count", "char_count", "question_marks",
            "exclamations", "all_caps_words", "urgency_keywords",
            "avg_word_length", "sentence_count",
            "user_tier", "submission_hour", "submission_day",
            "is_weekend", "is_outside_hours",
        ]
        return tfidf_names + scalar_names

    def get_top_features_per_class(
        self,
        classifier,
        class_names: List[str],
        top_n: int = 15
    ) -> dict:
        """
        Extract top-N most important TF-IDF features per class.
        Works with LogisticRegression (coef_) classifiers.

        Returns:
            Dict mapping class_name → list of {feature, importance} dicts.
        """
        if not hasattr(classifier, "coef_"):
            return {}

        feature_names = self.get_feature_names()
        result = {}

        for i, class_name in enumerate(class_names):
            if i >= len(classifier.coef_):
                break
            coefs = classifier.coef_[i]
            top_indices = np.argsort(coefs)[::-1][:top_n]
            result[class_name] = [
                {
                    "feature": feature_names[idx],
                    "importance": round(float(coefs[idx]), 4)
                }
                for idx in top_indices
            ]

        return result
