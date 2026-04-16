"""
ml/models/category_classifier.py — Logistic Regression category classifier.
Agent 1 of the TicketFlow pipeline.

Accepts pre-computed sparse feature matrices from FeatureEngineer.
TF-IDF vectorization is handled externally by FeatureEngineer.
"""

import joblib
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from loguru import logger

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    accuracy_score,
)

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


class CategoryClassifier:
    """
    Multinomial Logistic Regression for ticket category prediction.
    Accepts sparse feature matrices from FeatureEngineer (TF-IDF + scalars).
    C=5.0 gives sharper probability distributions than the default C=1.0.
    """

    def __init__(self):
        # Increased C from 5.0 to 10.0 for higher confidence predictions
        # Higher C = less regularization = more confident predictions
        self.classifier = LogisticRegression(
            C=10.0,
            max_iter=2000,
            class_weight="balanced",
            solver="lbfgs",
            multi_class="multinomial",
            random_state=42,
            n_jobs=-1,
        )
        self.classes_: Optional[np.ndarray] = None
        self._trained: bool = False
        self._feature_names: Optional[List[str]] = None

    def train(
        self,
        X_train,
        y_train: List[str],
        use_grid_search: bool = False,
    ) -> "CategoryClassifier":
        """
        Train on pre-computed sparse feature matrix from FeatureEngineer.

        Args:
            X_train:         Sparse matrix (n_samples, n_features).
            y_train:         Category label strings.
            use_grid_search: Run 5-fold CV over C values if True.
        """
        n_samples = X_train.shape[0]
        logger.info(
            f"Training CategoryClassifier on {n_samples} samples "
            f"(C=10.0, balanced, lbfgs)..."
        )

        if use_grid_search:
            logger.info(
                "Running 5-fold GridSearch over " "C: [1.0, 5.0, 10.0, 20.0, 50.0]..."
            )
            param_grid = {"C": [1.0, 5.0, 10.0, 20.0, 50.0]}
            base_clf = LogisticRegression(
                max_iter=2000,
                class_weight="balanced",
                solver="lbfgs",
                multi_class="multinomial",
                random_state=42,
                n_jobs=-1,
            )
            cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
            grid = GridSearchCV(
                base_clf,
                param_grid,
                cv=cv,
                scoring="f1_macro",
                n_jobs=-1,
                verbose=1,
            )
            grid.fit(X_train, y_train)
            self.classifier = grid.best_estimator_
            logger.info(
                f"Best C: {grid.best_params_['C']} | "
                f"CV Macro-F1: {grid.best_score_:.4f}"
            )
        else:
            self.classifier.fit(X_train, y_train)

        self.classes_ = self.classifier.classes_
        self._trained = True

        train_preds = self.classifier.predict(X_train)
        train_acc = float(np.mean(np.array(train_preds) == np.array(y_train)))
        logger.info(
            f"CategoryClassifier trained | "
            f"samples={n_samples} | "
            f"train_acc={train_acc:.4f} | "
            f"classes={list(self.classes_)}"
        )
        return self

    def set_feature_names(self, feature_names: List[str]) -> None:
        """Store TF-IDF feature names for get_top_features()."""
        self._feature_names = feature_names

    def predict(self, X) -> Tuple[str, float, Dict[str, float]]:
        """
        Predict category for a single sparse feature vector.

        Args:
            X: Sparse matrix shape (1, n_features) from FeatureEngineer.

        Returns:
            (predicted_category, confidence, prob_dict)
        """
        if not self._trained:
            raise RuntimeError("Not trained. Call train() or load() first.")

        probs = self.classifier.predict_proba(X)[0]
        predicted_idx = int(np.argmax(probs))
        predicted_class = str(self.classes_[predicted_idx])
        confidence = float(probs[predicted_idx])

        prob_dict: Dict[str, float] = {
            str(cls): round(float(p), 4)
            for cls, p in sorted(
                zip(self.classes_, probs),
                key=lambda x: x[1],
                reverse=True,
            )
        }
        return predicted_class, confidence, prob_dict

    def predict_proba_raw(self, X) -> np.ndarray:
        """
        Raw probability matrix for LIME.
        X: sparse or dense matrix (n_samples, n_features).
        """
        if not self._trained:
            raise RuntimeError("Not trained.")
        return self.classifier.predict_proba(X)

    def evaluate(self, X_test, y_test: List[str]) -> dict:
        """
        Evaluate on held-out sparse feature matrix.

        Args:
            X_test:  Sparse matrix from FeatureEngineer.
            y_test:  Ground-truth category labels.
        """
        if not self._trained:
            raise RuntimeError("Not trained.")

        y_pred = self.classifier.predict(X_test)
        y_arr = np.array(y_test)

        macro_f1 = float(f1_score(y_arr, y_pred, average="macro", zero_division=0))
        accuracy = float(accuracy_score(y_arr, y_pred))

        report = classification_report(
            y_arr,
            y_pred,
            target_names=ALL_CATEGORIES,
            output_dict=True,
            zero_division=0,
        )
        cm = confusion_matrix(y_arr, y_pred, labels=ALL_CATEGORIES)

        logger.info(f"Evaluation — Macro F1: {macro_f1:.4f} | Accuracy: {accuracy:.4f}")
        logger.info(f"{'Category':<18} {'Precision':>10} {'Recall':>8} {'F1':>8}")
        logger.info("-" * 50)
        for cat in ALL_CATEGORIES:
            if cat in report:
                r = report[cat]
                logger.info(
                    f"{cat:<18} {r['precision']:>10.3f} "
                    f"{r['recall']:>8.3f} {r['f1-score']:>8.3f}"
                )

        return {
            "macro_f1": round(macro_f1, 4),
            "accuracy": round(accuracy, 4),
            "per_category": {
                cat: {
                    "precision": round(report[cat]["precision"], 4),
                    "recall": round(report[cat]["recall"], 4),
                    "f1": round(report[cat]["f1-score"], 4),
                    "support": int(report[cat]["support"]),
                }
                for cat in ALL_CATEGORIES
                if cat in report
            },
            "confusion_matrix": cm.tolist(),
        }

    def get_top_features(self, category: str, n: int = 10) -> List[Tuple[str, float]]:
        """Top N important features for a category. Needs set_feature_names()."""
        if not self._trained or self._feature_names is None:
            return []
        try:
            cat_idx = list(self.classes_).index(category)
        except ValueError:
            return []
        coefs = self.classifier.coef_[cat_idx]
        feature_arr = np.array(self._feature_names)
        top_indices = np.argsort(coefs)[::-1][:n]
        return [(str(feature_arr[i]), round(float(coefs[i]), 4)) for i in top_indices]

    def get_all_top_features(self, n: int = 5) -> Dict[str, List[Tuple[str, float]]]:
        """Top N features for all categories. Used by ML dashboard."""
        return {cat: self.get_top_features(cat, n) for cat in ALL_CATEGORIES}

    def save(self, path: Optional[Path] = None) -> Path:
        """Save classifier to disk. TF-IDF saved separately by train.py."""
        save_path = Path(path) if path else (ARTIFACT_DIR / "category_model.pkl")
        save_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.classifier, save_path)
        logger.info(f"CategoryClassifier saved to {save_path}")
        return save_path

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "CategoryClassifier":
        """Load classifier from disk. TF-IDF loaded separately via FeatureEngineer."""
        load_path = Path(path) if path else (ARTIFACT_DIR / "category_model.pkl")
        if not load_path.exists():
            raise FileNotFoundError(
                f"No model at {load_path}. Run python -m ml.train first."
            )
        instance = cls()
        instance.classifier = joblib.load(load_path)
        instance.classes_ = instance.classifier.classes_
        instance._trained = True
        logger.info(
            f"CategoryClassifier loaded from {load_path} | "
            f"classes={list(instance.classes_)}"
        )
        return instance
