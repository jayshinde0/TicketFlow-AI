"""
ml/visualize_comparison.py — Generate visualizations for model comparison results.

Creates:
- Performance comparison bar charts
- Per-class performance heatmaps
- Confusion matrices
- Training time comparison
- Detailed performance report (Markdown)

Run with: python -m ml.visualize_comparison [comparison_json_file]
"""

import sys
import json
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stdout, format="{time:HH:mm:ss} | {level} | {message}", level="INFO")

sys.path.insert(0, str(Path(__file__).parent.parent))

ARTIFACT_DIR = Path(__file__).parent / "artifacts"
OUTPUT_DIR = ARTIFACT_DIR / "visualizations"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_comparison_results(json_path: Path = None) -> dict:
    """Load model comparison results from JSON file."""
    if json_path is None:
        # Find most recent comparison file
        comparison_files = sorted(ARTIFACT_DIR.glob("model_comparison_*.json"))
        if not comparison_files:
            raise FileNotFoundError(
                "No comparison results found. Run ml.model_comparison first."
            )
        json_path = comparison_files[-1]

    logger.info(f"Loading results from: {json_path}")
    with open(json_path, "r") as f:
        return json.load(f)


def plot_metrics_comparison(results: list, task_name: str, output_dir: Path):
    """Create bar chart comparing metrics across models."""
    models = [r["model_name"] for r in results]
    metrics = ["accuracy", "precision_macro", "recall_macro", "f1_macro"]
    metric_labels = ["Accuracy", "Precision", "Recall", "F1-Score"]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f"{task_name} Classification - Model Performance Comparison", fontsize=16)

    for idx, (metric, label) in enumerate(zip(metrics, metric_labels)):
        ax = axes[idx // 2, idx % 2]
        values = [r["metrics"][metric] for r in results]

        bars = ax.bar(models, values, color=plt.cm.viridis(np.linspace(0.3, 0.9, len(models))))
        ax.set_ylabel(label, fontsize=12)
        ax.set_ylim([0, 1.05])
        ax.set_title(f"{label} Comparison", fontsize=13, fontweight="bold")
        ax.grid(axis="y", alpha=0.3)

        # Add value labels on bars
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + 0.02,
                f"{val:.3f}",
                ha="center",
                va="bottom",
                fontsize=10,
            )

        # Rotate x-axis labels
        ax.set_xticklabels(models, rotation=15, ha="right")

    plt.tight_layout()
    output_path = output_dir / f"{task_name.lower()}_metrics_comparison.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    logger.info(f"  ✓ Saved: {output_path}")
    plt.close()


def plot_confusion_matrix(
    cm: list, labels: list, model_name: str, task_name: str, output_dir: Path
):
    """Plot confusion matrix heatmap."""
    cm_array = np.array(cm)

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(
        cm_array,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=labels,
        yticklabels=labels,
        ax=ax,
        cbar_kws={"label": "Count"},
    )
    ax.set_title(
        f"{task_name} - {model_name}\nConfusion Matrix",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_ylabel("True Label", fontsize=12)
    ax.set_xlabel("Predicted Label", fontsize=12)

    plt.tight_layout()
    safe_name = model_name.replace(" ", "_").replace("(", "").replace(")", "").lower()
    output_path = (
        output_dir / f"{task_name.lower()}_{safe_name}_confusion_matrix.png"
    )
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    logger.info(f"  ✓ Saved: {output_path}")
    plt.close()


def plot_per_class_performance(results: list, task_name: str, output_dir: Path):
    """Create heatmap of per-class F1 scores across models."""
    models = [r["model_name"] for r in results]

    # Get all class names
    first_result = results[0]
    class_names = list(first_result["per_class_metrics"].keys())

    # Build matrix: rows=models, cols=classes
    f1_matrix = []
    for result in results:
        f1_scores = [
            result["per_class_metrics"].get(cls, {}).get("f1-score", 0.0)
            for cls in class_names
        ]
        f1_matrix.append(f1_scores)

    f1_array = np.array(f1_matrix)

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.heatmap(
        f1_array,
        annot=True,
        fmt=".3f",
        cmap="RdYlGn",
        xticklabels=class_names,
        yticklabels=models,
        vmin=0,
        vmax=1,
        ax=ax,
        cbar_kws={"label": "F1-Score"},
    )
    ax.set_title(
        f"{task_name} - Per-Class F1-Score Comparison",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_xlabel("Class", fontsize=12)
    ax.set_ylabel("Model", fontsize=12)

    plt.tight_layout()
    output_path = output_dir / f"{task_name.lower()}_per_class_f1_heatmap.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    logger.info(f"  ✓ Saved: {output_path}")
    plt.close()


def plot_training_time_comparison(cat_results: list, pri_results: list, output_dir: Path):
    """Compare training times across models."""
    models = [r["model_name"] for r in cat_results]
    cat_times = [r["train_time_seconds"] for r in cat_results]
    pri_times = [r["train_time_seconds"] for r in pri_results]

    x = np.arange(len(models))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 6))
    bars1 = ax.bar(x - width / 2, cat_times, width, label="Category", color="#3498db")
    bars2 = ax.bar(x + width / 2, pri_times, width, label="Priority", color="#e74c3c")

    ax.set_ylabel("Training Time (seconds)", fontsize=12)
    ax.set_title("Model Training Time Comparison", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=15, ha="right")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + 0.5,
                f"{height:.2f}s",
                ha="center",
                va="bottom",
                fontsize=9,
            )

    plt.tight_layout()
    output_path = output_dir / "training_time_comparison.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    logger.info(f"  ✓ Saved: {output_path}")
    plt.close()


def generate_markdown_report(data: dict, output_dir: Path):
    """Generate detailed Markdown report."""
    report_lines = [
        "# TicketFlow AI - Model Performance Comparison Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Run ID:** {data['run_id']}",
        "",
        "---",
        "",
        "## Dataset Information",
        "",
        f"- **Total Samples:** {data['dataset_info']['total_samples']}",
        f"- **Training Samples:** {data['dataset_info']['train_samples']}",
        f"- **Test Samples:** {data['dataset_info']['test_samples']}",
        f"- **Feature Dimension:** {data['dataset_info']['feature_dimension']}",
        "",
        "---",
        "",
    ]

    # Category Classification
    report_lines.extend(
        [
            "## 1. Category Classification Results",
            "",
            "### Overall Performance Comparison",
            "",
            "| Model | Accuracy | Precision | Recall | F1-Score | Training Time |",
            "|-------|----------|-----------|--------|----------|---------------|",
        ]
    )

    for result in data["category_classification"]:
        m = result["metrics"]
        report_lines.append(
            f"| {result['model_name']} | {m['accuracy']:.4f} | "
            f"{m['precision_macro']:.4f} | {m['recall_macro']:.4f} | "
            f"{m['f1_macro']:.4f} | {result['train_time_seconds']:.2f}s |"
        )

    # Best model
    best_cat = max(
        data["category_classification"], key=lambda x: x["metrics"]["f1_macro"]
    )
    report_lines.extend(
        [
            "",
            f"**🏆 Best Model:** {best_cat['model_name']} (F1-Score: {best_cat['metrics']['f1_macro']:.4f})",
            "",
            "### Per-Category Performance",
            "",
        ]
    )

    # Per-category table
    class_names = list(best_cat["per_class_metrics"].keys())
    report_lines.append("| Category | Model | Precision | Recall | F1-Score |")
    report_lines.append("|----------|-------|-----------|--------|----------|")

    for cls in class_names:
        for result in data["category_classification"]:
            metrics = result["per_class_metrics"].get(cls, {})
            if metrics:
                report_lines.append(
                    f"| {cls} | {result['model_name']} | {metrics['precision']:.4f} | "
                    f"{metrics['recall']:.4f} | {metrics['f1-score']:.4f} |"
                )

    report_lines.extend(["", "---", ""])

    # Priority Classification
    report_lines.extend(
        [
            "## 2. Priority Classification Results",
            "",
            "### Overall Performance Comparison",
            "",
            "| Model | Accuracy | Precision | Recall | F1-Score | Training Time |",
            "|-------|----------|-----------|--------|----------|---------------|",
        ]
    )

    for result in data["priority_classification"]:
        m = result["metrics"]
        report_lines.append(
            f"| {result['model_name']} | {m['accuracy']:.4f} | "
            f"{m['precision_macro']:.4f} | {m['recall_macro']:.4f} | "
            f"{m['f1_macro']:.4f} | {result['train_time_seconds']:.2f}s |"
        )

    best_pri = max(
        data["priority_classification"], key=lambda x: x["metrics"]["f1_macro"]
    )
    report_lines.extend(
        [
            "",
            f"**🏆 Best Model:** {best_pri['model_name']} (F1-Score: {best_pri['metrics']['f1_macro']:.4f})",
            "",
            "---",
            "",
            "## Key Findings",
            "",
            "### Category Classification",
            f"- Best performing model: **{best_cat['model_name']}**",
            f"- Highest accuracy: **{best_cat['metrics']['accuracy']:.4f}**",
            f"- Macro F1-Score: **{best_cat['metrics']['f1_macro']:.4f}**",
            "",
            "### Priority Classification",
            f"- Best performing model: **{best_pri['model_name']}**",
            f"- Highest accuracy: **{best_pri['metrics']['accuracy']:.4f}**",
            f"- Macro F1-Score: **{best_pri['metrics']['f1_macro']:.4f}**",
            "",
            "---",
            "",
            "## Recommendations",
            "",
            "1. **Category Classification:** Use " + best_cat['model_name'],
            "2. **Priority Classification:** Use " + best_pri['model_name'],
            "",
            "---",
            "",
            "*Generated by TicketFlow AI Model Comparison Tool*",
        ]
    )

    # Save report
    output_path = output_dir / "MODEL_COMPARISON_REPORT.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    logger.info(f"  ✓ Saved: {output_path}")


def visualize_all(json_path: Path = None):
    """Generate all visualizations and reports."""
    logger.info("═" * 70)
    logger.info("TicketFlow AI - Model Comparison Visualization")
    logger.info("═" * 70)

    # Load data
    data = load_comparison_results(json_path)

    logger.info("\n[1/6] Generating metric comparison charts...")
    plot_metrics_comparison(
        data["category_classification"], "Category", OUTPUT_DIR
    )
    plot_metrics_comparison(
        data["priority_classification"], "Priority", OUTPUT_DIR
    )

    logger.info("\n[2/6] Generating per-class performance heatmaps...")
    plot_per_class_performance(
        data["category_classification"], "Category", OUTPUT_DIR
    )
    plot_per_class_performance(
        data["priority_classification"], "Priority", OUTPUT_DIR
    )

    logger.info("\n[3/6] Generating confusion matrices...")
    # Get class labels
    from ml.data_loader import ALL_CATEGORIES, ALL_PRIORITIES

    for result in data["category_classification"]:
        plot_confusion_matrix(
            result["confusion_matrix"],
            ALL_CATEGORIES,
            result["model_name"],
            "Category",
            OUTPUT_DIR,
        )

    for result in data["priority_classification"]:
        plot_confusion_matrix(
            result["confusion_matrix"],
            ALL_PRIORITIES,
            result["model_name"],
            "Priority",
            OUTPUT_DIR,
        )

    logger.info("\n[4/6] Generating training time comparison...")
    plot_training_time_comparison(
        data["category_classification"],
        data["priority_classification"],
        OUTPUT_DIR,
    )

    logger.info("\n[5/6] Generating detailed markdown report...")
    generate_markdown_report(data, OUTPUT_DIR)

    logger.info("\n[6/6] Creating summary CSV...")
    create_summary_csv(data, OUTPUT_DIR)

    logger.info("\n" + "═" * 70)
    logger.info(f"✓ All visualizations saved to: {OUTPUT_DIR}")
    logger.info("═" * 70)


def create_summary_csv(data: dict, output_dir: Path):
    """Create CSV summary of all results."""
    rows = []

    for result in data["category_classification"]:
        rows.append(
            {
                "Task": "Category",
                "Model": result["model_name"],
                "Accuracy": result["metrics"]["accuracy"],
                "Precision": result["metrics"]["precision_macro"],
                "Recall": result["metrics"]["recall_macro"],
                "F1_Score": result["metrics"]["f1_macro"],
                "Training_Time_s": result["train_time_seconds"],
            }
        )

    for result in data["priority_classification"]:
        rows.append(
            {
                "Task": "Priority",
                "Model": result["model_name"],
                "Accuracy": result["metrics"]["accuracy"],
                "Precision": result["metrics"]["precision_macro"],
                "Recall": result["metrics"]["recall_macro"],
                "F1_Score": result["metrics"]["f1_macro"],
                "Training_Time_s": result["train_time_seconds"],
            }
        )

    df = pd.DataFrame(rows)
    output_path = output_dir / "model_comparison_summary.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"  ✓ Saved: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Visualize model comparison results"
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=None,
        help="Path to comparison JSON file (uses latest if not specified)",
    )
    args = parser.parse_args()

    try:
        visualize_all(args.input)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
