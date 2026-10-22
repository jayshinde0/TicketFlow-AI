"""
research/research_logger.py — Comprehensive Research Data Logger

This module automatically logs all data, metrics, and artifacts required
for writing a research paper based on the TicketFlow AI system.

Author: Research Team
Project: ConfiTicketAI - Intelligent Auto-Handling of Support Tickets
"""

import json
import csv
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from loguru import logger
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support,
    confusion_matrix, classification_report, roc_auc_score, roc_curve
)

# Research output directory
RESEARCH_DIR = Path(__file__).parent.parent.parent / "research"
RESEARCH_DIR.mkdir(exist_ok=True)


class ResearchLogger:
    """
    Centralized logger for all research-related data collection.
    
    Features:
    - Dataset statistics and analysis
    - Preprocessing reports
    - Model training logs
    - Evaluation metrics
    - Experiment tracking
    - Visualization generation
    - Report exports (CSV, JSON, PDF)
    """
    
    def __init__(self, experiment_name: str = None):
        self.experiment_name = experiment_name or f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.experiment_dir = RESEARCH_DIR / "experiments" / self.experiment_name
        self.experiment_dir.mkdir(parents=True, exist_ok=True)
        
        self.metrics_log = []
        self.start_time = time.time()
        
        logger.info(f"Research Logger initialized: {self.experiment_name}")
    
    # ═══════════════════════════════════════════════════════════════════
    # 1. DATASET INFORMATION
    # ═══════════════════════════════════════════════════════════════════
    
    def log_dataset_info(self, df: pd.DataFrame, dataset_name: str = "training_data"):
        """
        Generate comprehensive dataset statistics report.
        
        Args:
            df: DataFrame containing ticket data
            dataset_name: Name of the dataset
        """
        logger.info(f"Logging dataset info for: {dataset_name}")
        
        # Basic statistics
        dataset_info = {
            "dataset_name": dataset_name,
            "timestamp": datetime.now().isoformat(),
            "total_tickets": len(df),
            "num_features": len(df.columns),
            "feature_names": list(df.columns),
            "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
        }
        
        # Category distribution
        if 'category' in df.columns:
            category_counts = df['category'].value_counts().to_dict()
            dataset_info['num_categories'] = len(category_counts)
            dataset_info['category_distribution'] = category_counts
            dataset_info['category_percentages'] = {
                k: f"{v/len(df)*100:.2f}%" for k, v in category_counts.items()
            }
        
        # Priority distribution
        if 'priority' in df.columns:
            priority_counts = df['priority'].value_counts().to_dict()
            dataset_info['priority_distribution'] = priority_counts
            dataset_info['priority_percentages'] = {
                k: f"{v/len(df)*100:.2f}%" for k, v in priority_counts.items()
            }
        
        # Missing values
        missing_values = df.isnull().sum().to_dict()
        dataset_info['missing_values'] = {
            k: v for k, v in missing_values.items() if v > 0
        }
        dataset_info['missing_percentage'] = {
            k: f"{v/len(df)*100:.2f}%" for k, v in missing_values.items() if v > 0
        }
        
        # Duplicate tickets
        duplicates = df.duplicated().sum()
        dataset_info['duplicate_tickets'] = int(duplicates)
        dataset_info['duplicate_percentage'] = f"{duplicates/len(df)*100:.2f}%"
        
        # Text length statistics (if description column exists)
        if 'description' in df.columns:
            df['text_length'] = df['description'].str.len()
            dataset_info['text_statistics'] = {
                'min_length': int(df['text_length'].min()),
                'max_length': int(df['text_length'].max()),
                'mean_length': float(df['text_length'].mean()),
                'median_length': float(df['text_length'].median()),
                'std_length': float(df['text_length'].std())
            }
        
        # Save to JSON
        output_path = RESEARCH_DIR / "dataset" / f"{dataset_name}_info.json"
        output_path.parent.mkdir(exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(dataset_info, f, indent=2)
        
        # Save to CSV
        df_summary = pd.DataFrame([dataset_info])
        csv_path = RESEARCH_DIR / "dataset" / f"{dataset_name}_summary.csv"
        df_summary.to_csv(csv_path, index=False)
        
        # Generate visualizations
        self._generate_dataset_visualizations(df, dataset_name)
        
        logger.success(f"Dataset info saved: {output_path}")
        return dataset_info
    
    def _generate_dataset_visualizations(self, df: pd.DataFrame, dataset_name: str):
        """Generate dataset distribution visualizations."""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # Category distribution
        if 'category' in df.columns:
            ax = axes[0, 0]
            category_counts = df['category'].value_counts()
            category_counts.plot(kind='bar', ax=ax, color='skyblue')
            ax.set_title('Category Distribution', fontsize=14, fontweight='bold')
            ax.set_xlabel('Category')
            ax.set_ylabel('Count')
            ax.tick_params(axis='x', rotation=45)
            
            # Add value labels on bars
            for container in ax.containers:
                ax.bar_label(container)
        
        # Priority distribution
        if 'priority' in df.columns:
            ax = axes[0, 1]
            priority_counts = df['priority'].value_counts()
            colors = {'Critical': 'red', 'High': 'orange', 'Medium': 'yellow', 'Low': 'green'}
            priority_counts.plot(
                kind='pie', ax=ax, autopct='%1.1f%%',
                colors=[colors.get(x, 'gray') for x in priority_counts.index]
            )
            ax.set_title('Priority Distribution', fontsize=14, fontweight='bold')
            ax.set_ylabel('')
        
        # Text length distribution
        if 'description' in df.columns:
            ax = axes[1, 0]
            text_lengths = df['description'].str.len()
            ax.hist(text_lengths, bins=50, color='lightcoral', edgecolor='black')
            ax.set_title('Text Length Distribution', fontsize=14, fontweight='bold')
            ax.set_xlabel('Text Length (characters)')
            ax.set_ylabel('Frequency')
            ax.axvline(text_lengths.mean(), color='red', linestyle='--', 
                      label=f'Mean: {text_lengths.mean():.0f}')
            ax.legend()
        
        # Missing values heatmap
        ax = axes[1, 1]
        missing_data = df.isnull().sum()
        missing_data = missing_data[missing_data > 0]
        if len(missing_data) > 0:
            missing_data.plot(kind='barh', ax=ax, color='salmon')
            ax.set_title('Missing Values by Column', fontsize=14, fontweight='bold')
            ax.set_xlabel('Count')
        else:
            ax.text(0.5, 0.5, 'No Missing Values', 
                   ha='center', va='center', fontsize=16)
            ax.set_title('Missing Values', fontsize=14, fontweight='bold')
            ax.axis('off')
        
        plt.tight_layout()
        
        # Save figure
        output_path = RESEARCH_DIR / "graphs" / f"{dataset_name}_distribution.png"
        output_path.parent.mkdir(exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Dataset visualizations saved: {output_path}")
    
    # ═══════════════════════════════════════════════════════════════════
    # 2. DATA PREPROCESSING REPORT
    # ═══════════════════════════════════════════════════════════════════
    
    def log_preprocessing_report(self, preprocessing_stats: Dict[str, Any]):
        """
        Log comprehensive preprocessing report.
        
        Args:
            preprocessing_stats: Dictionary containing preprocessing statistics
        """
        logger.info("Logging preprocessing report")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "experiment": self.experiment_name,
            **preprocessing_stats
        }
        
        # Save to JSON
        json_path = RESEARCH_DIR / "preprocessing" / f"preprocessing_report_{self.experiment_name}.json"
        json_path.parent.mkdir(exist_ok=True)
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Save to CSV
        df_report = pd.DataFrame([report])
        csv_path = RESEARCH_DIR / "preprocessing" / f"preprocessing_report_{self.experiment_name}.csv"
        df_report.to_csv(csv_path, index=False)
        
        logger.success(f"Preprocessing report saved: {json_path}")
        return report
    
    # ═══════════════════════════════════════════════════════════════════
    # 3. MODEL TRAINING LOGS
    # ═══════════════════════════════════════════════════════════════════
    
    def log_training_start(self, model_name: str, hyperparameters: Dict[str, Any]):
        """Log the start of model training."""
        self.training_start_time = time.time()
        
        training_log = {
            "experiment": self.experiment_name,
            "model_name": model_name,
            "hyperparameters": hyperparameters,
            "start_time": datetime.now().isoformat(),
            "start_timestamp": self.training_start_time
        }
        
        log_path = self.experiment_dir / "training_log.json"
        with open(log_path, 'w') as f:
            json.dump(training_log, f, indent=2)
        
        logger.info(f"Training started: {model_name}")
        return training_log
    
    def log_training_end(self, training_time: float = None):
        """Log the end of model training."""
        if training_time is None:
            training_time = time.time() - self.training_start_time
        
        log_path = self.experiment_dir / "training_log.json"
        with open(log_path, 'r') as f:
            training_log = json.load(f)
        
        training_log.update({
            "end_time": datetime.now().isoformat(),
            "training_time_seconds": training_time,
            "training_time_formatted": f"{training_time:.2f}s"
        })
        
        with open(log_path, 'w') as f:
            json.dump(training_log, f, indent=2)
        
        logger.success(f"Training completed in {training_time:.2f}s")
        return training_log
    
    # ═══════════════════════════════════════════════════════════════════
    # 4. EVALUATION METRICS
    # ═══════════════════════════════════════════════════════════════════
    
    def log_evaluation_metrics(
        self,
        y_true: List,
        y_pred: List,
        y_pred_proba: Optional[np.ndarray] = None,
        model_name: str = "model",
        labels: List[str] = None
    ):
        """
        Compute and log comprehensive evaluation metrics.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            y_pred_proba: Prediction probabilities (for ROC-AUC)
            model_name: Name of the model
            labels: Label names for classification report
        """
        logger.info(f"Computing evaluation metrics for {model_name}")
        
        # Basic metrics
        accuracy = accuracy_score(y_true, y_pred)
        precision, recall, f1, support = precision_recall_fscore_support(
            y_true, y_pred, average='weighted', zero_division=0
        )
        
        # Per-class metrics
        precision_per_class, recall_per_class, f1_per_class, support_per_class = \
            precision_recall_fscore_support(y_true, y_pred, average=None, zero_division=0)
        
        # Classification report
        class_report = classification_report(
            y_true, y_pred, target_names=labels, output_dict=True, zero_division=0
        )
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        
        metrics = {
            "experiment": self.experiment_name,
            "model_name": model_name,
            "timestamp": datetime.now().isoformat(),
            "accuracy": float(accuracy),
            "precision_weighted": float(precision),
            "recall_weighted": float(recall),
            "f1_score_weighted": float(f1),
            "support": int(sum(support)),
            "classification_report": class_report,
            "confusion_matrix": cm.tolist()
        }
        
        # ROC-AUC if probabilities provided
        if y_pred_proba is not None:
            try:
                roc_auc = roc_auc_score(y_true, y_pred_proba, multi_class='ovr', average='weighted')
                metrics['roc_auc_weighted'] = float(roc_auc)
            except Exception as e:
                logger.warning(f"Could not compute ROC-AUC: {e}")
        
        # Save metrics
        metrics_path = RESEARCH_DIR / "metrics" / f"{model_name}_metrics.json"
        metrics_path.parent.mkdir(exist_ok=True)
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        # Save classification report as CSV
        df_report = pd.DataFrame(class_report).transpose()
        report_path = RESEARCH_DIR / "metrics" / f"{model_name}_classification_report.csv"
        df_report.to_csv(report_path)
        
        # Generate confusion matrix visualization
        self._plot_confusion_matrix(cm, labels, model_name)
        
        # Generate ROC curve if applicable
        if y_pred_proba is not None and len(np.unique(y_true)) == 2:
            self._plot_roc_curve(y_true, y_pred_proba[:, 1], model_name)
        
        logger.success(f"Evaluation metrics saved: {metrics_path}")
        return metrics
    
    def _plot_confusion_matrix(self, cm: np.ndarray, labels: List[str], model_name: str):
        """Generate and save confusion matrix heatmap."""
        plt.figure(figsize=(10, 8))
        sns.heatmap(
            cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=labels, yticklabels=labels,
            cbar_kws={'label': 'Count'}
        )
        plt.title(f'Confusion Matrix - {model_name}', fontsize=16, fontweight='bold')
        plt.ylabel('True Label', fontsize=12)
        plt.xlabel('Predicted Label', fontsize=12)
        plt.tight_layout()
        
        output_path = RESEARCH_DIR / "confusion_matrix" / f"{model_name}_confusion_matrix.png"
        output_path.parent.mkdir(exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Confusion matrix saved: {output_path}")
    
    def _plot_roc_curve(self, y_true, y_scores, model_name: str):
        """Generate and save ROC curve."""
        fpr, tpr, thresholds = roc_curve(y_true, y_scores)
        roc_auc = roc_auc_score(y_true, y_scores)
        
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, color='darkorange', lw=2, 
                label=f'ROC curve (AUC = {roc_auc:.2f})')
        plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate', fontsize=12)
        plt.ylabel('True Positive Rate', fontsize=12)
        plt.title(f'ROC Curve - {model_name}', fontsize=16, fontweight='bold')
        plt.legend(loc="lower right")
        plt.grid(alpha=0.3)
        plt.tight_layout()
        
        output_path = RESEARCH_DIR / "graphs" / f"{model_name}_roc_curve.png"
        output_path.parent.mkdir(exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"ROC curve saved: {output_path}")
    
    # ═══════════════════════════════════════════════════════════════════
    # 5. ALGORITHM COMPARISON
    # ═══════════════════════════════════════════════════════════════════
    
    def log_model_comparison(self, comparison_results: List[Dict[str, Any]]):
        """
        Log comparison of multiple models.
        
        Args:
            comparison_results: List of dicts with model metrics
        """
        logger.info("Logging model comparison")
        
        df_comparison = pd.DataFrame(comparison_results)
        
        # Sort by F1 score
        df_comparison = df_comparison.sort_values('f1_score', ascending=False)
        
        # Save to CSV
        csv_path = RESEARCH_DIR / "reports" / "model_comparison.csv"
        csv_path.parent.mkdir(exist_ok=True)
        df_comparison.to_csv(csv_path, index=False)
        
        # Save to JSON
        json_path = RESEARCH_DIR / "reports" / "model_comparison.json"
        comparison_data = {
            "timestamp": datetime.now().isoformat(),
            "experiment": self.experiment_name,
            "models": comparison_results,
            "best_model": comparison_results[0] if comparison_results else None
        }
        with open(json_path, 'w') as f:
            json.dump(comparison_data, f, indent=2)
        
        # Generate comparison visualization
        self._plot_model_comparison(df_comparison)
        
        logger.success(f"Model comparison saved: {csv_path}")
        return comparison_data
    
    def _plot_model_comparison(self, df: pd.DataFrame):
        """Generate model comparison charts."""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        metrics = ['accuracy', 'precision', 'recall', 'f1_score']
        titles = ['Accuracy', 'Precision', 'Recall', 'F1 Score']
        
        for idx, (metric, title) in enumerate(zip(metrics, titles)):
            ax = axes[idx // 2, idx % 2]
            df_sorted = df.sort_values(metric, ascending=True)
            df_sorted.plot(
                x='model_name', y=metric, kind='barh', ax=ax,
                color='steelblue', legend=False
            )
            ax.set_title(f'{title} Comparison', fontsize=14, fontweight='bold')
            ax.set_xlabel(title)
            ax.set_ylabel('Model')
            
            # Add value labels
            for container in ax.containers:
                ax.bar_label(container, fmt='%.3f')
        
        plt.tight_layout()
        
        output_path = RESEARCH_DIR / "graphs" / "model_comparison.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Model comparison chart saved: {output_path}")
    
    # ═══════════════════════════════════════════════════════════════════
    # 6. EXPERIMENT TRACKING
    # ═══════════════════════════════════════════════════════════════════
    
    def save_experiment(self, experiment_data: Dict[str, Any]):
        """
        Save complete experiment data.
        
        Args:
            experiment_data: Complete experiment information
        """
        experiment_data.update({
            "experiment_name": self.experiment_name,
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": time.time() - self.start_time
        })
        
        # Save to experiment directory
        exp_path = self.experiment_dir / "experiment_summary.json"
        with open(exp_path, 'w') as f:
            json.dump(experiment_data, f, indent=2)
        
        # Also append to master experiments log
        master_log_path = RESEARCH_DIR / "experiments" / "all_experiments.jsonl"
        with open(master_log_path, 'a') as f:
            f.write(json.dumps(experiment_data) + '\n')
        
        logger.success(f"Experiment saved: {exp_path}")
        return experiment_data
    
    # ═══════════════════════════════════════════════════════════════════
    # 7. UTILITY METHODS
    # ═══════════════════════════════════════════════════════════════════
    
    def export_research_assets(self, output_zip: str = None):
        """Export all research assets as ZIP file."""
        import shutil
        
        if output_zip is None:
            output_zip = f"research_assets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        
        zip_path = RESEARCH_DIR / output_zip
        shutil.make_archive(
            str(zip_path).replace('.zip', ''),
            'zip',
            RESEARCH_DIR
        )
        
        logger.success(f"Research assets exported: {zip_path}")
        return zip_path


# Singleton instance
research_logger = ResearchLogger()
