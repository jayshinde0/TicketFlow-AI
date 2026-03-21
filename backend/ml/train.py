"""
ml/train.py — Complete training pipeline for all TicketFlow AI models.

Run with: python -m ml.train --skip-grid-search
"""

import sys
import os
import argparse
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from loguru import logger

# ── Ensure output is visible immediately ──────────────────────────────
logger.remove()
logger.add(sys.stdout, format="{time:HH:mm:ss} | {level} | {message}",
           level="DEBUG", colorize=False)

# Add backend root to python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.data_loader import (
    load_training_data,
    train_val_test_split,
    ALL_CATEGORIES,
    ALL_PRIORITIES,
)
from ml.feature_engineering import FeatureEngineer
from ml.models.category_classifier import CategoryClassifier
from ml.models.priority_classifier import PriorityClassifier
from ml.models.sla_predictor import SLAPredictor
from utils.text_cleaner import basic_clean, count_urgency_keywords
from utils.helpers import tier_to_int

import joblib

ARTIFACT_DIR = Path(__file__).parent / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def preprocess_texts(texts: pd.Series) -> list:
    """Apply basic_clean + lowercase to all texts."""
    logger.info(f"Preprocessing {len(texts)} texts...")
    cleaned = [basic_clean(str(t)).lower() for t in texts]
    logger.info("Text preprocessing complete.")
    return cleaned


def generate_synthetic_sla_labels(df: pd.DataFrame) -> np.ndarray:
    """Generate SLA breach labels from synthetic/training data."""
    rng = np.random.default_rng(42)
    labels = []
    breach_rates = {
        "Critical": 0.60, "High": 0.35,
        "Medium": 0.15, "Low": 0.05
    }
    for _, row in df.iterrows():
        category = row.get("category", "Software")
        priority = row.get("priority", "Medium")
        rate = 0.80 if category == "Security" else breach_rates.get(priority, 0.20)
        labels.append(int(rng.random() < rate))
    return np.array(labels)


def build_sla_feature_dicts(df: pd.DataFrame,
                             queue_lengths: np.ndarray) -> list:
    """Build per-ticket dicts for SLA feature matrix."""
    dicts = []
    rng = np.random.default_rng(0)
    for i, (_, row) in enumerate(df.iterrows()):
        text = str(row.get("text", ""))
        dicts.append({
            "category":           row.get("category", "Software"),
            "priority":           row.get("priority", "Medium"),
            "user_tier":          rng.choice(["Free","Standard","Premium","Enterprise"]),
            "submission_hour":    int(rng.integers(0, 24)),
            "submission_day_of_week": int(rng.integers(0, 7)),
            "word_count":         len(text.split()),
            "urgency_keyword_count": count_urgency_keywords(text),
            "sentiment_score":    float(rng.uniform(0.1, 0.9)),
            "current_queue_length": int(queue_lengths[i]),
            "similar_ticket_avg_resolution_hours": float(rng.uniform(0.5, 12.0)),
        })
    return dicts


def train_all_models(
    data_dir: str = None,
    use_grid_search: bool = True,
    skip_sla: bool = False,
    feedback_docs: list = None,
) -> dict:
    """
    Full training pipeline. Returns dict of evaluation metrics.
    """
    from sklearn.metrics import (
        classification_report, f1_score,
        precision_score, recall_score
    )

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    logger.info(f"═══ TicketFlow AI Training Run: {run_id} ═══")

    # ── Step 1: Load data ─────────────────────────────────────────────
    logger.info("Step 1/6 — Loading training data...")
    df = load_training_data(data_dir=data_dir, use_synthetic=True)
    logger.info(f"Total samples loaded: {len(df)}")

    # ── Step 2: Split ─────────────────────────────────────────────────
    logger.info("Step 2/6 — Stratified 70/15/15 split...")
    train_df, val_df, test_df = train_val_test_split(df)

    # ── Step 3: Preprocess ────────────────────────────────────────────
    logger.info("Step 3/6 — Preprocessing text...")
    X_train_text = preprocess_texts(train_df["text"])
    X_val_text   = preprocess_texts(val_df["text"])
    X_test_text  = preprocess_texts(test_df["text"])

    y_cat_train = train_df["category"].tolist()
    y_cat_val   = val_df["category"].tolist()
    y_cat_test  = test_df["category"].tolist()

    y_pri_train = train_df["priority"].tolist()
    y_pri_val   = val_df["priority"].tolist()
    y_pri_test  = test_df["priority"].tolist()

    # ── Step 4: Feature engineering ───────────────────────────────────
    logger.info("Step 4/6 — Building TF-IDF feature matrix...")
    fe = FeatureEngineer()
    X_train_feat = fe.fit_transform(X_train_text)
    X_val_feat   = fe.transform(X_val_text)
    X_test_feat  = fe.transform(X_test_text)

    tfidf_path = ARTIFACT_DIR / "tfidf_vectorizer.pkl"
    joblib.dump(fe, tfidf_path)
    logger.info(f"FeatureEngineer saved to {tfidf_path}")

    # ── Step 5: Category Classifier ───────────────────────────────────
    logger.info("Step 5/6 — Training Category Classifier...")
    cat_clf = CategoryClassifier()
    cat_clf.train(X_train_feat, y_cat_train,
                  use_grid_search=use_grid_search)

    # Store feature names for ML dashboard
    try:
        cat_clf.set_feature_names(fe.get_feature_names())
    except Exception:
        pass

    cat_clf.save()

    # Evaluate
    y_cat_pred_val  = cat_clf.classifier.predict(X_val_feat)
    y_cat_pred_test = cat_clf.classifier.predict(X_test_feat)

    cat_val_report  = classification_report(
        y_cat_val, y_cat_pred_val,
        target_names=ALL_CATEGORIES, output_dict=True
    )
    cat_test_report = classification_report(
        y_cat_test, y_cat_pred_test,
        target_names=ALL_CATEGORIES, output_dict=True
    )
    cat_f1_macro = cat_test_report["macro avg"]["f1-score"]

    logger.info(f"Category Classifier — Test F1 (macro): {cat_f1_macro:.4f}")
    for cat in ALL_CATEGORIES:
        r = cat_test_report.get(cat, {})
        logger.info(
            f"  {cat:15s}: "
            f"F1={r.get('f1-score',0):.3f} | "
            f"P={r.get('precision',0):.3f} | "
            f"R={r.get('recall',0):.3f}"
        )

    # ── Step 5b: Priority Classifier ──────────────────────────────────
    logger.info("Training Priority Classifier (Random Forest)...")
    pri_clf = PriorityClassifier()
    pri_clf.train(X_train_feat, y_pri_train)
    pri_clf.save()

    y_pri_pred_test = pri_clf.classifier.predict(X_test_feat)
    y_pri_pred_labels = pri_clf.label_encoder.inverse_transform(
        y_pri_pred_test
    )
    pri_f1_macro = f1_score(
        y_pri_test, y_pri_pred_labels,
        average="macro", zero_division=0
    )
    logger.info(f"Priority Classifier — Test F1 (macro): {pri_f1_macro:.4f}")

    # ── Step 6: SLA Predictor ─────────────────────────────────────────
    sla_auc = 0.0
    if not skip_sla:
        logger.info("Step 6/6 — Training SLA Breach Predictor...")
        rng = np.random.default_rng(1)
        train_queues = rng.integers(1, 50, size=len(train_df))
        test_queues  = rng.integers(1, 50, size=len(test_df))

        train_sla_dicts  = build_sla_feature_dicts(train_df, train_queues)
        test_sla_dicts   = build_sla_feature_dicts(test_df,  test_queues)
        train_sla_labels = generate_synthetic_sla_labels(train_df)
        test_sla_labels  = generate_synthetic_sla_labels(test_df)

        sla_clf = SLAPredictor()
        sla_clf.train(train_sla_dicts, train_sla_labels.tolist())
        sla_clf.save()

        from sklearn.metrics import roc_auc_score
        sla_probs = [
            sla_clf.predict_breach_probability(t)
            for t in test_sla_dicts
        ]
        try:
            sla_auc = roc_auc_score(test_sla_labels, sla_probs)
            logger.info(f"SLA Predictor — Test AUC-ROC: {sla_auc:.4f}")
        except Exception as e:
            logger.warning(f"Could not compute SLA AUC: {e}")
    else:
        logger.info("Skipping SLA predictor (--skip-sla flag).")

    # ── Save metrics ──────────────────────────────────────────────────
    metrics = {
        "run_id": run_id,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "training_samples": len(train_df),
        "category_f1_macro": round(cat_f1_macro, 4),
        "priority_f1_macro": round(pri_f1_macro, 4),
        "sla_auc_roc": round(sla_auc, 4),
        "per_category_metrics": {
            cat: {
                "precision": round(cat_test_report.get(cat,{}).get("precision",0), 4),
                "recall":    round(cat_test_report.get(cat,{}).get("recall",0), 4),
                "f1":        round(cat_test_report.get(cat,{}).get("f1-score",0), 4),
                "support":   int(cat_test_report.get(cat,{}).get("support",0)),
            }
            for cat in ALL_CATEGORIES
        },
    }

    metrics_path = ARTIFACT_DIR / f"training_metrics_{run_id}.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {metrics_path}")

    # ── Performance targets ───────────────────────────────────────────
    logger.info("═══ Performance Target Check ═══")
    targets = {
        "Overall F1 >= 0.85":      cat_f1_macro >= 0.85,
        "Auth F1 >= 0.90":         cat_test_report.get("Auth",{}).get("f1-score",0) >= 0.90,
        "Security Recall >= 0.98": cat_test_report.get("Security",{}).get("recall",0) >= 0.98,
        "Billing F1 >= 0.88":      cat_test_report.get("Billing",{}).get("f1-score",0) >= 0.88,
        "SLA AUC >= 0.80":         sla_auc >= 0.80 or skip_sla,
    }
    all_passed = True
    for target, passed in targets.items():
        status = "PASS" if passed else "REVIEW"
        if not passed:
            all_passed = False
        logger.info(f"  {status} | {target}")

    if all_passed:
        logger.info("All performance targets met!")
    else:
        logger.warning(
            "Some targets not yet met — expected with synthetic-only data."
        )

    logger.info("═══ Training Complete ═══")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train TicketFlow AI models"
    )
    parser.add_argument(
        "--data-dir", default=None,
        help="Path to directory with Kaggle CSV datasets"
    )
    parser.add_argument(
        "--skip-grid-search", action="store_true",
        help="Skip GridSearchCV (faster for development)"
    )
    parser.add_argument(
        "--skip-sla", action="store_true",
        help="Skip SLA predictor training"
    )
    args = parser.parse_args()

    metrics = train_all_models(
        data_dir=args.data_dir,
        use_grid_search=not args.skip_grid_search,
        skip_sla=args.skip_sla,
    )
    print("\nFinal metrics:")
    print(json.dumps(metrics, indent=2))