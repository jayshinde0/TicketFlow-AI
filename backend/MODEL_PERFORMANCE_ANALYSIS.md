# Model Performance Analysis Guide

## Overview

This guide explains how to evaluate and compare different machine learning models for TicketFlow AI's ticket classification system. The analysis compares **four different algorithms** across **two classification tasks** (Category and Priority).

## Models Evaluated

### 1. Naive Bayes (MultinomialNB)
- **Type:** Probabilistic classifier
- **Best for:** Text classification with bag-of-words features
- **Speed:** Very fast training and prediction
- **Assumption:** Features are conditionally independent

### 2. Logistic Regression
- **Type:** Linear classifier
- **Best for:** Balanced accuracy and interpretability
- **Speed:** Fast
- **Feature:** Provides probability scores
- **Current use:** Category classification in production

### 3. Random Forest
- **Type:** Ensemble of decision trees
- **Best for:** Handling non-linear relationships
- **Speed:** Slower training, fast prediction
- **Feature:** Feature importance rankings
- **Current use:** Priority classification in production

### 4. Support Vector Machine (SVM)
- **Type:** Maximum margin classifier
- **Best for:** High-dimensional spaces
- **Speed:** Slower for large datasets
- **Feature:** Effective in high-dimensional feature spaces

## Classification Tasks

### Task 1: Category Classification
Predict the category of a support ticket from 10 possible categories:
- Network
- Auth (Authentication)
- Software
- Hardware
- Access
- Billing
- Email
- Security
- ServiceRequest
- Database

### Task 2: Priority Classification
Predict the urgency level from 4 priority levels:
- Low
- Medium
- High
- Critical

## Performance Metrics Explained

### 1. Accuracy
```
Accuracy = (Correct Predictions) / (Total Predictions)
```
- **Range:** 0.0 to 1.0 (higher is better)
- **Use case:** Overall correctness
- **Limitation:** Can be misleading with imbalanced classes

### 2. Precision
```
Precision = True Positives / (True Positives + False Positives)
```
- **Range:** 0.0 to 1.0 (higher is better)
- **Meaning:** Of all predicted positive cases, how many were actually positive?
- **Use case:** When false positives are costly

### 3. Recall (Sensitivity)
```
Recall = True Positives / (True Positives + False Negatives)
```
- **Range:** 0.0 to 1.0 (higher is better)
- **Meaning:** Of all actual positive cases, how many did we catch?
- **Use case:** When missing positives is costly (e.g., Security tickets)

### 4. F1-Score
```
F1 = 2 × (Precision × Recall) / (Precision + Recall)
```
- **Range:** 0.0 to 1.0 (higher is better)
- **Meaning:** Harmonic mean of precision and recall
- **Use case:** Balance between precision and recall

### Macro vs Weighted Averaging
- **Macro:** Simple average across all classes (treats all classes equally)
- **Weighted:** Weighted by class support (accounts for class imbalance)

## Running the Analysis

### Quick Start
```bash
# Run complete analysis (comparison + visualizations)
python run_model_analysis.py
```

### Step-by-Step

#### Step 1: Run Model Comparison
```bash
cd backend
python -m ml.model_comparison
```

**Output:**
- `ml/artifacts/model_comparison_YYYYMMDD_HHMMSS.json`
- Console output with performance metrics

#### Step 2: Generate Visualizations
```bash
python -m ml.visualize_comparison
```

**Output Location:** `ml/artifacts/visualizations/`

**Generated Files:**
- `category_metrics_comparison.png` - Bar charts for Category task
- `priority_metrics_comparison.png` - Bar charts for Priority task
- `category_per_class_f1_heatmap.png` - Heatmap of F1 scores by class
- `priority_per_class_f1_heatmap.png` - Heatmap for Priority task
- `*_confusion_matrix.png` - One for each model × task combination
- `training_time_comparison.png` - Training time across models
- `MODEL_COMPARISON_REPORT.md` - Detailed markdown report
- `model_comparison_summary.csv` - CSV summary for spreadsheets

### Advanced Options

```bash
# Use specific comparison file
python -m ml.visualize_comparison --input ml/artifacts/model_comparison_20260925_120000.json

# Skip visualization (comparison only)
python -m ml.model_comparison
```

## Understanding the Results

### 1. Metrics Comparison Charts
- **4 subplots:** Accuracy, Precision, Recall, F1-Score
- **Compare:** Model performance side-by-side
- **Look for:** Highest bars (best performance)

### 2. Per-Class Performance Heatmaps
- **Rows:** Different models
- **Columns:** Different classes (categories or priorities)
- **Colors:** Green = good, Red = poor
- **Use:** Identify which model handles which class best

### 3. Confusion Matrices
- **Rows:** True labels
- **Columns:** Predicted labels
- **Diagonal:** Correct predictions
- **Off-diagonal:** Misclassifications
- **Use:** Understand error patterns

### 4. Training Time Comparison
- **Compare:** Training speed across models
- **Trade-off:** Performance vs. speed
- **Consider:** Real-time requirements

## Example Output Interpretation

### Sample Console Output
```
═══════════════════════════════════════════════════════════════════════════════
Category Classification - Model Comparison Summary
═══════════════════════════════════════════════════════════════════════════════
Model                     Accuracy   Precision    Recall     F1-Score  
──────────────────────────────────────────────────────────────────────────────
Naive Bayes               0.8234     0.8156       0.8190     0.8173    
Logistic Regression       0.8756     0.8689       0.8721     0.8705    
Random Forest             0.8534     0.8478       0.8501     0.8489    
SVM (Linear)              0.8612     0.8545       0.8589     0.8567    
──────────────────────────────────────────────────────────────────────────────

🏆 Best Model: Logistic Regression (F1-Score: 0.8705)
```

### Interpretation
- **Winner:** Logistic Regression
- **Why:** Highest F1-Score (best balance of precision and recall)
- **Note:** Naive Bayes is fastest but less accurate
- **Trade-off:** Random Forest is slower but handles complex patterns

## Choosing the Best Model

### Decision Criteria

#### 1. Performance-First
Choose the model with the **highest F1-Score** for balanced performance.

#### 2. Speed-Critical Applications
If real-time prediction is critical:
- Choose **Naive Bayes** (fastest)
- Or **Logistic Regression** (good balance)

#### 3. Class-Specific Requirements
For critical classes (e.g., Security):
- Check **per-class recall**
- Choose model with highest recall for that class

#### 4. Interpretability
If you need to explain predictions:
- **Logistic Regression:** Feature weights
- **Random Forest:** Feature importance
- Avoid: SVM (less interpretable)

### Example Decision Tree

```
Is prediction speed critical (< 10ms)?
├─ Yes → Use Naive Bayes or Logistic Regression
└─ No
    └─ Are certain classes critical (Security, Billing)?
        ├─ Yes → Check per-class recall, choose highest
        └─ No → Choose model with highest overall F1-Score
```

## Integration with Existing Code

### Current Production Models
```python
# backend/ml/models/category_classifier.py
# Uses: Logistic Regression (C=10.0)

# backend/ml/models/priority_classifier.py
# Uses: Random Forest (200 estimators)
```

### How to Switch Models

#### Option 1: Replace in Existing Code
Edit `ml/models/category_classifier.py`:
```python
# Change from Logistic Regression to Random Forest
from sklearn.ensemble import RandomForestClassifier

self.classifier = RandomForestClassifier(
    n_estimators=200,
    class_weight='balanced',
    random_state=42,
    n_jobs=-1
)
```

#### Option 2: Create New Model Class
Create `ml/models/category_classifier_nb.py` for Naive Bayes version.

#### Option 3: Model Factory Pattern
```python
# ml/models/model_factory.py
def get_category_classifier(model_type='logistic'):
    if model_type == 'naive_bayes':
        return MultinomialNB(alpha=1.0)
    elif model_type == 'random_forest':
        return RandomForestClassifier(...)
    # etc.
```

## Performance Benchmarks

### Expected Ranges (on synthetic data)

#### Category Classification
| Model | Accuracy | Precision | Recall | F1-Score |
|-------|----------|-----------|--------|----------|
| Target | > 0.85 | > 0.85 | > 0.85 | > 0.85 |
| Naive Bayes | 0.80-0.85 | 0.78-0.83 | 0.80-0.85 | 0.79-0.84 |
| Logistic Regression | 0.85-0.90 | 0.84-0.89 | 0.85-0.90 | 0.85-0.90 |
| Random Forest | 0.83-0.88 | 0.82-0.87 | 0.83-0.88 | 0.83-0.88 |
| SVM | 0.84-0.89 | 0.83-0.88 | 0.84-0.89 | 0.84-0.89 |

#### Priority Classification
| Model | F1-Score Range |
|-------|----------------|
| Naive Bayes | 0.75-0.82 |
| Logistic Regression | 0.78-0.85 |
| Random Forest | 0.80-0.87 |
| SVM | 0.79-0.86 |

### Training Time (Approximate)
- **Naive Bayes:** < 1 second
- **Logistic Regression:** 2-5 seconds
- **Random Forest:** 10-30 seconds
- **SVM:** 30-120 seconds (depends on kernel)

## Troubleshooting

### Issue: Low Accuracy (< 0.70)
**Possible causes:**
1. Insufficient training data
2. Poor feature engineering
3. Class imbalance
4. Wrong hyperparameters

**Solutions:**
```python
# 1. Check dataset size
df = load_training_data(use_synthetic=True)
print(f"Samples: {len(df)}")

# 2. Balance classes
from imblearn.over_sampling import SMOTE
X_train, y_train = SMOTE().fit_resample(X_train, y_train)

# 3. Tune hyperparameters
from sklearn.model_selection import GridSearchCV
param_grid = {'C': [1, 5, 10, 20, 50]}
grid = GridSearchCV(LogisticRegression(), param_grid, cv=5)
```

### Issue: Training Takes Too Long
**Solutions:**
1. Reduce dataset size for testing
2. Use Naive Bayes for quick iterations
3. Reduce Random Forest estimators
4. Use linear SVM instead of RBF kernel

### Issue: Memory Error
**Solutions:**
```python
# Use sparse matrices
from scipy.sparse import csr_matrix
X_train_sparse = csr_matrix(X_train)

# Reduce feature dimensions
from sklearn.decomposition import TruncatedSVD
svd = TruncatedSVD(n_components=1000)
X_reduced = svd.fit_transform(X_train)
```

### Issue: Models Not Importing
**Solution:**
```bash
# Ensure you're in the backend directory
cd backend

# Check Python path
python -c "import sys; print(sys.path)"

# Run with module syntax
python -m ml.model_comparison
```

## Using Results for Presentation/Report

### Include These Visualizations
1. **Metrics Comparison Chart** - Shows overall performance
2. **Per-Class Heatmap** - Shows detailed performance
3. **Best Model Confusion Matrix** - Shows error patterns
4. **Training Time Chart** - Shows efficiency

### Key Points to Present
1. "Compared 4 ML algorithms: Naive Bayes, Logistic Regression, Random Forest, SVM"
2. "Evaluated on 2 tasks: Category (10 classes) and Priority (4 classes)"
3. "Used 4 metrics: Accuracy, Precision, Recall, F1-Score"
4. "Best model for Category: [Model Name] with F1-Score: [X.XXXX]"
5. "Best model for Priority: [Model Name] with F1-Score: [X.XXXX]"

### Sample Presentation Slide Structure
```
Slide 1: Model Comparison Methodology
- 4 algorithms tested
- 2 classification tasks
- 70/15/15 train/val/test split
- TF-IDF + metadata features

Slide 2: Performance Metrics
- Show metrics comparison chart
- Highlight best model

Slide 3: Detailed Analysis
- Show per-class heatmap
- Explain strengths/weaknesses

Slide 4: Selected Model
- Show confusion matrix
- Justify choice
```

## Advanced: Cross-Validation

For more robust evaluation, use k-fold cross-validation:

```python
from sklearn.model_selection import cross_val_score

# 5-fold cross-validation
cv_scores = cross_val_score(
    LogisticRegression(C=10.0),
    X_train,
    y_train,
    cv=5,
    scoring='f1_macro'
)

print(f"CV F1 Scores: {cv_scores}")
print(f"Mean: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
```

## References

- **Scikit-learn Documentation:** https://scikit-learn.org/
- **Model Comparison Best Practices:** [Machine Learning Mastery](https://machinelearningmastery.com/)
- **Confusion Matrix Guide:** https://en.wikipedia.org/wiki/Confusion_matrix

## Next Steps

1. **Run the analysis:**
   ```bash
   python run_model_analysis.py
   ```

2. **Review the generated report:**
   - Open `ml/artifacts/visualizations/MODEL_COMPARISON_REPORT.md`

3. **Analyze visualizations:**
   - Check PNG files in `ml/artifacts/visualizations/`

4. **Choose your model:**
   - Based on performance requirements
   - Consider speed vs. accuracy trade-offs

5. **Update production code:**
   - Modify model classes if needed
   - Retrain with `python -m ml.train`

---

**Questions?** Check existing model implementations in `backend/ml/models/` or review `ml/train.py` for training pipeline details.
