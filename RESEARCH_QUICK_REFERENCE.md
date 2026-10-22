# Research System - Quick Reference Card

## 🚀 Quick Start Commands

```bash
# 1. Analyze dataset
cd backend
python research/run_dataset_analysis.py

# 2. View generated files
cd ../research
dir dataset      # Dataset statistics
dir graphs       # Visualizations
dir paper_assets # LaTeX tables

# 3. Export everything
python -c "from research import research_logger; research_logger.export_research_assets()"
```

---

## 📊 Key Metrics Generated

| Category | Metrics | Output Location |
|----------|---------|-----------------|
| **Dataset** | Total samples, categories, distributions, quality | `research/dataset/` |
| **Training** | Time, hyperparameters, epochs | `research/experiments/` |
| **Evaluation** | Accuracy, P/R/F1, ROC-AUC | `research/metrics/` |
| **Comparison** | Multi-model performance | `research/reports/` |
| **Visuals** | All charts (300 DPI) | `research/graphs/` |

---

## 💻 Code Snippets

### Analyze Dataset
```python
from research.dataset_analyzer import analyze_dataset
report = analyze_dataset("ml/data/customer_support_tickets.csv")
```

### Log Training
```python
from research import research_logger

research_logger.log_training_start("RandomForest", {
    "n_estimators": 100,
    "max_depth": 10,
    "random_state": 42
})
```

### Log Metrics
```python
research_logger.log_evaluation_metrics(
    y_true=y_test,
    y_pred=y_pred,
    y_pred_proba=y_proba,
    model_name="RandomForest",
    labels=["Network", "Software", "Hardware", "Access", "Billing"]
)
```

### Compare Models
```python
comparison = [
    {"model_name": "LogisticRegression", "accuracy": 0.85, "f1_score": 0.84},
    {"model_name": "RandomForest", "accuracy": 0.89, "f1_score": 0.88}
]
research_logger.log_model_comparison(comparison)
```

---

## 📁 Output Structure

```
research/
├── dataset/              ← Dataset stats (JSON, CSV)
├── preprocessing/        ← Preprocessing logs
├── experiments/          ← All experiment data
├── metrics/              ← Evaluation metrics
├── graphs/               ← Charts (PNG, 300 DPI)
├── confusion_matrix/     ← Confusion matrices
├── reports/              ← Comparison tables
└── paper_assets/         ← LaTeX tables, figures
    └── latex/
```

---

## 📈 Visualizations Generated

| Visualization | Filename | Description |
|---------------|----------|-------------|
| Category Distribution | `class_distribution.png` | Bar chart of categories |
| Text Length | `text_length_distribution.png` | Histogram of lengths |
| Missing Values | `missing_values.png` | Missing data by feature |
| Confusion Matrix | `{model}_confusion_matrix.png` | Classification accuracy |
| ROC Curve | `{model}_roc_curve.png` | Model performance |
| Model Comparison | `model_comparison.png` | Multi-model chart |

---

## 🎓 Paper Sections Mapping

| Paper Section | Data Source | Files Needed |
|---------------|-------------|--------------|
| **3.1 Dataset** | DatasetAnalyzer | `dataset_analysis.json`, `class_distribution.png` |
| **3.4 Models** | ModelComparator | `model_comparison.csv`, `model_comparison.png` |
| **4.2 Evaluation** | ResearchLogger | `*_metrics.json`, `*_confusion_matrix.png` |
| **4.3 Performance** | PerformanceMonitor | `performance_benchmark.json` (TBD) |

---

## ⚙️ Integration Points

### In Training Script (`ml/train.py`)
```python
from research import research_logger

# At start
research_logger.log_dataset_info(df, "training_data")

# Before training
research_logger.log_training_start("RandomForest", params)

# After training
research_logger.log_training_end(training_time)

# After evaluation
research_logger.log_evaluation_metrics(y_true, y_pred, y_proba, labels)
```

### In API (`main.py`)
```python
from research.performance_monitor import performance_monitor

@app.post("/api/tickets")
@performance_monitor.measure_execution_time  # TBD
async def create_ticket(ticket: TicketCreate):
    # ... existing code ...
```

---

## 📦 Export Options

```python
# Export everything as ZIP
research_logger.export_research_assets("research_2024.zip")

# Export specific components
from research import RESEARCH_DIR
import shutil

# Copy graphs only
shutil.copytree(RESEARCH_DIR / "graphs", "my_graphs/")

# Copy metrics only
shutil.copytree(RESEARCH_DIR / "metrics", "my_metrics/")
```

---

## ✅ Pre-Submission Checklist

- [ ] Dataset statistics generated
- [ ] All visualizations created (300 DPI)
- [ ] Model comparison complete
- [ ] Confusion matrices generated
- [ ] ROC curves plotted
- [ ] LaTeX tables formatted
- [ ] Experiments logged
- [ ] Research assets exported
- [ ] Figures numbered
- [ ] Tables formatted

---

## 🔧 Troubleshooting

### Dataset not found
```bash
# Check path
ls ml/data/customer_support_tickets.csv

# Or use absolute path
python -c "from research.dataset_analyzer import analyze_dataset; analyze_dataset('/full/path/to/dataset.csv')"
```

### Missing dependencies
```bash
pip install matplotlib seaborn pandas numpy scikit-learn
```

### Permission errors
```bash
# On Windows
icacls research /grant Users:F /T

# On Linux/Mac
chmod -R 755 research/
```

---

## 📞 Quick Help

| Issue | Solution |
|-------|----------|
| Can't find research module | Run from `backend/` directory |
| Import errors | Install: `pip install -r requirements.txt` |
| No visualizations | Check `research/graphs/` directory |
| LaTeX tables missing | Check `research/paper_assets/latex/` |
| Export fails | Ensure `research/` directory exists |

---

## 🎯 Common Tasks

### Task 1: Generate Dataset Report
```bash
cd backend
python research/run_dataset_analysis.py
```
**Output**: `research/dataset/dataset_analysis.json`

### Task 2: Log Model Training
```python
from research import research_logger
research_logger.log_training_start("MyModel", {"param": "value"})
# ... train ...
research_logger.log_training_end(120.5)  # 120.5 seconds
```

### Task 3: Create Confusion Matrix
```python
from research import research_logger
research_logger.log_evaluation_metrics(
    y_true, y_pred, y_proba,
    model_name="MyModel",
    labels=["Cat1", "Cat2", "Cat3"]
)
```
**Output**: `research/confusion_matrix/MyModel_confusion_matrix.png`

### Task 4: Compare Models
```python
results = [
    {"model_name": "Model1", "accuracy": 0.85, "f1_score": 0.84},
    {"model_name": "Model2", "accuracy": 0.89, "f1_score": 0.88}
]
research_logger.log_model_comparison(results)
```
**Output**: `research/reports/model_comparison.csv`

### Task 5: Export Everything
```python
from research import research_logger
zip_path = research_logger.export_research_assets()
print(f"Exported to: {zip_path}")
```

---

## 📚 Documentation Links

- **Full Guide**: `RESEARCH_PAPER_IMPLEMENTATION_GUIDE.md`
- **System Summary**: `RESEARCH_SYSTEM_SUMMARY.md`
- **Research README**: `research/README.md`
- **API Docs**: Run server, visit http://localhost:8000/docs

---

## 💡 Pro Tips

1. **Run analysis first** - Before writing paper
2. **Export often** - Don't lose data
3. **Use descriptive names** - For experiments
4. **Check LaTeX** - Before copy-paste
5. **300 DPI minimum** - For all figures
6. **Track seeds** - For reproducibility
7. **Log everything** - Better too much than too little

---

## 🆘 Emergency Commands

```bash
# Rebuild research directory
rm -rf research/
python research/run_dataset_analysis.py

# Reset experiments
rm -rf research/experiments/*

# Clear graphs
rm -rf research/graphs/*

# Start fresh
git clean -fdx research/
```

---

**Last Updated**: 2026-07-30  
**Version**: 1.0.0  
**Status**: Core system operational ✅
