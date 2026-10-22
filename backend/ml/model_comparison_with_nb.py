"""
ml/model_comparison_with_nb.py — Model comparison INCLUDING Naive Bayes.

This version uses TF-IDF features ONLY (no scaled metadata) to be compatible
with Naive Bayes, which requires non-negative features.

Run with: python -m ml.model_comparison_with_nb
"""

import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from loguru import logger
from typing import Dict, List

# Configure logger
logger.remove()
logger.add(
    sys.stdout,
    format="{time:HH:mm:ss} | {level} | {message}",
    level="INFO",
    colorize=False,
)

# Add backend root to python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.data_loader import (
    load_training_data,
    train_val_test_split,
    ALL_CATEGORIES,
    ALL_PRIORITIES,
)
from utils.text_cleaner import basic_clean

# Sklearn imports
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
)

ARTIFACT_DIR = Path(__file__).parent / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def preprocess_texts(texts: pd.Series) -> List[str]:
    """Clean and lowercase text data."""
    return [basic_clean(str(t)).lower() for t in texts]


def run_comparison_with_naive_bayes():
    """Run model comparison with Naive Bayes included (TF-IDF features only)."""
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    logger.info(f"\n{'='*90}")
    logger.info(f"Model Comparison with Naive Bayes")
    logger.info(f"Run ID: {run_id}")
    logger.info(f"Note: Using TF-IDF features ONLY (no scaled metadata)")
    logger.info(f"{'='*90}")

    # Load data
    logger.info("\n[1/4] Loading data...")
    df = load_training_data(use_synthetic=True)
    train_df, val_df, test_df = train_val_test_split(df)

    # Preprocess
    logger.info("\n[2/4] Preprocessing...")
    X_train_text = preprocess_texts(train_df["text"])
    X_test_text = preprocess_texts(test_df["text"])

    # TF-IDF only (no metadata)
    logger.info("\n[3/4] Building TF-IDF features (no metadata)...")
    vectorizer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
    )
    X_train = vectorizer.fit_transform(X_train_text)
    X_test = vectorizer.transform(X_test_text)

    y_cat_train = train_df["category"].tolist()
    y_cat_test = test_df["category"].tolist()
    y_pri_train = train_df["priority"].tolist()
    y_pri_test = test_df["priority"].tolist()

    # Models
    models = {
        "Naive Bayes": MultinomialNB(alpha=1.0),
        "Logistic Regression": LogisticRegression(
            C=10.0,
            max_iter=2000,
            class_weight="balanced",
            solver="lbfgs",
            random_state=42,
            n_jobs=-1,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=200,
            class_weight="balanced",
            max_depth=10,
            random_state=42,
            n_jobs=-1,
        ),
        "SVM (Linear)": SVC(
            kernel="linear",
            C=1.0,
            class_weight="balanced",
            random_state=42,
        ),
    }

    # Run comparisons
    logger.info("\n[4/4] Training and evaluating models...\n")

    results = {"category": {}, "priority": {}}

    for task_name, y_train, y_test in [
        ("Category", y_cat_train, y_cat_test),
        ("Priority", y_pri_train, y_pri_test),
    ]:
        logger.info(f"\n{'='*70}")
        logger.info(f"{task_name} Classification")
        logger.info(f"{'='*70}")

        task_results = []

        for model_name, model in models.items():
            logger.info(f"Training {model_name}...")
            start = datetime.now()

            # Train
            model.fit(X_train, y_train)
            train_time = (datetime.now() - start).total_seconds()

            # Predict
            y_pred = model.predict(X_test)

            # Metrics
            acc = accuracy_score(y_test, y_pred)
            prec = precision_score(y_test, y_pred, average="macro", zero_division=0)
            rec = recall_score(y_test, y_pred, average="macro", zero_division=0)
            f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)

            logger.info(
                f"  ✓ {model_name:20s} | Acc: {acc:.4f} | F1: {f1:.4f} | Time: {train_time:.2f}s"
            )

            task_results.append(
                {
                    "model": model_name,
                    "accuracy": round(acc, 4),
                    "precision": round(prec, 4),
                    "recall": round(rec, 4),
                    "f1_score": round(f1, 4),
                    "train_time": round(train_time, 2),
                }
            )

        results[task_name.lower()] = task_results

        # Print summary table
        logger.info(f"\n{task_name} Summary:")
        logger.info(
            f"{'Model':<20s} {'Accuracy':<10s} {'Precision':<12s} {'Recall':<10s} {'F1-Score':<10s}"
        )
        logger.info("-" * 70)
        for r in task_results:
            logger.info(
                f"{r['model']:<20s} {r['accuracy']:<10.4f} {r['precision']:<12.4f} "
                f"{r['recall']:<10.4f} {r['f1_score']:<10.4f}"
            )

        best = max(task_results, key=lambda x: x["f1_score"])
        logger.info(f"\n🏆 Best: {best['model']} (F1: {best['f1_score']:.4f})")

    # Save results
    output = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "note": "TF-IDF features only (no metadata) to include Naive Bayes",
        "feature_count": X_train.shape[1],
        "results": results,
    }

    output_path = ARTIFACT_DIR / f"model_comparison_with_nb_{run_id}.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    logger.info(f"\n✓ Results saved to {output_path}")

    logger.info(f"\n{'='*90}")
    logger.info("Comparison complete!")
    logger.info(f"{'='*90}\n")

    return results


if __name__ == "__main__":
    run_comparison_with_naive_bayes()
