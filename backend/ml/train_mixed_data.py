"""
ml/train_mixed_data.py — Train model with MIXED synthetic + external data.

This addresses the overfitting issue by training on diverse data sources.

Goal: Improve real-world performance from 71% to 80%+

Run with: python -m ml.train_mixed_data
"""

import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from loguru import logger

logger.remove()
logger.add(sys.stdout, format="{time:HH:mm:ss} | {level} | {message}", level="INFO")

sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.data_loader import (
    generate_synthetic_tickets,
    map_label,
    train_val_test_split,
    ALL_CATEGORIES,
)
from ml.feature_engineering import FeatureEngineer
from ml.models.category_classifier import CategoryClassifier
from ml.models.priority_classifier import PriorityClassifier
from utils.text_cleaner import basic_clean

from sklearn.metrics import classification_report, f1_score
import joblib

ARTIFACT_DIR = Path(__file__).parent / "artifacts"
DATA_DIR = Path(__file__).parent / "data"


def load_external_data(csv_path: Path, max_samples: int = 3000) -> pd.DataFrame:
    """Load external CSV data."""
    logger.info(f"Loading external data from: {csv_path}")
    
    df_raw = pd.read_csv(csv_path)
    
    # Find columns
    text_col = next(
        (c for c in df_raw.columns if any(
            kw in c.lower() for kw in ["description", "body", "text"]
        )),
        None,
    )
    label_col = next(
        (c for c in df_raw.columns if any(
            kw in c.lower() for kw in ["type", "category", "topic"]
        )),
        None,
    )
    
    if not text_col or not label_col:
        raise ValueError(f"Cannot find text/label columns in {csv_path}")
    
    # Process
    df = pd.DataFrame()
    df["text"] = df_raw[text_col].astype(str)
    df["category"] = df_raw[label_col].apply(lambda x: map_label(str(x)))
    df["priority"] = "Medium"  # Default priority
    
    # Filter
    df = df.dropna(subset=["category"])
    df = df[df["text"].str.len() > 20]
    df = df[df["category"].isin(ALL_CATEGORIES)]
    
    if len(df) > max_samples:
        df = df.sample(n=max_samples, random_state=42)
    
    logger.info(f"Loaded {len(df)} external samples")
    logger.info(f"Categories: {df['category'].value_counts().to_dict()}")
    
    return df


def create_mixed_dataset(
    synthetic_ratio: float = 0.5,
    external_csv: Path = None,
) -> pd.DataFrame:
    """Create mixed dataset from synthetic + external sources."""
    logger.info("\n" + "="*70)
    logger.info("CREATING MIXED DATASET")
    logger.info("="*70)
    
    # Generate synthetic data
    logger.info(f"\n1. Generating synthetic data...")
    synthetic_df = generate_synthetic_tickets()
    logger.info(f"   ✅ {len(synthetic_df)} synthetic samples")
    
    # Load external data
    external_df = None
    if external_csv and external_csv.exists():
        logger.info(f"\n2. Loading external data...")
        try:
            external_df = load_external_data(external_csv)
            logger.info(f"   ✅ {len(external_df)} external samples")
        except Exception as e:
            logger.warning(f"   ⚠️  Could not load external data: {e}")
            logger.warning("   Using synthetic data only")
    
    # Mix datasets
    if external_df is not None and len(external_df) > 0:
        # Calculate sample sizes
        total_external = len(external_df)
        synthetic_samples = int(total_external * synthetic_ratio / (1 - synthetic_ratio))
        
        # Sample from synthetic
        if len(synthetic_df) > synthetic_samples:
            synthetic_sample = synthetic_df.sample(n=synthetic_samples, random_state=42)
        else:
            synthetic_sample = synthetic_df
        
        # Combine
        mixed_df = pd.concat([synthetic_sample, external_df], ignore_index=True)
        mixed_df = mixed_df.sample(frac=1, random_state=42).reset_index(drop=True)
        
        logger.info(f"\n3. Mixed dataset created:")
        logger.info(f"   Synthetic: {len(synthetic_sample)} ({len(synthetic_sample)/len(mixed_df)*100:.1f}%)")
        logger.info(f"   External:  {len(external_df)} ({len(external_df)/len(mixed_df)*100:.1f}%)")
        logger.info(f"   Total:     {len(mixed_df)}")
        
        return mixed_df
    else:
        logger.warning("\n⚠️  No external data available, using synthetic only")
        return synthetic_df


def train_with_mixed_data(
    synthetic_ratio: float = 0.3,  # 30% synthetic, 70% external
    use_grid_search: bool = False,
):
    """Train models on mixed data."""
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    
    logger.info("="*70)
    logger.info("TRAINING WITH MIXED DATA")
    logger.info(f"Run ID: {run_id}")
    logger.info("="*70)
    
    # Load mixed dataset
    external_csv = DATA_DIR / "customer_support_tickets.csv"
    mixed_df = create_mixed_dataset(
        synthetic_ratio=synthetic_ratio,
        external_csv=external_csv
    )
    
    # Split data
    logger.info("\n" + "="*70)
    logger.info("SPLITTING DATA")
    logger.info("="*70)
    train_df, val_df, test_df = train_val_test_split(mixed_df)
    
    # Preprocess
    logger.info("\n" + "="*70)
    logger.info("PREPROCESSING")
    logger.info("="*70)
    X_train_text = [basic_clean(str(t)).lower() for t in train_df["text"]]
    X_test_text = [basic_clean(str(t)).lower() for t in test_df["text"]]
    
    y_cat_train = train_df["category"].tolist()
    y_cat_test = test_df["category"].tolist()
    
    # Feature engineering
    logger.info("\n" + "="*70)
    logger.info("FEATURE ENGINEERING")
    logger.info("="*70)
    fe = FeatureEngineer()
    X_train = fe.fit_transform(X_train_text)
    X_test = fe.transform(X_test_text)
    
    logger.info(f"Feature matrix shape: {X_train.shape}")
    
    # Save feature engineering pipeline
    tfidf_path = ARTIFACT_DIR / "tfidf_vectorizer_mixed.pkl"
    joblib.dump(fe, tfidf_path)
    logger.info(f"✅ Feature engineer saved: {tfidf_path}")
    
    # Train category classifier
    logger.info("\n" + "="*70)
    logger.info("TRAINING CATEGORY CLASSIFIER")
    logger.info("="*70)
    
    cat_clf = CategoryClassifier()
    cat_clf.train(X_train, y_cat_train, use_grid_search=use_grid_search)
    
    # Evaluate
    y_pred = cat_clf.classifier.predict(X_test)
    
    accuracy = (np.array(y_pred) == np.array(y_cat_test)).mean()
    f1_macro = f1_score(y_cat_test, y_pred, average='macro', zero_division=0)
    
    logger.info(f"\n✅ Training Complete!")
    logger.info(f"   Test Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    logger.info(f"   Test F1-Score: {f1_macro:.4f}")
    
    # Per-category report
    report = classification_report(
        y_cat_test, y_pred,
        labels=sorted(list(set(y_cat_test))),
        target_names=sorted(list(set(y_cat_test))),
        output_dict=True,
        zero_division=0
    )
    
    logger.info(f"\n📊 Per-Category Performance:")
    logger.info(f"{'Category':<20s} {'Precision':>10s} {'Recall':>8s} {'F1':>8s}")
    logger.info("-" * 55)
    
    for category in sorted(list(set(y_cat_test))):
        r = report[category]
        logger.info(
            f"{category:<20s} {r['precision']:>10.3f} {r['recall']:>8.3f} "
            f"{r['f1-score']:>8.3f}"
        )
    
    # Save model
    model_path = ARTIFACT_DIR / "category_model_mixed.pkl"
    cat_clf.save(model_path)
    logger.info(f"\n✅ Model saved: {model_path}")
    
    # Save metrics
    metrics = {
        "run_id": run_id,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "synthetic_ratio": synthetic_ratio,
        "total_samples": len(mixed_df),
        "train_samples": len(train_df),
        "test_samples": len(test_df),
        "test_accuracy": float(accuracy),
        "test_f1_macro": float(f1_macro),
        "per_category": {
            cat: {
                "precision": float(report[cat]["precision"]),
                "recall": float(report[cat]["recall"]),
                "f1": float(report[cat]["f1-score"]),
            }
            for cat in sorted(list(set(y_cat_test)))
        },
    }
    
    metrics_path = ARTIFACT_DIR / f"training_metrics_mixed_{run_id}.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"✅ Metrics saved: {metrics_path}")
    
    return metrics


def main():
    logger.info("\n" + "="*70)
    logger.info("MIXED DATA TRAINING - Improve Generalization")
    logger.info("="*70)
    
    # Check for external data
    external_csv = DATA_DIR / "customer_support_tickets.csv"
    
    if not external_csv.exists():
        logger.warning("\n⚠️  No external CSV found!")
        logger.warning(f"Expected: {external_csv}")
        logger.warning("\nWill train on synthetic data only.")
        logger.warning("For best results, add external data to ml/data/")
        input("\nPress Enter to continue with synthetic only, or Ctrl+C to cancel...")
    
    # Train
    metrics = train_with_mixed_data(
        synthetic_ratio=0.3,  # 30% synthetic, 70% external
        use_grid_search=False
    )
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("TRAINING COMPLETE")
    logger.info("="*70)
    logger.info(f"\n✅ Test Accuracy: {metrics['test_accuracy']*100:.2f}%")
    logger.info(f"✅ Test F1-Score: {metrics['test_f1_macro']:.4f}")
    
    logger.info("\n💡 Next Steps:")
    logger.info("1. Test this model on external data:")
    logger.info("   python -m ml.test_external_data")
    logger.info("2. Compare with previous results")
    logger.info("3. Use this model if performance improved!")
    
    logger.info("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
