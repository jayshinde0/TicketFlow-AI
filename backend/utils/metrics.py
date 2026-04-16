"""
utils/metrics.py — Custom ML metric functions for model evaluation.
"""

import numpy as np
from typing import List, Dict, Tuple
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    precision_recall_curve,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
)


def full_classification_report(
    y_true: List, y_pred: List, class_names: List[str]
) -> Dict:
    """
    Generate a structured classification report dict.

    Returns:
        Dict with per-class metrics and macro/weighted averages.
    """
    report = classification_report(
        y_true, y_pred, target_names=class_names, output_dict=True
    )
    return report


def compute_confusion_matrix(
    y_true: List, y_pred: List, class_names: List[str]
) -> Dict:
    """
    Compute and return confusion matrix as a nested dict suitable for JSON.

    Returns:
        {
          "matrix": [[...], ...],      # raw counts
          "matrix_normalized": [[...]], # row-normalized (0.0-1.0)
          "class_names": [...]
        }
    """
    cm = confusion_matrix(y_true, y_pred, labels=class_names)
    cm_normalized = cm.astype(float)

    # Normalize by row (true label) — avoids divide-by-zero
    row_sums = cm.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums == 0, 1, row_sums)
    cm_normalized = (cm / row_sums).round(4)

    return {
        "matrix": cm.tolist(),
        "matrix_normalized": cm_normalized.tolist(),
        "class_names": class_names,
    }


def compute_expected_calibration_error(
    confidences: np.ndarray, correct: np.ndarray, n_bins: int = 10
) -> Tuple[float, Dict]:
    """
    Compute Expected Calibration Error (ECE) for probability calibration plot.

    Args:
        confidences: Predicted confidence scores (0.0-1.0).
        correct: Binary array (1=correct prediction, 0=wrong).
        n_bins: Number of bins for calibration curve.

    Returns:
        Tuple of (ECE float, calibration_data dict for frontend plotting).
    """
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_data = []
    ece = 0.0

    for i in range(n_bins):
        # Find predictions falling in this confidence bin
        mask = (confidences >= bins[i]) & (confidences < bins[i + 1])
        if not mask.any():
            continue

        bin_confidence = confidences[mask].mean()
        bin_accuracy = correct[mask].mean()
        bin_count = mask.sum()
        total = len(confidences)

        # ECE contribution from this bin
        ece += (bin_count / total) * abs(bin_accuracy - bin_confidence)

        bin_data.append(
            {
                "bin_lower": round(bins[i], 2),
                "bin_upper": round(bins[i + 1], 2),
                "average_confidence": round(float(bin_confidence), 4),
                "actual_accuracy": round(float(bin_accuracy), 4),
                "count": int(bin_count),
            }
        )

    return round(ece, 4), {"bins": bin_data, "ece": round(ece, 4)}


def compute_sla_auc(y_true: np.ndarray, y_scores: np.ndarray) -> Dict:
    """
    Compute AUC-ROC and Average Precision for the binary SLA breach predictor.

    Returns:
        Dict with auc_roc, avg_precision, and precision_recall_curve data.
    """
    auc_roc = roc_auc_score(y_true, y_scores)
    avg_prec = average_precision_score(y_true, y_scores)
    precision, recall, thresholds = precision_recall_curve(y_true, y_scores)

    # Sample every 10th point for frontend chart
    step = max(1, len(precision) // 100)
    pr_curve = [
        {
            "precision": round(float(p), 4),
            "recall": round(float(r), 4),
            "threshold": round(float(t), 4) if i < len(thresholds) else 1.0,
        }
        for i, (p, r, t) in enumerate(
            zip(precision[::step], recall[::step], thresholds[::step])
        )
    ]

    return {
        "auc_roc": round(auc_roc, 4),
        "avg_precision": round(avg_prec, 4),
        "pr_curve": pr_curve,
    }


def metrics_at_threshold(
    y_true: np.ndarray, y_scores: np.ndarray, threshold: float = 0.70
) -> Dict:
    """
    Compute precision, recall, F1 at a specific threshold for SLA model.

    Returns:
        Dict with precision, recall, f1 at given threshold.
    """
    y_pred = (y_scores >= threshold).astype(int)
    return {
        "threshold": threshold,
        "precision": round(precision_score(y_true, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_true, y_pred, zero_division=0), 4),
        "f1": round(f1_score(y_true, y_pred, zero_division=0), 4),
    }
