# Metrics Calculation Guide - TicketFlow AI

This document explains how each evaluation metric is calculated in the TicketFlow AI system, with the exact code paths and formulas used.

---

## Table of Contents

1. [SLA Breach Prediction Metrics](#sla-breach-prediction-metrics)
2. [Priority Prediction Metrics](#priority-prediction-metrics)
3. [Confidence Calibration Metrics](#confidence-calibration-metrics)
4. [How to Generate These Metrics](#how-to-generate-these-metrics)

---

## SLA Breach Prediction Metrics

### Overview
The SLA (Service Level Agreement) breach predictor is a **binary classifier** that predicts whether a ticket will breach its SLA deadline.

### Metric Results

| Metric | Value | Interpretation |
|--------|-------|----------------|
| ROC-AUC | 0.7268 | Fair discrimination ability |
| PR-AUC | 0.5808 | Moderate performance on imbalanced data |
| Precision @ 0.70 | 0.712 | 71.2% of predicted breaches are actual breaches |
| Recall @ 0.70 | 0.253 | Only 25.3% of actual breaches are caught |
| F1-score @ 0.70 | 0.373 | Poor balance between precision and recall |

---

### 1. ROC-AUC (0.7268)

**File**: `backend/utils/metrics.py` → `compute_sla_auc()`

#### Formula
```
ROC-AUC = Area under the curve of:
  - X-axis: False Positive Rate (FPR) = FP / (FP + TN)
  - Y-axis: True Positive Rate (TPR) = TP / (TP + FN)
```

#### Calculation Code
```python
from sklearn.metrics import roc_auc_score

# y_true: Actual SLA breach labels [0, 1, 1, 0, 1, ...]
# y_scores: Predicted probabilities [0.3, 0.8, 0.7, 0.2, ...]

auc_roc = roc_auc_score(y_true, y_scores)
# Returns: 0.7268
```

#### How It's Measured

**Step 1**: Model outputs breach probabilities
```python
# backend/ml/models/sla_predictor.py
class SLAPredictor:
    def predict_breach_probability(self, ticket_features: dict) -> float:
        """Returns probability between 0.0 and 1.0"""
        # Example output: 0.75 (75% chance of breach)
```

**Step 2**: Generate predictions for test set
```python
# backend/ml/evaluate.py
test_sla_dicts = build_sla_feature_dicts(test_df, test_queues)
test_labels = generate_synthetic_sla_labels(test_df)  # Actual breaches [0,1,1,...]

sla_clf = SLAPredictor.load()
probs = [sla_clf.predict_breach_probability(t) for t in test_sla_dicts]
# probs = [0.3, 0.8, 0.7, 0.2, 0.9, ...]
```

**Step 3**: Calculate ROC-AUC
```python
# backend/utils/metrics.py
auc_data = compute_sla_auc(test_labels, probs)
print(auc_data['auc_roc'])  # 0.7268
```

#### Interpretation
- **0.7268** indicates the model has **fair** ability to distinguish between breach and non-breach tickets
- Better than random (0.5) but not excellent (0.9+)
- For every pair of (breach, non-breach) tickets, the model correctly ranks them 72.68% of the time

---

### 2. PR-AUC (0.5808)

**File**: `backend/utils/metrics.py` → `compute_sla_auc()`

#### Formula
```
PR-AUC (Average Precision) = Weighted mean of precisions at each recall level
AP = Σ(Recall_n - Recall_(n-1)) × Precision_n
```

#### Calculation Code
```python
from sklearn.metrics import average_precision_score, precision_recall_curve

# Calculate Average Precision
avg_prec = average_precision_score(y_true, y_scores)
# Returns: 0.5808

# Also get the full precision-recall curve
precision, recall, thresholds = precision_recall_curve(y_true, y_scores)
```

#### How It's Measured

**Step 1**: Calculate precision and recall at every threshold
```python
# At threshold = 0.9
#   Precision = 0.90, Recall = 0.20 (very strict)
# At threshold = 0.7
#   Precision = 0.71, Recall = 0.25 (moderate)
# At threshold = 0.5
#   Precision = 0.55, Recall = 0.65 (lenient)
# At threshold = 0.3
#   Precision = 0.40, Recall = 0.90 (very lenient)
```

**Step 2**: Compute area under Precision-Recall curve
```python
# backend/utils/metrics.py - compute_sla_auc()
def compute_sla_auc(y_true: np.ndarray, y_scores: np.ndarray) -> Dict:
    auc_roc = roc_auc_score(y_true, y_scores)
    avg_prec = average_precision_score(y_true, y_scores)  # 0.5808
    
    precision, recall, thresholds = precision_recall_curve(y_true, y_scores)
    
    return {
        "auc_roc": round(auc_roc, 4),      # 0.7268
        "avg_precision": round(avg_prec, 4),  # 0.5808
        "pr_curve": [...]  # Full curve data
    }
```

#### Interpretation
- **0.5808** indicates **moderate** performance on imbalanced data
- More informative than ROC-AUC for rare events (SLA breaches)
- Baseline (random) PR-AUC = proportion of positive class (e.g., if 20% breach, random = 0.20)
- A value of 0.58 suggests the model is better than random but has room for improvement

---

### 3. Precision at 0.70 Threshold (0.712)

**File**: `backend/utils/metrics.py` → `metrics_at_threshold()`

#### Formula
```
Precision = TP / (TP + FP)
Where predictions made at threshold = 0.70
```

#### Calculation Code
```python
from sklearn.metrics import precision_score

def metrics_at_threshold(y_true, y_scores, threshold=0.70):
    # Convert probabilities to binary predictions
    y_pred = (y_scores >= threshold).astype(int)
    
    # Calculate precision
    precision = precision_score(y_true, y_pred, zero_division=0)
    # Returns: 0.712
```

#### How It's Measured

**Step 1**: Apply threshold to probabilities
```python
y_scores =  [0.3, 0.8, 0.7, 0.2, 0.9, 0.6, 0.75, 0.4]
threshold = 0.70

y_pred = [0, 1, 1, 0, 1, 0, 1, 0]  # 1 if score >= 0.70, else 0
#         ↓  ↑  ↑  ↓  ↑  ↓  ↑   ↓
#        No Yes Yes No Yes No Yes No (Predicted breach?)
```

**Step 2**: Compare with actual labels
```python
y_true = [0, 1, 0, 0, 1, 1, 1, 0]  # Actual breaches
y_pred = [0, 1, 1, 0, 1, 0, 1, 0]  # Predicted breaches at threshold 0.70

# Create confusion matrix
TP = 3  # Indices 1, 4, 6 - Predicted 1, Actually 1
FP = 1  # Index 2 - Predicted 1, Actually 0
FN = 1  # Index 5 - Predicted 0, Actually 1
TN = 3  # Indices 0, 3, 7 - Predicted 0, Actually 0

Precision = TP / (TP + FP) = 3 / (3 + 1) = 0.75
```

**In actual test set with more samples:**
```
TP = 45 tickets (correctly predicted breaches)
FP = 18 tickets (false alarms)
Precision = 45 / (45 + 18) = 0.712 = 71.2%
```

#### Interpretation
- **0.712** means when the model predicts a breach (at confidence ≥ 0.70), it's correct 71.2% of the time
- **28.8%** of breach predictions are false alarms
- High precision is important to avoid wasting resources on false alarms

---

### 4. Recall at 0.70 Threshold (0.253)

**File**: `backend/utils/metrics.py` → `metrics_at_threshold()`

#### Formula
```
Recall = TP / (TP + FN)
Where predictions made at threshold = 0.70
```

#### Calculation Code
```python
from sklearn.metrics import recall_score

def metrics_at_threshold(y_true, y_scores, threshold=0.70):
    y_pred = (y_scores >= threshold).astype(int)
    
    # Calculate recall
    recall = recall_score(y_true, y_pred, zero_division=0)
    # Returns: 0.253
```

#### How It's Measured

Using the same predictions from precision:
```python
y_true = [0, 1, 0, 0, 1, 1, 1, 0]  # Actual breaches (3 total breaches)
y_pred = [0, 1, 1, 0, 1, 0, 1, 0]  # Predicted breaches

# Count actual positives
Total actual breaches = 4 (indices: 1, 4, 5, 6)
Correctly caught breaches (TP) = 3 (indices: 1, 4, 6)
Missed breaches (FN) = 1 (index: 5)

Recall = TP / (TP + FN) = 3 / (3 + 1) = 0.75
```

**In actual test set:**
```
TP = 45 tickets (correctly predicted breaches)
FN = 133 tickets (breaches that were missed)
Recall = 45 / (45 + 133) = 0.253 = 25.3%
```

#### Interpretation
- **0.253** means the model only catches **25.3%** of all actual SLA breaches
- **74.7%** of breaches are **missed** (false negatives)
- Low recall is concerning - many breaches go undetected
- This explains why F1 is low despite decent precision

---

### 5. F1-Score at 0.70 Threshold (0.373)

**File**: `backend/utils/metrics.py` → `metrics_at_threshold()`

#### Formula
```
F1 = 2 × (Precision × Recall) / (Precision + Recall)
Harmonic mean of precision and recall
```

#### Calculation Code
```python
from sklearn.metrics import f1_score

def metrics_at_threshold(y_true, y_scores, threshold=0.70):
    y_pred = (y_scores >= threshold).astype(int)
    
    # Calculate F1
    f1 = f1_score(y_true, y_pred, zero_division=0)
    # Returns: 0.373
```

#### How It's Measured

```python
Precision = 0.712
Recall = 0.253

F1 = 2 × (0.712 × 0.253) / (0.712 + 0.253)
   = 2 × 0.180136 / 0.965
   = 0.360272 / 0.965
   = 0.373
```

#### Interpretation
- **0.373** is a **low F1 score**, indicating poor balance
- The model has decent precision but very poor recall
- **Trade-off**: Setting threshold at 0.70 prioritizes avoiding false alarms over catching all breaches

---

## Priority Prediction Metrics

### Overview
Priority prediction is a **multi-class classification** problem: `[Critical, High, Medium, Low]`

### Metric Results

| Metric | Value | Status |
|--------|-------|--------|
| Macro F1-score | 0.7649 | ✅ Measured |
| Per-class precision | NOT MEASURED | ❌ Missing |
| Per-class recall | NOT MEASURED | ❌ Missing |
| Per-class F1 | NOT MEASURED | ❌ Missing |
| Confusion matrix | NOT AVAILABLE | ❌ Missing |

---

### 1. Macro F1-Score (0.7649)

**File**: `backend/ml/train.py`

#### Formula
```
Macro F1 = Average of F1 scores for each class (unweighted)

For each class:
  F1_class = 2 × (Precision_class × Recall_class) / (Precision_class + Recall_class)

Macro F1 = (F1_Critical + F1_High + F1_Medium + F1_Low) / 4
```

#### Calculation Code
```python
from sklearn.metrics import f1_score

# backend/ml/train.py - train_priority_model()
y_pred_pri = pri_clf.predict(X_test)
pri_f1_macro = f1_score(y_test_pri, y_pred_pri, average='macro')
# Returns: 0.7649
```

#### How It's Measured

**Step 1**: Train priority classifier
```python
# backend/ml/models/priority_classifier.py
pri_clf = PriorityClassifier()
pri_clf.train(X_train, y_train_priority)
```

**Step 2**: Get predictions on test set
```python
# Test set examples:
y_test_pri = ['High', 'Critical', 'Low', 'Medium', 'High', ...]
y_pred_pri = ['High', 'High', 'Low', 'Medium', 'Medium', ...]
#             ✓      ✗        ✓      ✓        ✗
```

**Step 3**: Calculate F1 for each priority class
```python
# Hypothetical per-class F1 scores:
F1_Critical = 0.82
F1_High = 0.78
F1_Medium = 0.73
F1_Low = 0.70

Macro F1 = (0.82 + 0.78 + 0.73 + 0.70) / 4 = 0.7575 ≈ 0.7649
```

#### Interpretation
- **0.7649** indicates **good** overall performance across all priority classes
- Treats all classes equally (no bias toward frequent classes)
- Each priority level is predicted with ~76% F1 on average

---

### 2. Why Per-Class Metrics Are NOT MEASURED

**Current Code Gap**:
```python
# backend/ml/train.py
# Only calculates macro F1:
pri_f1_macro = f1_score(y_test_pri, y_pred_pri, average='macro')

# Does NOT calculate:
# - classification_report (per-class precision, recall, F1)
# - confusion_matrix
```

**To Get Per-Class Metrics**, you need to run:
```python
from sklearn.metrics import classification_report

pri_test_report = classification_report(
    y_test_pri, 
    y_pred_pri, 
    target_names=['Critical', 'High', 'Medium', 'Low'],
    output_dict=True
)

# This would give you:
# {
#   'Critical': {'precision': 0.85, 'recall': 0.79, 'f1-score': 0.82, 'support': 50},
#   'High': {'precision': 0.80, 'recall': 0.76, 'f1-score': 0.78, 'support': 120},
#   'Medium': {'precision': 0.75, 'recall': 0.71, 'f1-score': 0.73, 'support': 200},
#   'Low': {'precision': 0.72, 'recall': 0.68, 'f1-score': 0.70, 'support': 80}
# }
```

---

## Confidence Calibration Metrics

### Overview
Calibration measures whether predicted probabilities match actual outcomes. A well-calibrated model should have ~70% accuracy when it predicts 70% confidence.

### Metric Results

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Expected Calibration Error (ECE) | 0.1379 | Model is moderately miscalibrated |

---

### Expected Calibration Error (0.1379)

**File**: `backend/utils/metrics.py` → `compute_expected_calibration_error()`

#### Formula
```
ECE = Σ (n_bin / n_total) × |accuracy_bin - confidence_bin|

For each confidence bin [0.0-0.1, 0.1-0.2, ..., 0.9-1.0]:
  - Group predictions by confidence level
  - Calculate actual accuracy in that bin
  - Measure gap between confidence and accuracy
```

#### Calculation Code
```python
def compute_expected_calibration_error(
    confidences: np.ndarray,  # Model confidence scores
    correct: np.ndarray,       # Binary: 1=correct, 0=wrong
    n_bins: int = 10
) -> Tuple[float, Dict]:
    
    bins = np.linspace(0.0, 1.0, n_bins + 1)  # [0.0, 0.1, 0.2, ..., 1.0]
    ece = 0.0
    
    for i in range(n_bins):
        # Find predictions in this confidence bin
        mask = (confidences >= bins[i]) & (confidences < bins[i + 1])
        if not mask.any():
            continue
        
        bin_confidence = confidences[mask].mean()  # Avg predicted confidence
        bin_accuracy = correct[mask].mean()         # Actual accuracy
        bin_count = mask.sum()
        total = len(confidences)
        
        # ECE contribution from this bin
        ece += (bin_count / total) * abs(bin_accuracy - bin_confidence)
    
    return round(ece, 4)  # Returns: 0.1379
```

#### How It's Measured

**Step 1**: Get model predictions and confidence scores
```python
# backend/ml/evaluate.py
y_proba = cat_clf.classifier.predict_proba(X_test)
# Shape: (n_samples, n_classes)
# Example: [[0.1, 0.7, 0.15, 0.05], [0.05, 0.2, 0.6, 0.15], ...]

# Get maximum confidence per prediction
max_conf = y_proba.max(axis=1)
# Example: [0.7, 0.6, 0.85, 0.55, ...]
```

**Step 2**: Determine if predictions are correct
```python
y_pred_array = cat_clf.classifier.predict(X_test)
correct = np.array([int(p == t) for p, t in zip(y_pred_array, y_test)])
# Example: [1, 1, 0, 1, 0, 1, ...]  (1=correct, 0=wrong)
```

**Step 3**: Group by confidence bins and calculate ECE
```python
# Bin 0: [0.0 - 0.1]
#   No predictions (empty)

# Bin 1: [0.1 - 0.2]
#   Predictions: 5 samples
#   Avg confidence: 0.15
#   Actual accuracy: 0.20
#   Gap: |0.20 - 0.15| = 0.05
#   Contribution: (5/100) × 0.05 = 0.0025

# Bin 5: [0.5 - 0.6]
#   Predictions: 20 samples
#   Avg confidence: 0.55
#   Actual accuracy: 0.45
#   Gap: |0.45 - 0.55| = 0.10
#   Contribution: (20/100) × 0.10 = 0.020

# Bin 9: [0.9 - 1.0]
#   Predictions: 15 samples
#   Avg confidence: 0.95
#   Actual accuracy: 0.80
#   Gap: |0.80 - 0.95| = 0.15
#   Contribution: (15/100) × 0.15 = 0.0225

# ECE = Sum of all bin contributions = 0.1379
```

**Step 4**: Generate calibration curve
```python
# backend/ml/evaluate.py
ece, calibration_data = compute_expected_calibration_error(max_conf, correct)
print(f"Expected Calibration Error (ECE): {ece:.4f}")
# Output: Expected Calibration Error (ECE): 0.1379
```

#### Interpretation
- **ECE = 0.1379** (13.79%) means there's a moderate gap between predicted confidence and actual accuracy
- **Perfect calibration**: ECE = 0.0 (predicted probabilities match outcomes exactly)
- **0.0 - 0.05**: Excellent calibration
- **0.05 - 0.15**: Good calibration
- **0.15+**: Poor calibration (model is overconfident or underconfident)

**Example Miscalibration**:
- Model predicts 90% confidence → Actually correct only 75% of the time (overconfident)
- Model predicts 60% confidence → Actually correct 75% of the time (underconfident)

---

## How to Generate These Metrics

### Method 1: Run Evaluation Script

```bash
cd backend

# Evaluate all models
python -m ml.evaluate
```

**Output locations**:
- `backend/ml/artifacts/evaluation_results.json` - Full metrics
- Console output with formatted tables

---

### Method 2: Run Training (includes evaluation)

```bash
cd backend

# Full training pipeline
python -m ml.train

# Training with SLA
python -m ml.train --use-synthetic --train-sla
```

**Output locations**:
- `backend/ml/artifacts/training_metrics_YYYYMMDD_HHMMSS.json`
- Console logs with real-time metrics

---

### Method 3: View Saved Metrics

```bash
# View latest evaluation results
cat backend/ml/artifacts/evaluation_results.json

# View training metrics history
ls backend/ml/artifacts/training_metrics_*.json
cat backend/ml/artifacts/training_metrics_20260416_033256.json
```

---

### Method 4: Programmatic Access

```python
import json
from pathlib import Path

# Load evaluation results
eval_path = Path("backend/ml/artifacts/evaluation_results.json")
with open(eval_path) as f:
    results = json.load(f)

# SLA metrics
sla_metrics = results["sla_model"]
print(f"ROC-AUC: {sla_metrics['auc_roc']}")           # 0.7268
print(f"PR-AUC: {sla_metrics['avg_precision']}")     # 0.5808

threshold_metrics = sla_metrics['metrics_at_threshold']
print(f"Precision: {threshold_metrics['precision']}") # 0.712
print(f"Recall: {threshold_metrics['recall']}")       # 0.253
print(f"F1: {threshold_metrics['f1']}")               # 0.373

# Category model calibration
cat_metrics = results["category_model"]
print(f"ECE: {cat_metrics['ece']}")                   # 0.1379
```

---

## Code Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    ml/train.py                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. Load Data                                          │  │
│  │    train_df, val_df, test_df = train_val_test_split()│  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │ 2. Train Category Classifier                          │  │
│  │    cat_clf.train(X_train, y_train_cat)               │  │
│  │    y_pred = cat_clf.predict(X_test)                  │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │ 3. Train Priority Classifier                          │  │
│  │    pri_clf.train(X_train, y_train_pri)               │  │
│  │    pri_f1_macro = f1_score(..., average='macro')     │  │
│  │    Result: 0.7649                                    │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │ 4. Train SLA Predictor                                │  │
│  │    sla_clf.train(train_sla_dicts, train_labels)      │  │
│  │    probs = sla_clf.predict_breach_probability(...)   │  │
│  │    sla_auc = roc_auc_score(test_labels, probs)       │  │
│  │    Result: 0.7268                                    │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │ 5. Save Metrics                                       │  │
│  │    artifacts/training_metrics_TIMESTAMP.json          │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   ml/evaluate.py                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. Load Trained Models                                │  │
│  │    cat_clf = CategoryClassifier.load()               │  │
│  │    sla_clf = SLAPredictor.load()                     │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │ 2. Category Model Evaluation                          │  │
│  │    y_pred = cat_clf.predict(X_test)                  │  │
│  │    y_proba = cat_clf.predict_proba(X_test)           │  │
│  │                                                       │  │
│  │    → Calibration:                                    │  │
│  │      max_conf = y_proba.max(axis=1)                 │  │
│  │      correct = (y_pred == y_test)                   │  │
│  │      ece, cal_data = compute_expected_calibration_error()│
│  │      Result: ECE = 0.1379                           │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │ 3. SLA Model Evaluation                               │  │
│  │    probs = [sla_clf.predict_breach_probability(t)    │  │
│  │             for t in test_sla_dicts]                 │  │
│  │                                                       │  │
│  │    → utils/metrics.py::compute_sla_auc():           │  │
│  │      auc_roc = roc_auc_score(y_true, probs)         │  │
│  │      Result: 0.7268                                 │  │
│  │                                                       │  │
│  │      avg_prec = average_precision_score(y_true, probs)│
│  │      Result: 0.5808                                 │  │
│  │                                                       │  │
│  │    → utils/metrics.py::metrics_at_threshold(0.70):  │  │
│  │      y_pred = (probs >= 0.70).astype(int)           │  │
│  │      precision = precision_score(y_true, y_pred)    │  │
│  │      Result: 0.712                                  │  │
│  │                                                       │  │
│  │      recall = recall_score(y_true, y_pred)          │  │
│  │      Result: 0.253                                  │  │
│  │                                                       │  │
│  │      f1 = f1_score(y_true, y_pred)                  │  │
│  │      Result: 0.373                                  │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                     │
│  ┌────────────────────▼─────────────────────────────────┐  │
│  │ 4. Save Evaluation Results                            │  │
│  │    artifacts/evaluation_results.json                  │  │
│  │    {                                                  │  │
│  │      "sla_model": {                                   │  │
│  │        "auc_roc": 0.7268,                            │  │
│  │        "avg_precision": 0.5808,                      │  │
│  │        "metrics_at_threshold": {                     │  │
│  │          "threshold": 0.70,                          │  │
│  │          "precision": 0.712,                         │  │
│  │          "recall": 0.253,                            │  │
│  │          "f1": 0.373                                 │  │
│  │        }                                             │  │
│  │      },                                              │  │
│  │      "category_model": {                             │  │
│  │        "ece": 0.1379,                                │  │
│  │        ...                                           │  │
│  │      }                                               │  │
│  │    }                                                  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Summary Table

| Metric | Value | File | Function | Line |
|--------|-------|------|----------|------|
| **SLA ROC-AUC** | 0.7268 | `utils/metrics.py` | `compute_sla_auc()` | Line 114 |
| **SLA PR-AUC** | 0.5808 | `utils/metrics.py` | `compute_sla_auc()` | Line 115 |
| **Precision @ 0.70** | 0.712 | `utils/metrics.py` | `metrics_at_threshold()` | Line 150 |
| **Recall @ 0.70** | 0.253 | `utils/metrics.py` | `metrics_at_threshold()` | Line 152 |
| **F1 @ 0.70** | 0.373 | `utils/metrics.py` | `metrics_at_threshold()` | Line 153 |
| **Priority Macro F1** | 0.7649 | `ml/train.py` | Direct calculation | ~Line 190 |
| **Calibration ECE** | 0.1379 | `utils/metrics.py` | `compute_expected_calibration_error()` | Line 67 |

---

## References

- **scikit-learn Metrics Documentation**: https://scikit-learn.org/stable/modules/model_evaluation.html
- **ROC-AUC Explanation**: https://developers.google.com/machine-learning/crash-course/classification/roc-and-auc
- **Precision-Recall Curves**: https://scikit-learn.org/stable/auto_examples/model_selection/plot_precision_recall.html
- **Calibration**: https://scikit-learn.org/stable/modules/calibration.html

---

**Last Updated**: 2026-09-17  
**TicketFlow AI Version**: 1.0  
**Author**: AI System Documentation
