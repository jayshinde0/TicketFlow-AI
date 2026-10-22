# Research Data Collection System

## ConfiTicketAI: Automatic Research Documentation

This directory contains all automatically generated research data, metrics, visualizations, and reports for publication in IEEE/Springer/Scopus journals.

---

## 📂 Directory Structure

```
research/
├── dataset/              # Dataset statistics and analysis
│   ├── dataset_analysis.json
│   ├── dataset_summary.csv
│   └── *_info.json
├── preprocessing/        # Preprocessing reports
│   └── preprocessing_report_*.json
├── experiments/          # Experiment logs
│   ├── exp_*/
│   └── all_experiments.jsonl
├── metrics/              # Evaluation metrics
│   ├── *_metrics.json
│   └── *_classification_report.csv
├── graphs/               # Visualizations (PNG, 300 DPI)
│   ├── class_distribution.png
│   ├── text_length_distribution.png
│   ├── model_comparison.png
│   └── *_roc_curve.png
├── confusion_matrix/     # Confusion matrix heatmaps
│   └── *_confusion_matrix.png
├── reports/              # Generated reports
│   ├── model_comparison.csv
│   └── model_comparison.json
├── architecture/         # System diagrams
│   └── (to be generated)
├── screenshots/          # Application screenshots
│   └── (to be captured)
└── paper_assets/         # Publication-ready assets
    └── latex/            # LaTeX tables
        ├── dataset_statistics.tex
        └── category_distribution.tex
```

---

## 🚀 Quick Start

### 1. Analyze Dataset

```bash
cd backend
python research/run_dataset_analysis.py
```

**Output**:
- Dataset statistics (JSON, CSV)
- Distribution visualizations
- LaTeX tables for paper

### 2. Train Models and Log Metrics

```python
from research.research_logger import research_logger

# Initialize experiment
logger = research_logger

# Log dataset
logger.log_dataset_info(df, "training_data")

# Log training
logger.log_training_start("RandomForest", hyperparameters)
# ... train model ...
logger.log_training_end()

# Log evaluation
logger.log_evaluation_metrics(y_true, y_pred, y_proba, labels=CATEGORIES)

# Compare models
logger.log_model_comparison(comparison_results)
```

### 3. Export All Assets

```python
from research.research_logger import research_logger

# Export everything as ZIP
zip_path = research_logger.export_research_assets()
print(f"All assets exported to: {zip_path}")
```

---

## 📊 What Gets Generated

### Dataset Analysis
✅ Total samples, features, memory usage  
✅ Category and priority distributions  
✅ Missing values report  
✅ Duplicate detection  
✅ Text statistics (length, word count)  
✅ Visualizations (bar charts, histograms, pie charts)  
✅ LaTeX tables for publication  

### Model Training
✅ Hyperparameters logged  
✅ Training time tracked  
✅ Random seed recorded  
✅ Train/test split ratios  
✅ Model version  

### Evaluation Metrics
✅ Accuracy  
✅ Precision (weighted, per-class)  
✅ Recall (weighted, per-class)  
✅ F1 Score (weighted, per-class)  
✅ ROC-AUC (if applicable)  
✅ Confusion Matrix  
✅ Classification Report  
✅ All metrics saved as JSON/CSV  
✅ Visualizations (confusion matrix heatmap, ROC curve)  

### Model Comparison
✅ Multiple algorithms compared  
✅ Side-by-side metrics table  
✅ Training time comparison  
✅ Prediction time comparison  
✅ Best model recommendation  
✅ Comparison charts  

### Experiment Tracking
✅ Every experiment logged  
✅ Timestamp recorded  
✅ Parameters saved  
✅ Results archived  
✅ Master log maintained  

---

## 📈 Visualization Gallery

All graphs are generated at **300 DPI** for publication quality.

### Dataset Visualizations
- **class_distribution.png**: Category and priority bar charts
- **text_length_distribution.png**: Text length histograms
- **missing_values.png**: Missing values by feature
- **correlation_matrix.png**: Feature correlations

### Model Visualizations
- **{model}_confusion_matrix.png**: Confusion matrix heatmap
- **{model}_roc_curve.png**: ROC curve with AUC score
- **model_comparison.png**: Multi-model performance comparison

---

## 📄 Report Formats

### JSON Reports
- Structured, machine-readable
- Complete data preservation
- Easy to parse programmatically

### CSV Reports
- Excel-compatible
- Easy to import into papers
- Readable in any spreadsheet software

### LaTeX Tables
- Ready to copy into paper
- Properly formatted
- Professional appearance

### PDF Reports (Coming Soon)
- Executive summary
- Complete analysis
- All visualizations included

---

## 🎓 Research Paper Mapping

### Table 1: Dataset Statistics
**Source**: `research/dataset/dataset_analysis.json`  
**LaTeX**: `research/paper_assets/latex/dataset_statistics.tex`

| Metric | Value |
|--------|-------|
| Total Samples | From analysis |
| Number of Categories | From analysis |
| Class Balance Ratio | From analysis |
| Completeness Score | From analysis |

### Table 2: Category Distribution
**Source**: `research/dataset/dataset_analysis.json`  
**LaTeX**: `research/paper_assets/latex/category_distribution.tex`

### Table 3: Model Comparison
**Source**: `research/reports/model_comparison.csv`

| Model | Accuracy | Precision | Recall | F1 Score | Training Time |
|-------|----------|-----------|--------|----------|---------------|
| Logistic Regression | ... | ... | ... | ... | ... |
| Random Forest | ... | ... | ... | ... | ... |
| ... | ... | ... | ... | ... | ... |

### Figure 1: Category Distribution
**Source**: `research/graphs/class_distribution.png`

### Figure 2: Confusion Matrix
**Source**: `research/confusion_matrix/{model}_confusion_matrix.png`

### Figure 3: ROC Curve
**Source**: `research/graphs/{model}_roc_curve.png`

### Figure 4: Model Comparison
**Source**: `research/graphs/model_comparison.png`

---

## 🔧 Integration Examples

### In Training Script

```python
from research.research_logger import ResearchLogger

# Initialize
logger = ResearchLogger(experiment_name="exp_20260730_v1")

# Log preprocessing
preprocessing_stats = {
    "lowercase": True,
    "stopwords_removed": 127,
    "vocabulary_size_before": 5432,
    "vocabulary_size_after": 4123,
    "avg_length_before": 156.3,
    "avg_length_after": 89.7
}
logger.log_preprocessing_report(preprocessing_stats)

# Log training
logger.log_training_start("RandomForest", {
    "n_estimators": 100,
    "max_depth": 10,
    "random_state": 42
})

# ... train model ...

logger.log_training_end(training_time=45.2)

# Log metrics
metrics = logger.log_evaluation_metrics(
    y_true=y_test,
    y_pred=y_pred,
    y_pred_proba=y_proba,
    model_name="RandomForest",
    labels=["Network", "Software", "Hardware", "Access", "Billing"]
)

# Save experiment
logger.save_experiment({
    "dataset": "customer_support_tickets.csv",
    "model": "RandomForest",
    "accuracy": metrics['accuracy'],
    "f1_score": metrics['f1_score_weighted']
})
```

### In API Endpoint

```python
from research.research_logger import research_logger

@app.post("/api/tickets")
async def create_ticket(ticket: TicketCreate):
    # ... existing code ...
    
    # Log for research
    research_logger.log_prediction(
        ticket_id=ticket_id,
        true_category=None,  # Unknown at submission
        pred_category=category,
        confidence=confidence,
        processing_time_ms=processing_time
    )
```

---

## 📦 Export Options

### Export as ZIP
```python
research_logger.export_research_assets("my_research_2024.zip")
```

### Export Individual Components
```python
# Export metrics only
metrics = research_logger.export_metrics()

# Export visualizations only
graphs = research_logger.export_graphs()

# Export LaTeX tables only
latex_tables = research_logger.export_latex_tables()
```

---

## ✅ Checklist for Paper Submission

- [ ] Dataset statistics generated
- [ ] All visualizations created (300 DPI)
- [ ] Model comparison table complete
- [ ] Evaluation metrics calculated
- [ ] Confusion matrices generated
- [ ] ROC curves plotted
- [ ] LaTeX tables formatted
- [ ] All experiments logged
- [ ] Performance benchmarks recorded
- [ ] Research assets exported
- [ ] Figures numbered and captioned
- [ ] Tables formatted consistently
- [ ] All metrics double-checked

---

## 🎯 Publication Checklist

### For IEEE Transactions
✅ Figures in PNG/PDF format (300 DPI minimum)  
✅ Tables in LaTeX format  
✅ All metrics with 3-4 decimal places  
✅ Confusion matrix as heatmap  
✅ ROC curves with AUC scores  
✅ Proper citations for datasets  

### For Springer
✅ High-resolution figures (300-600 DPI)  
✅ Color figures acceptable  
✅ Tables in LaTeX or Word format  
✅ Supplementary materials organized  

### For Scopus Indexed Journals
✅ Complete methodology description  
✅ Reproducible experiments  
✅ All data properly documented  
✅ Code availability statement  

---

## 🚧 Coming Soon

- [ ] RAG evaluation metrics
- [ ] HITL performance tracking
- [ ] System performance benchmarks
- [ ] Architecture diagrams
- [ ] Automated screenshot capture
- [ ] PDF report generation
- [ ] Excel workbook export
- [ ] Interactive dashboard

---

## 💡 Tips

1. **Run dataset analysis first** - It sets the foundation
2. **Log everything** - Better to have too much data than too little
3. **Generate visualizations early** - Helps identify issues
4. **Keep experiments organized** - Use descriptive experiment names
5. **Export regularly** - Don't lose data
6. **Review LaTeX tables** - Ensure formatting is correct
7. **Use high DPI** - 300 DPI minimum for publication

---

## 🤝 Contributing

To add new research metrics:

1. Create new method in `ResearchLogger`
2. Add visualization function
3. Update export system
4. Document in this README

---

## 📚 References

- **Dataset**: customer_support_tickets.csv
- **ML Framework**: scikit-learn
- **Visualization**: matplotlib, seaborn
- **Report Generation**: pandas, json

---

**Last Updated**: 2026-07-30  
**Status**: ✅ Core system operational  
**Next Phase**: RAG & HITL metrics
