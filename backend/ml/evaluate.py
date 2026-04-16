"""
ml/evaluate.py — Model evaluation script for TicketFlow AI.

Run with: python -m ml.evaluate

Generates:
  - Classification report per domain
  - Confusion matrix (prints + saves JSON)
  - Calibration curve data
  - AUC-ROC for SLA predictor
  - Feature importance top-15
"""

import sys
import json
import numpy as np
from pathlib import Path
from loguru import logger
from sklearn.metrics import classification_report

sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.data_loader import load_training_data, train_val_test_split, ALL_CATEGORIES
from ml.feature_engineering import FeatureEngineer
from ml.models.category_classifier import CategoryClassifier
from ml.models.priority_classifier import PriorityClassifier
from ml.models.sla_predictor import SLAPredictor
from ml.train import (
    preprocess_texts,
    build_sla_feature_dicts,
    generate_synthetic_sla_labels,
)
from utils.metrics import (
    compute_confusion_matrix,
    compute_expected_calibration_error,
    compute_sla_auc,
    metrics_at_threshold,
)
import joblib
import numpy as np

ARTIFACT_DIR = Path(__file__).parent / "artifacts"
TFIDF_PATH = ARTIFACT_DIR / "tfidf_vectorizer.pkl"


def evaluate_category_model() -> dict:
    """Full evaluation of the Category Classifier on held-out test set."""
    logger.info("Loading data and models for evaluation...")

    df = load_training_data(use_synthetic=True)
    _, _, test_df = train_val_test_split(df)

    X_test_text = preprocess_texts(test_df["text"])
    y_test = test_df["category"].tolist()

    if not TFIDF_PATH.exists():
        raise FileNotFoundError(f"Run ml/train.py first. Missing: {TFIDF_PATH}")

    fe: FeatureEngineer = joblib.load(TFIDF_PATH)
    X_test = fe.transform(X_test_text)

    cat_clf = CategoryClassifier.load()

    # Classification report
    y_pred = cat_clf.classifier.predict(X_test)
    report = classification_report(
        y_test, y_pred, target_names=ALL_CATEGORIES, output_dict=True
    )

    logger.info("Category Classifier — Per-domain Test Results:")
    logger.info(
        f"{'Domain':20s} {'Precision':>10s} {'Recall':>8s} {'F1':>8s} {'Support':>8s}"
    )
    logger.info("─" * 60)
    for cat in ALL_CATEGORIES:
        m = report.get(cat, {})
        logger.info(
            f"{cat:20s} {m.get('precision', 0):>10.3f} "
            f"{m.get('recall', 0):>8.3f} "
            f"{m.get('f1-score', 0):>8.3f} "
            f"{m.get('support', 0):>8}"
        )
    logger.info("─" * 60)
    logger.info(
        f"{'Macro Average':20s} "
        f"{report['macro avg']['precision']:>10.3f} "
        f"{report['macro avg']['recall']:>8.3f} "
        f"{report['macro avg']['f1-score']:>8.3f}"
    )

    # Confusion matrix
    cm_data = compute_confusion_matrix(y_test, y_pred, ALL_CATEGORIES)

    # Calibration curve
    y_proba = cat_clf.classifier.predict_proba(X_test)
    y_pred_array = cat_clf.classifier.predict(X_test)
    correct = np.array([int(p == t) for p, t in zip(y_pred_array, y_test)])
    max_conf = y_proba.max(axis=1)
    ece, calibration_data = compute_expected_calibration_error(max_conf, correct)
    logger.info(f"Expected Calibration Error (ECE): {ece:.4f}")

    # Feature importance
    top_features = fe.get_top_features_per_class(
        cat_clf.classifier, ALL_CATEGORIES, top_n=15
    )

    return {
        "classification_report": report,
        "confusion_matrix": cm_data,
        "calibration": calibration_data,
        "ece": ece,
        "top_features_per_class": top_features,
    }


def evaluate_sla_model() -> dict:
    """Evaluate SLA breach predictor."""
    df = load_training_data(use_synthetic=True)
    _, _, test_df = train_val_test_split(df)

    rng = np.random.default_rng(99)
    test_queues = rng.integers(1, 50, size=len(test_df))
    test_sla_dicts = build_sla_feature_dicts(test_df, test_queues)
    test_labels = generate_synthetic_sla_labels(test_df)

    try:
        sla_clf = SLAPredictor.load()
    except FileNotFoundError:
        logger.warning("SLA model not found. Run training first.")
        return {}

    probs = np.array([sla_clf.predict_breach_probability(t) for t in test_sla_dicts])

    auc_data = compute_sla_auc(test_labels, probs)
    threshold_metrics = metrics_at_threshold(test_labels, probs, threshold=0.70)

    logger.info(f"SLA AUC-ROC: {auc_data['auc_roc']:.4f}")
    logger.info(f"SLA @ 0.70 threshold: {threshold_metrics}")

    return {**auc_data, "metrics_at_threshold": threshold_metrics}


def save_evaluation_results(eval_results: dict, sla_results: dict) -> None:
    """Save evaluation results as JSON for API serving."""
    output = {
        "category_model": eval_results,
        "sla_model": sla_results,
    }
    out_path = ARTIFACT_DIR / "evaluation_results.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    logger.info(f"Evaluation results saved to {out_path}")


if __name__ == "__main__":
    logger.info("═══ TicketFlow AI Model Evaluation ═══")
    cat_results = evaluate_category_model()
    sla_results = evaluate_sla_model()
    save_evaluation_results(cat_results, sla_results)
    logger.info("Evaluation complete.")
