# Quick Start: Model Performance Comparison

## TL;DR - Run This Command

```bash
cd backend
python run_model_analysis.py
```

This will:
- ✅ Compare 4 ML models (Naive Bayes, Logistic Regression, Random Forest, SVM)
- ✅ Calculate Accuracy, Precision, Recall, F1-Score
- ✅ Generate charts and confusion matrices
- ✅ Create a detailed report

## What You'll Get

### Console Output
```
Category Classification - Model Comparison Summary
═══════════════════════════════════════════════════════════
Model                     Accuracy   Precision   Recall   F1-Score
───────────────────────────────────────────────────────────
Naive Bayes               0.8234     0.8156      0.8190   0.8173
Logistic Regression       0.8756     0.8689      0.8721   0.8705
Random Forest             0.8534     0.8478      0.8501   0.8489
SVM (Linear)              0.8612     0.8545      0.8589   0.8567

🏆 Best Model: Logistic Regression (F1-Score: 0.8705)
```

### Generated Files
**Location:** `backend/ml/artifacts/visualizations/`

1. **Charts:**
   - `category_metrics_comparison.png` - Bar charts showing all metrics
   - `priority_metrics_comparison.png` - Bar charts for priority task
   - `category_per_class_f1_heatmap.png` - Performance by category
   - `priority_per_class_f1_heatmap.png` - Performance by priority
   - `training_time_comparison.png` - Speed comparison

2. **Confusion Matrices:** (4 models × 2 tasks = 8 files)
   - Shows correct predictions vs. errors

3. **Reports:**
   - `MODEL_COMPARISON_REPORT.md` - Detailed analysis
   - `model_comparison_summary.csv` - Excel-ready data

4. **Raw Data:**
   - `backend/ml/artifacts/model_comparison_YYYYMMDD_HHMMSS.json`

## Step-by-Step (If You Want Manual Control)

### Step 1: Run Comparison Only
```bash
cd backend
python -m ml.model_comparison
```
⏱️ Takes: 2-5 minutes

### Step 2: Generate Visualizations
```bash
python -m ml.visualize_comparison
```
⏱️ Takes: 30 seconds

## Understanding the Metrics

| Metric | What It Means | When High is Critical |
|--------|---------------|----------------------|
| **Accuracy** | Overall correctness | Balanced datasets |
| **Precision** | Of predictions, how many correct? | Avoid false alarms |
| **Recall** | Of actual cases, how many caught? | Don't miss important cases (Security!) |
| **F1-Score** | Balance of precision & recall | General purpose |

### Simple Example
Imagine 100 Security tickets:
- **90 correctly identified** → Recall = 90%
- **Model predicted 95 as Security, but 5 were wrong** → Precision = 90/95 = 94.7%
- **F1-Score** = Harmonic mean of both ≈ 92.3%

## What Model Should I Use?

### Quick Decision Guide

```
Need SPEED? 
  └─→ Use Naive Bayes (fastest)

Need ACCURACY?
  └─→ Use Logistic Regression or SVM

Need INTERPRETABILITY?
  └─→ Use Logistic Regression (can explain features)

Need to handle COMPLEX patterns?
  └─→ Use Random Forest
```

### Current Production Setup
- **Category Classification:** Logistic Regression ✅
- **Priority Classification:** Random Forest ✅

These are already good choices! But it's worth comparing to confirm.

## For Your Presentation/Report

### What to Show

1. **Methodology Slide:**
   - "Compared 4 algorithms: Naive Bayes, Logistic Regression, Random Forest, SVM"
   - "Evaluated on Category (10 classes) and Priority (4 classes)"
   - "Metrics: Accuracy, Precision, Recall, F1-Score"

2. **Results Slide:**
   - Show `*_metrics_comparison.png` charts
   - Highlight best performer

3. **Detailed Analysis:**
   - Show confusion matrix of best model
   - Show per-class heatmap

4. **Conclusion:**
   - "Selected [Model Name] based on F1-Score of [X.XX]"
   - "Achieves [accuracy]% accuracy on test set"

### Copy-Paste Ready Stats

After running the analysis, you'll get exact numbers like:

```
Category Classification:
- Best Model: Logistic Regression
- Accuracy: 87.56%
- Precision: 86.89%
- Recall: 87.21%
- F1-Score: 87.05%

Priority Classification:
- Best Model: Random Forest
- Accuracy: 83.45%
- F1-Score: 82.78%
```

## Common Issues

### "ModuleNotFoundError"
```bash
# Make sure you're in the backend directory
cd backend

# Run with module syntax
python -m ml.model_comparison
```

### "No training data found"
```bash
# Generate demo data first
python generate_enhanced_tickets.py
```

### Takes too long
This is normal! Model comparison trains 8 models (4 for category, 4 for priority).
Expected time: 2-5 minutes total.

## What's Happening Behind the Scenes?

1. **Loads data** from `ml/data/customer_support_tickets.csv`
2. **Splits** 70% train, 15% validation, 15% test
3. **Preprocesses** text (cleaning, TF-IDF vectorization)
4. **Trains** each model on training set
5. **Evaluates** on test set
6. **Computes** all metrics
7. **Generates** visualizations
8. **Saves** results

## Next Steps After Running

1. ✅ Open `ml/artifacts/visualizations/MODEL_COMPARISON_REPORT.md`
2. ✅ Review PNG images
3. ✅ Copy numbers to your presentation
4. ✅ (Optional) Change models in `ml/models/*.py` if needed
5. ✅ (Optional) Retrain production models: `python -m ml.train`

## Advanced: Custom Configuration

### Compare Only Specific Models
Edit `ml/model_comparison.py`:
```python
self.models = {
    "Logistic Regression": LogisticRegression(...),
    "Random Forest": RandomForestClassifier(...),
    # Remove others or add new ones
}
```

### Change Hyperparameters
```python
"Random Forest": RandomForestClassifier(
    n_estimators=500,  # More trees
    max_depth=15,      # Deeper trees
    # etc.
)
```

### Use Different Datasets
```python
df = load_training_data(data_dir="path/to/your/data", use_synthetic=False)
```

## Need More Details?

See **MODEL_PERFORMANCE_ANALYSIS.md** for:
- In-depth metric explanations
- Model selection strategies
- Troubleshooting guide
- Integration instructions

---

**Ready?** Just run:
```bash
cd backend
python run_model_analysis.py
```

That's it! 🚀
