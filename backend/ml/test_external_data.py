"""
ml/test_external_data.py — Test trained models on EXTERNAL data (not synthetic).

This script:
1. Loads your trained models
2. Tests on REAL external CSV data (customer_support_tickets.csv)
3. Shows TRUE generalization performance
4. Compares synthetic vs. external data results

This is the REAL test of whether the model overfits!

Run with: python -m ml.test_external_data
"""

import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from loguru import logger
from typing import Dict, List

logger.remove()
logger.add(sys.stdout, format="{time:HH:mm:ss} | {level} | {message}", level="INFO")

sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.data_loader import map_label, ALL_CATEGORIES
from ml.feature_engineering import FeatureEngineer
from ml.models.category_classifier import CategoryClassifier
from utils.text_cleaner import basic_clean

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

ARTIFACT_DIR = Path(__file__).parent / "artifacts"
DATA_DIR = Path(__file__).parent / "data"


def load_external_csv_data(csv_path: Path, max_samples: int = None) -> pd.DataFrame:
    """Load and preprocess external CSV data."""
    logger.info(f"Loading external data from: {csv_path}")
    
    df_raw = pd.read_csv(csv_path)
    logger.info(f"Raw CSV rows: {len(df_raw)}")
    logger.info(f"Columns: {list(df_raw.columns)}")
    
    # Try to find text and label columns
    text_col = next(
        (
            c for c in df_raw.columns
            if any(keyword in c.lower() for keyword in 
                   ["description", "body", "text", "ticket_description", "message", "complaint"])
        ),
        None,
    )
    
    label_col = next(
        (
            c for c in df_raw.columns
            if any(keyword in c.lower() for keyword in
                   ["type", "category", "topic", "issue_type", "ticket_type"])
        ),
        None,
    )
    
    if not text_col or not label_col:
        logger.error(f"Could not find text or label columns!")
        logger.error(f"Available columns: {list(df_raw.columns)}")
        raise ValueError("Cannot identify text/label columns in CSV")
    
    logger.info(f"Using text column: '{text_col}'")
    logger.info(f"Using label column: '{label_col}'")
    
    # Map labels to our categories
    df_processed = pd.DataFrame()
    df_processed["text"] = df_raw[text_col].astype(str)
    df_processed["raw_label"] = df_raw[label_col].astype(str)
    df_processed["category"] = df_processed["raw_label"].apply(map_label)
    
    # Remove unmapped and short texts
    df_processed = df_processed.dropna(subset=["category"])
    df_processed = df_processed[df_processed["text"].str.len() > 20]
    df_processed = df_processed[df_processed["category"].isin(ALL_CATEGORIES)]
    
    if max_samples and len(df_processed) > max_samples:
        df_processed = df_processed.sample(n=max_samples, random_state=42)
    
    logger.info(f"Processed samples: {len(df_processed)}")
    logger.info(f"Category distribution:")
    for cat, count in df_processed["category"].value_counts().items():
        logger.info(f"  {cat:20s}: {count:4d}")
    
    # Show unmapped categories
    unmapped = df_raw[label_col].apply(lambda x: map_label(str(x)) is None).sum()
    logger.info(f"Unmapped labels: {unmapped} (not in our 10 categories)")
    
    return df_processed


def test_on_external_data(external_df: pd.DataFrame) -> Dict:
    """Test trained model on external data."""
    logger.info("\n" + "="*70)
    logger.info("TESTING ON EXTERNAL DATA")
    logger.info("="*70)
    
    # Load trained model
    logger.info("\nLoading trained model...")
    
    # Try mixed model first, fall back to original
    mixed_model_path = ARTIFACT_DIR / "category_model_mixed.pkl"
    if mixed_model_path.exists():
        logger.info("Using MIXED-DATA model...")
        cat_clf = CategoryClassifier.load(mixed_model_path)
        tfidf_path = ARTIFACT_DIR / "tfidf_vectorizer_mixed.pkl"
    else:
        logger.info("Using ORIGINAL model...")
        try:
            cat_clf = CategoryClassifier.load()
            tfidf_path = ARTIFACT_DIR / "tfidf_vectorizer.pkl"
        except FileNotFoundError:
            logger.error("❌ Model not found! Train first with: python -m ml.train")
            raise
    
    logger.info("✅ Model loaded successfully")
    
    # Load feature engineering pipeline
    if not tfidf_path.exists():
        logger.error("❌ TF-IDF vectorizer not found! Train first.")
        raise FileNotFoundError(f"Missing {tfidf_path}")
    
    import joblib
    fe: FeatureEngineer = joblib.load(tfidf_path)
    logger.info("✅ Feature engineering pipeline loaded")
    
    # Preprocess external data
    logger.info("\nPreprocessing external data...")
    X_text = [basic_clean(str(t)).lower() for t in external_df["text"]]
    y_true = external_df["category"].tolist()
    
    # Transform features
    logger.info("Extracting features...")
    X = fe.transform(X_text)
    logger.info(f"Feature matrix shape: {X.shape}")
    
    # Predict
    logger.info("\nMaking predictions...")
    y_pred = cat_clf.classifier.predict(X)
    y_proba = cat_clf.classifier.predict_proba(X)
    
    # Calculate metrics
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, average='macro', zero_division=0)
    recall = recall_score(y_true, y_pred, average='macro', zero_division=0)
    f1 = f1_score(y_true, y_pred, average='macro', zero_division=0)
    
    # Get unique categories in test data
    unique_categories = sorted(list(set(y_true)))
    logger.info(f"\nCategories in external data: {unique_categories}")
    logger.info(f"Total categories: {len(unique_categories)}")
    
    # Per-class report (only for present categories)
    report = classification_report(
        y_true, y_pred,
        labels=unique_categories,
        target_names=unique_categories,
        output_dict=True,
        zero_division=0
    )
    
    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=unique_categories)
    
    # Display results
    logger.info("\n" + "="*70)
    logger.info("RESULTS ON EXTERNAL DATA")
    logger.info("="*70)
    logger.info(f"\n📊 Overall Metrics:")
    logger.info(f"  Accuracy:  {accuracy:.4f} ({accuracy*100:.2f}%)")
    logger.info(f"  Precision: {precision:.4f}")
    logger.info(f"  Recall:    {recall:.4f}")
    logger.info(f"  F1-Score:  {f1:.4f}")
    
    logger.info(f"\n📋 Per-Category Performance:")
    logger.info(f"{'Category':<20s} {'Precision':>10s} {'Recall':>8s} {'F1':>8s} {'Support':>8s}")
    logger.info("-" * 70)
    
    for category in unique_categories:
        r = report[category]
        logger.info(
            f"{category:<20s} {r['precision']:>10.3f} {r['recall']:>8.3f} "
            f"{r['f1-score']:>8.3f} {int(r['support']):>8d}"
        )
    
    logger.info("-" * 70)
    logger.info(
        f"{'Macro Avg':<20s} {report['macro avg']['precision']:>10.3f} "
        f"{report['macro avg']['recall']:>8.3f} "
        f"{report['macro avg']['f1-score']:>8.3f}"
    )
    
    # Confidence analysis
    max_proba = y_proba.max(axis=1)
    avg_confidence = max_proba.mean()
    low_confidence_count = (max_proba < 0.7).sum()
    
    logger.info(f"\n🎯 Confidence Analysis:")
    logger.info(f"  Average confidence: {avg_confidence:.4f}")
    logger.info(f"  Low confidence predictions (<70%): {low_confidence_count} "
                f"({low_confidence_count/len(y_pred)*100:.1f}%)")
    
    return {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "avg_confidence": float(avg_confidence),
        "low_confidence_count": int(low_confidence_count),
        "per_category": {
            cat: {
                "precision": float(report[cat]["precision"]),
                "recall": float(report[cat]["recall"]),
                "f1": float(report[cat]["f1-score"]),
                "support": int(report[cat]["support"]),
            }
            for cat in unique_categories
        },
        "confusion_matrix": cm.tolist(),
    }


def compare_synthetic_vs_external():
    """Compare performance on synthetic vs. external data."""
    logger.info("\n" + "="*70)
    logger.info("COMPARISON: Synthetic vs. External Data")
    logger.info("="*70)
    
    # Load previous synthetic results
    synthetic_results_path = ARTIFACT_DIR / "evaluation_results.json"
    
    if synthetic_results_path.exists():
        with open(synthetic_results_path, 'r') as f:
            synthetic_data = json.load(f)
            synthetic_report = synthetic_data.get("category_model", {}).get("classification_report", {})
            synthetic_f1 = synthetic_report.get("macro avg", {}).get("f1-score", None)
            
            if synthetic_f1:
                logger.info(f"\n📊 Synthetic Test Data F1-Score: {synthetic_f1:.4f}")
            else:
                logger.warning("⚠️  Could not load synthetic F1-score")
    else:
        logger.warning("⚠️  No synthetic evaluation results found")


def main():
    logger.info("="*70)
    logger.info("EXTERNAL DATA VALIDATION TEST")
    logger.info("="*70)
    logger.info("\nThis tests your model on COMPLETELY DIFFERENT data")
    logger.info("to see true generalization performance!\n")
    
    # Check if model exists
    model_path = ARTIFACT_DIR / "category_model.pkl"
    if not model_path.exists():
        logger.error("\n❌ No trained model found!")
        logger.error("Train first with: python -m ml.train")
        return 1
    
    # Load external CSV
    csv_path = DATA_DIR / "customer_support_tickets.csv"
    
    if not csv_path.exists():
        logger.error(f"\n❌ External CSV not found at: {csv_path}")
        logger.error("\nOptions:")
        logger.error("1. Place your CSV at: backend/ml/data/customer_support_tickets.csv")
        logger.error("2. Or download a Kaggle dataset (customer support tickets)")
        logger.error("3. Or use your own real support tickets")
        return 1
    
    try:
        # Load and test
        external_df = load_external_csv_data(csv_path, max_samples=2000)
        
        if len(external_df) < 100:
            logger.warning(f"\n⚠️  Only {len(external_df)} samples after filtering")
            logger.warning("Consider using a dataset with more diverse categories")
        
        # Test model
        results = test_on_external_data(external_df)
        
        # Compare with synthetic
        compare_synthetic_vs_external()
        
        # Interpretation
        logger.info("\n" + "="*70)
        logger.info("INTERPRETATION")
        logger.info("="*70)
        
        external_f1 = results["f1_score"]
        
        if external_f1 > 0.90:
            logger.info("\n🎉 EXCELLENT! Model generalizes very well to external data!")
            logger.info("Your model is robust and production-ready.")
        elif external_f1 > 0.80:
            logger.info("\n✅ GOOD! Model performs well on external data.")
            logger.info("This is realistic production-level performance.")
            logger.info("Better than industry average (80-85%)")
        elif external_f1 > 0.70:
            logger.info("\n⚠️  MODERATE. Performance dropped on external data.")
            logger.info("This is expected - external data has different patterns.")
            logger.info("Consider retraining with mix of synthetic + external data.")
        else:
            logger.info("\n❌ LOW. Model struggles with external data.")
            logger.info("Possible reasons:")
            logger.info("  1. External data has very different vocabulary")
            logger.info("  2. Categories don't align well")
            logger.info("  3. Model needs retraining on broader data")
        
        # Save results
        output = {
            "test_date": datetime.now().isoformat(),
            "external_data_samples": len(external_df),
            "results": results,
        }
        
        output_path = ARTIFACT_DIR / "external_test_results.json"
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"\n✅ Results saved to: {output_path}")
        
        # Final summary
        logger.info("\n" + "="*70)
        logger.info("SUMMARY")
        logger.info("="*70)
        logger.info(f"\n✅ Tested on {len(external_df)} EXTERNAL samples")
        logger.info(f"📊 Accuracy: {results['accuracy']*100:.2f}%")
        logger.info(f"📊 F1-Score: {results['f1_score']:.4f}")
        logger.info(f"🎯 Avg Confidence: {results['avg_confidence']:.4f}")
        
        logger.info("\n💡 This is your TRUE generalization performance!")
        logger.info("Use this number in your presentation for realistic expectations.\n")
        
        return 0
        
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
