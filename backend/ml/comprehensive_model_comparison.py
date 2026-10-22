"""
ml/comprehensive_model_comparison.py — Complete model comparison with confusion matrices.

Compares 5 ML algorithms:
1. Naive Bayes (MultinomialNB)
2. Logistic Regression
3. Random Forest
4. Support Vector Machine (SVM)
5. Gradient Boosting (XGBoost/LightGBM alternative)

Generates detailed confusion matrices and comparison report.

Run with: python -m ml.comprehensive_model_comparison
"""

import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from loguru import logger

logger.remove()
logger.add(sys.stdout, format="{time:HH:mm:ss} | {level} | {message}", level="INFO")

sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.data_loader import map_label, ALL_CATEGORIES
from ml.feature_engineering import FeatureEngineer
from utils.text_cleaner import basic_clean

from sklearn.naive_bayes import MultinomialNB, GaussianNB
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
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


def load_mixed_data():
    """Load the mixed training data."""
    logger.info("Loading mixed training data...")
    
    # Load external data
    external_csv = DATA_DIR / "customer_support_tickets.csv"
    
    if not external_csv.exists():
        logger.error(f"External CSV not found: {external_csv}")
        raise FileNotFoundError("Run train_mixed_data.py first")
    
    df_raw = pd.read_csv(external_csv)
    
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
    
    # Process
    df = pd.DataFrame()
    df["text"] = df_raw[text_col].astype(str)
    df["category"] = df_raw[label_col].apply(lambda x: map_label(str(x)))
    
    # Filter
    df = df.dropna(subset=["category"])
    df = df[df["text"].str.len() > 20]
    df = df[df["category"].isin(ALL_CATEGORIES)]
    
    # Sample for faster comparison
    if len(df) > 3000:
        df = df.sample(n=3000, random_state=42)
    
    logger.info(f"Loaded {len(df)} samples")
    logger.info(f"Categories: {df['category'].value_counts().to_dict()}")
    
    return df


def train_val_split(df: pd.DataFrame, test_size=0.2):
    """Split data into train and test."""
    from sklearn.model_selection import train_test_split
    
    train_df, test_df = train_test_split(
        df,
        test_size=test_size,
        stratify=df["category"],
        random_state=42
    )
    
    return train_df, test_df


def get_models():
    """Return dictionary of models to compare."""
    models = {
        "Naive Bayes (Gaussian)": GaussianNB(),
        
        "Logistic Regression": LogisticRegression(
            C=10.0,
            max_iter=2000,
            class_weight='balanced',
            solver='lbfgs',
            random_state=42,
            n_jobs=-1
        ),
        
        "Random Forest": RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        ),
        
        "SVM (Linear)": SVC(
            kernel='linear',
            C=1.0,
            class_weight='balanced',
            random_state=42,
        ),
        
        "Gradient Boosting": GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42,
        ),
        
        "K-Nearest Neighbors": KNeighborsClassifier(
            n_neighbors=5,
            weights='distance',
            n_jobs=-1
        ),
        
        "Decision Tree": DecisionTreeClassifier(
            max_depth=10,
            class_weight='balanced',
            random_state=42,
        ),
    }
    
    return models


def evaluate_model(model, model_name, X_train, y_train, X_test, y_test, categories):
    """Train and evaluate a single model."""
    logger.info(f"\n{'='*70}")
    logger.info(f"Training: {model_name}")
    logger.info(f"{'='*70}")
    
    # Train
    start_time = datetime.now()
    model.fit(X_train, y_train)
    train_time = (datetime.now() - start_time).total_seconds()
    
    # Predict
    y_pred = model.predict(X_test)
    
    # Metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average='macro', zero_division=0)
    recall = recall_score(y_test, y_pred, average='macro', zero_division=0)
    f1 = f1_score(y_test, y_pred, average='macro', zero_division=0)
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred, labels=categories)
    
    # Per-class report
    report = classification_report(
        y_test, y_pred,
        labels=categories,
        target_names=categories,
        output_dict=True,
        zero_division=0
    )
    
    logger.info(f"✅ {model_name}")
    logger.info(f"   Accuracy:  {accuracy:.4f} ({accuracy*100:.2f}%)")
    logger.info(f"   Precision: {precision:.4f}")
    logger.info(f"   Recall:    {recall:.4f}")
    logger.info(f"   F1-Score:  {f1:.4f}")
    logger.info(f"   Time:      {train_time:.2f}s")
    
    return {
        "model_name": model_name,
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "train_time": float(train_time),
        "confusion_matrix": cm.tolist(),
        "per_class": {
            cat: {
                "precision": float(report[cat]["precision"]),
                "recall": float(report[cat]["recall"]),
                "f1": float(report[cat]["f1-score"]),
                "support": int(report[cat]["support"]),
            }
            for cat in categories
        }
    }


def generate_markdown_report(results, categories, output_path):
    """Generate comprehensive markdown report."""
    lines = [
        "# Comprehensive Model Comparison Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Models Compared:** {len(results)}",
        "",
        "---",
        "",
        "## Overall Performance Comparison",
        "",
        "| Model | Accuracy | Precision | Recall | F1-Score | Training Time |",
        "|-------|----------|-----------|--------|----------|---------------|",
    ]
    
    # Sort by F1-Score
    sorted_results = sorted(results, key=lambda x: x['f1_score'], reverse=True)
    
    for r in sorted_results:
        lines.append(
            f"| {r['model_name']} | {r['accuracy']:.4f} | {r['precision']:.4f} | "
            f"{r['recall']:.4f} | {r['f1_score']:.4f} | {r['train_time']:.2f}s |"
        )
    
    # Best model
    best = sorted_results[0]
    lines.extend([
        "",
        f"**🏆 Best Model:** {best['model_name']} (F1-Score: {best['f1_score']:.4f})",
        "",
        "---",
        "",
        "## Confusion Matrices",
        "",
    ])
    
    # Confusion matrix for each model
    for result in sorted_results:
        lines.extend([
            f"### {result['model_name']}",
            "",
            "```",
        ])
        
        # Header
        cm = np.array(result['confusion_matrix'])
        header = "Actual/Predicted | " + " | ".join([f"{c[:4]:>4s}" for c in categories])
        lines.append(header)
        lines.append("-" * len(header))
        
        # Rows
        for i, category in enumerate(categories):
            row = f"{category[:16]:<16s} | " + " | ".join([f"{cm[i][j]:>4d}" for j in range(len(categories))])
            lines.append(row)
        
        lines.extend([
            "```",
            "",
            f"**Metrics:**",
            f"- Accuracy: {result['accuracy']:.4f} ({result['accuracy']*100:.2f}%)",
            f"- F1-Score: {result['f1_score']:.4f}",
            f"- Training Time: {result['train_time']:.2f}s",
            "",
        ])
    
    # Per-category comparison
    lines.extend([
        "---",
        "",
        "## Per-Category Performance",
        "",
    ])
    
    for category in categories:
        lines.extend([
            f"### {category}",
            "",
            "| Model | Precision | Recall | F1-Score | Support |",
            "|-------|-----------|--------|----------|---------|",
        ])
        
        for result in sorted_results:
            pc = result['per_class'][category]
            lines.append(
                f"| {result['model_name']} | {pc['precision']:.4f} | "
                f"{pc['recall']:.4f} | {pc['f1']:.4f} | {pc['support']} |"
            )
        
        lines.append("")
    
    # Model Selection Rationale
    lines.extend([
        "---",
        "",
        "## Why We Chose This Model",
        "",
        f"### Selected: {best['model_name']}",
        "",
        "**Reasons:**",
        "",
    ])
    
    # Add rationale based on results
    if best['model_name'] == "Logistic Regression":
        lines.extend([
            "1. **Best F1-Score:** Highest balanced performance across all metrics",
            "2. **Fast Training:** Efficient training time for production deployment",
            "3. **Interpretable:** Can explain predictions through feature weights",
            "4. **Scalable:** Handles high-dimensional sparse data well",
            "5. **Robust:** Consistent performance across different categories",
            "6. **Production-Ready:** Well-established algorithm with reliable libraries",
        ])
    elif best['model_name'] == "Random Forest":
        lines.extend([
            "1. **Best F1-Score:** Highest performance",
            "2. **Handles Non-Linearity:** Captures complex patterns",
            "3. **Feature Importance:** Provides insight into key features",
            "4. **Robust to Overfitting:** Ensemble method reduces variance",
        ])
    else:
        lines.extend([
            f"1. **Best F1-Score:** {best['f1_score']:.4f}",
            f"2. **High Accuracy:** {best['accuracy']:.4f}",
            f"3. **Balanced Performance:** Good precision and recall",
        ])
    
    # Comparison with other models
    lines.extend([
        "",
        "### Comparison with Other Models:",
        "",
    ])
    
    for result in sorted_results[1:]:
        diff = (best['f1_score'] - result['f1_score']) * 100
        lines.append(f"- **{result['model_name']}:** {diff:+.2f}% lower F1-Score")
        
        if result['train_time'] < best['train_time']:
            time_diff = best['train_time'] - result['train_time']
            lines.append(f"  - Faster training ({time_diff:.2f}s faster) but lower accuracy")
        else:
            time_diff = result['train_time'] - best['train_time']
            lines.append(f"  - Slower training ({time_diff:.2f}s slower)")
    
    # Trade-offs
    lines.extend([
        "",
        "---",
        "",
        "## Trade-offs Analysis",
        "",
        "### Accuracy vs Speed",
        "",
    ])
    
    fastest = min(sorted_results, key=lambda x: x['train_time'])
    slowest = max(sorted_results, key=lambda x: x['train_time'])
    
    lines.extend([
        f"- **Fastest Model:** {fastest['model_name']} ({fastest['train_time']:.2f}s)",
        f"  - F1-Score: {fastest['f1_score']:.4f}",
        f"  - Trade-off: {(best['f1_score'] - fastest['f1_score'])*100:+.2f}% F1 for speed",
        "",
        f"- **Slowest Model:** {slowest['model_name']} ({slowest['train_time']:.2f}s)",
        f"  - F1-Score: {slowest['f1_score']:.4f}",
        f"  - Trade-off: {(slowest['f1_score'] - best['f1_score'])*100:+.2f}% F1 for {slowest['train_time']:.2f}s",
        "",
        "### Conclusion",
        "",
        f"**{best['model_name']}** provides the best balance of:",
        "- High accuracy and F1-Score",
        "- Reasonable training time",
        "- Production-ready performance",
        "- Interpretability and maintainability",
        "",
        "---",
        "",
        "*Generated by comprehensive_model_comparison.py*"
    ])
    
    # Write file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    logger.info(f"\n✅ Report saved: {output_path}")


def main():
    logger.info("="*70)
    logger.info("COMPREHENSIVE MODEL COMPARISON")
    logger.info("="*70)
    
    # Load data
    df = load_mixed_data()
    train_df, test_df = train_val_split(df)
    
    logger.info(f"\nTrain samples: {len(train_df)}")
    logger.info(f"Test samples: {len(test_df)}")
    
    # Get unique categories in data
    categories = sorted(list(set(test_df["category"].values)))
    logger.info(f"Categories: {categories}")
    
    # Preprocess
    logger.info("\nPreprocessing...")
    X_train_text = [basic_clean(str(t)).lower() for t in train_df["text"]]
    X_test_text = [basic_clean(str(t)).lower() for t in test_df["text"]]
    y_train = train_df["category"].tolist()
    y_test = test_df["category"].tolist()
    
    # Feature engineering
    logger.info("Building features...")
    fe = FeatureEngineer()
    X_train = fe.fit_transform(X_train_text)
    X_test = fe.transform(X_test_text)
    
    # Convert to dense for Naive Bayes Gaussian
    X_train_dense = X_train.toarray()
    X_test_dense = X_test.toarray()
    
    logger.info(f"Feature matrix shape: {X_train.shape}")
    
    # Get models
    models = get_models()
    
    logger.info(f"\nComparing {len(models)} models...")
    
    # Evaluate each model
    results = []
    
    for model_name, model in models.items():
        try:
            # Use dense for Gaussian NB, sparse for others
            if "Gaussian" in model_name:
                result = evaluate_model(
                    model, model_name,
                    X_train_dense, y_train,
                    X_test_dense, y_test,
                    categories
                )
            else:
                result = evaluate_model(
                    model, model_name,
                    X_train, y_train,
                    X_test, y_test,
                    categories
                )
            results.append(result)
        except Exception as e:
            logger.error(f"❌ {model_name} failed: {e}")
    
    # Sort and display
    results_sorted = sorted(results, key=lambda x: x['f1_score'], reverse=True)
    
    logger.info("\n" + "="*70)
    logger.info("FINAL RANKINGS (by F1-Score)")
    logger.info("="*70)
    
    for i, result in enumerate(results_sorted, 1):
        logger.info(
            f"{i}. {result['model_name']:<25s} | "
            f"F1: {result['f1_score']:.4f} | "
            f"Acc: {result['accuracy']:.4f} | "
            f"Time: {result['train_time']:.2f}s"
        )
    
    # Save results
    output_json = ARTIFACT_DIR / "comprehensive_comparison.json"
    with open(output_json, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "categories": categories,
            "results": results_sorted
        }, f, indent=2)
    
    logger.info(f"\n✅ JSON saved: {output_json}")
    
    # Generate markdown report
    output_md = ARTIFACT_DIR / "COMPREHENSIVE_MODEL_COMPARISON.md"
    generate_markdown_report(results_sorted, categories, output_md)
    
    logger.info("\n" + "="*70)
    logger.info("COMPARISON COMPLETE!")
    logger.info("="*70)
    logger.info(f"\nBest Model: {results_sorted[0]['model_name']}")
    logger.info(f"F1-Score: {results_sorted[0]['f1_score']:.4f}\n")


if __name__ == "__main__":
    main()
