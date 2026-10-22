"""
ml/model_comparison.py — Comprehensive model performance comparison.

Compares multiple ML algorithms for Category and Priority classification:
- Naive Bayes (MultinomialNB)
- Logistic Regression
- Random Forest
- Support Vector Machine (SVM)

Metrics calculated: Accuracy, Precision, Recall, F1-Score

Run with: python -m ml.model_comparison
"""

import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from loguru import logger
from typing import Dict, List, Tuple

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
from ml.feature_engineering import FeatureEngineer
from utils.text_cleaner import basic_clean

# Sklearn imports
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
    confusion_matrix,
)

ARTIFACT_DIR = Path(__file__).parent / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def preprocess_texts(texts: pd.Series) -> List[str]:
    """Clean and lowercase text data."""
    return [basic_clean(str(t)).lower() for t in texts]


class ModelComparator:
    """Compares multiple ML models for classification tasks."""

    def __init__(self):
        self.models = {
            "Logistic Regression": LogisticRegression(
                C=10.0,
                max_iter=2000,
                class_weight="balanced",
                solver="lbfgs",
                multi_class="multinomial",
                random_state=42,
                n_jobs=-1,
            ),
            "Random Forest": RandomForestClassifier(
                n_estimators=200,
                class_weight="balanced",
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1,
            ),
            "SVM (Linear)": SVC(
                kernel="linear",
                C=1.0,
                class_weight="balanced",
                random_state=42,
                probability=True,
            ),
            # Note: Naive Bayes removed due to incompatibility with scaled features
            # MultinomialNB requires non-negative features, but our FeatureEngineer
            # includes StandardScaler which produces negative values
        }
        self.results = {}

    def train_and_evaluate(
        self,
        model_name: str,
        model,
        X_train,
        y_train,
        X_test,
        y_test,
        task_name: str,
    ) -> Dict:
        """
        Train a model and compute evaluation metrics.

        Args:
            model_name: Name of the model (e.g., "Naive Bayes")
            model: Sklearn classifier instance
            X_train: Training features
            y_train: Training labels
            X_test: Test features
            y_test: Test labels
            task_name: "Category" or "Priority"

        Returns:
            Dictionary with all metrics
        """
        logger.info(f"Training {model_name} for {task_name} classification...")

        # Train
        start_time = datetime.now()
        model.fit(X_train, y_train)
        train_time = (datetime.now() - start_time).total_seconds()

        # Predict
        y_pred = model.predict(X_test)

        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision_macro = precision_score(
            y_test, y_pred, average="macro", zero_division=0
        )
        recall_macro = recall_score(y_test, y_pred, average="macro", zero_division=0)
        f1_macro = f1_score(y_test, y_pred, average="macro", zero_division=0)

        precision_weighted = precision_score(
            y_test, y_pred, average="weighted", zero_division=0
        )
        recall_weighted = recall_score(
            y_test, y_pred, average="weighted", zero_division=0
        )
        f1_weighted = f1_score(y_test, y_pred, average="weighted", zero_division=0)

        # Per-class metrics
        if task_name == "Category":
            target_names = ALL_CATEGORIES
        else:
            target_names = ALL_PRIORITIES

        report = classification_report(
            y_test, y_pred, target_names=target_names, output_dict=True, zero_division=0
        )

        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred, labels=target_names)

        results = {
            "model_name": model_name,
            "task": task_name,
            "train_time_seconds": round(train_time, 3),
            "test_samples": len(y_test),
            "metrics": {
                "accuracy": round(accuracy, 4),
                "precision_macro": round(precision_macro, 4),
                "recall_macro": round(recall_macro, 4),
                "f1_macro": round(f1_macro, 4),
                "precision_weighted": round(precision_weighted, 4),
                "recall_weighted": round(recall_weighted, 4),
                "f1_weighted": round(f1_weighted, 4),
            },
            "per_class_metrics": {
                cls: {
                    "precision": round(report[cls]["precision"], 4),
                    "recall": round(report[cls]["recall"], 4),
                    "f1-score": round(report[cls]["f1-score"], 4),
                    "support": int(report[cls]["support"]),
                }
                for cls in target_names
                if cls in report
            },
            "confusion_matrix": cm.tolist(),
        }

        logger.info(
            f"  ✓ {model_name} | "
            f"Accuracy: {accuracy:.4f} | "
            f"F1-Macro: {f1_macro:.4f} | "
            f"Time: {train_time:.2f}s"
        )

        return results

    def compare_models(
        self,
        X_train,
        y_train,
        X_test,
        y_test,
        task_name: str,
    ) -> List[Dict]:
        """Compare all models for a given task."""
        results = []

        logger.info(f"\n{'='*70}")
        logger.info(f"Comparing models for {task_name} Classification")
        logger.info(f"{'='*70}")

        for model_name, model in self.models.items():
            try:
                result = self.train_and_evaluate(
                    model_name, model, X_train, y_train, X_test, y_test, task_name
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error training {model_name}: {e}")
                continue

        return results

    def print_comparison_table(self, results: List[Dict], task_name: str):
        """Print a formatted comparison table."""
        logger.info(f"\n{'='*90}")
        logger.info(f"{task_name} Classification - Model Comparison Summary")
        logger.info(f"{'='*90}")
        logger.info(
            f"{'Model':<25} {'Accuracy':<10} {'Precision':<12} {'Recall':<10} {'F1-Score':<10}"
        )
        logger.info(f"{'-'*90}")

        for result in results:
            metrics = result["metrics"]
            logger.info(
                f"{result['model_name']:<25} "
                f"{metrics['accuracy']:<10.4f} "
                f"{metrics['precision_macro']:<12.4f} "
                f"{metrics['recall_macro']:<10.4f} "
                f"{metrics['f1_macro']:<10.4f}"
            )

        logger.info(f"{'-'*90}")

        # Find best model
        best_model = max(results, key=lambda x: x["metrics"]["f1_macro"])
        logger.info(
            f"\n🏆 Best Model: {best_model['model_name']} "
            f"(F1-Score: {best_model['metrics']['f1_macro']:.4f})"
        )

    def save_results(self, all_results: Dict, output_path: Path):
        """Save comparison results to JSON."""
        with open(output_path, "w") as f:
            json.dump(all_results, f, indent=2)
        logger.info(f"\n✓ Results saved to {output_path}")


def run_model_comparison():
    """Main function to run complete model comparison."""
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    logger.info(f"\n{'='*90}")
    logger.info(f"TicketFlow AI - Model Comparison Analysis")
    logger.info(f"Run ID: {run_id}")
    logger.info(f"{'='*90}")

    # Load and split data
    logger.info("\n[1/5] Loading training data...")
    df = load_training_data(use_synthetic=True)
    logger.info(f"Total samples: {len(df)}")

    logger.info("\n[2/5] Splitting data (70/15/15)...")
    train_df, val_df, test_df = train_val_test_split(df)
    logger.info(
        f"Train: {len(train_df)} | Validation: {len(val_df)} | Test: {len(test_df)}"
    )

    # Preprocess
    logger.info("\n[3/5] Preprocessing text...")
    X_train_text = preprocess_texts(train_df["text"])
    X_test_text = preprocess_texts(test_df["text"])

    # Feature engineering
    logger.info("\n[4/5] Building feature matrix (TF-IDF)...")
    fe = FeatureEngineer()
    X_train_feat = fe.fit_transform(X_train_text)
    X_test_feat = fe.transform(X_test_text)
    logger.info(f"Feature matrix shape: {X_train_feat.shape}")

    # Extract labels
    y_cat_train = train_df["category"].tolist()
    y_cat_test = test_df["category"].tolist()
    y_pri_train = train_df["priority"].tolist()
    y_pri_test = test_df["priority"].tolist()

    # Run comparisons
    logger.info("\n[5/5] Running model comparisons...\n")

    comparator = ModelComparator()

    # Category classification comparison
    cat_results = comparator.compare_models(
        X_train_feat, y_cat_train, X_test_feat, y_cat_test, "Category"
    )
    comparator.print_comparison_table(cat_results, "Category")

    # Priority classification comparison
    pri_results = comparator.compare_models(
        X_train_feat, y_pri_train, X_test_feat, y_pri_test, "Priority"
    )
    comparator.print_comparison_table(pri_results, "Priority")

    # Compile all results
    all_results = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset_info": {
            "total_samples": len(df),
            "train_samples": len(train_df),
            "test_samples": len(test_df),
            "feature_dimension": X_train_feat.shape[1],
        },
        "category_classification": cat_results,
        "priority_classification": pri_results,
    }

    # Save results
    output_path = ARTIFACT_DIR / f"model_comparison_{run_id}.json"
    comparator.save_results(all_results, output_path)

    # Generate summary report
    logger.info(f"\n{'='*90}")
    logger.info("OVERALL SUMMARY")
    logger.info(f"{'='*90}")

    logger.info("\nCategory Classification:")
    best_cat = max(cat_results, key=lambda x: x["metrics"]["f1_macro"])
    logger.info(f"  Best: {best_cat['model_name']} (F1: {best_cat['metrics']['f1_macro']:.4f})")

    logger.info("\nPriority Classification:")
    best_pri = max(pri_results, key=lambda x: x["metrics"]["f1_macro"])
    logger.info(f"  Best: {best_pri['model_name']} (F1: {best_pri['metrics']['f1_macro']:.4f})")

    logger.info(f"\n{'='*90}")
    logger.info("Model comparison complete! 🎉")
    logger.info(f"{'='*90}\n")

    return all_results


if __name__ == "__main__":
    results = run_model_comparison()
