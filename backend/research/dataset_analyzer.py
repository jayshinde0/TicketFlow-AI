"""
research/dataset_analyzer.py — Comprehensive Dataset Analysis

Generates detailed dataset statistics, visualizations, and reports
for research paper documentation.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, Any
from loguru import logger

from research.research_logger import RESEARCH_DIR


class DatasetAnalyzer:
    """
    Comprehensive dataset analysis for research documentation.
    """
    
    def __init__(self, dataset_path: str):
        self.dataset_path = Path(dataset_path)
        self.df = pd.read_csv(dataset_path)
        self.analysis_timestamp = datetime.now().isoformat()
        
        logger.info(f"Dataset loaded: {len(self.df)} samples")
    
    def generate_complete_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive dataset report with all statistics.
        
        Returns:
            Complete analysis report
        """
        logger.info("Generating complete dataset analysis report...")
        
        report = {
            "metadata": self._get_metadata(),
            "basic_statistics": self._get_basic_statistics(),
            "distribution_analysis": self._get_distribution_analysis(),
            "data_quality": self._get_data_quality_report(),
            "text_analysis": self._get_text_analysis(),
            "temporal_analysis": self._get_temporal_analysis() if 'created_at' in self.df.columns else {},
        }
        
        # Save report
        self._save_report(report)
        
        # Generate all visualizations
        self._generate_all_visualizations()
        
        # Generate LaTeX table
        self._generate_latex_tables(report)
        
        logger.success("Dataset analysis complete!")
        return report
    
    def _get_metadata(self) -> Dict[str, Any]:
        """Get dataset metadata."""
        return {
            "dataset_name": self.dataset_path.name,
            "dataset_path": str(self.dataset_path),
            "analysis_timestamp": self.analysis_timestamp,
            "total_samples": len(self.df),
            "total_features": len(self.df.columns),
            "feature_names": list(self.df.columns),
            "dtypes": {col: str(dtype) for col, dtype in self.df.dtypes.items()},
            "memory_usage_mb": float(self.df.memory_usage(deep=True).sum() / 1024 / 1024)
        }
    
    def _get_basic_statistics(self) -> Dict[str, Any]:
        """Calculate basic statistical measures."""
        stats = {
            "shape": {
                "rows": int(self.df.shape[0]),
                "columns": int(self.df.shape[1])
            },
            "numeric_summary": {},
            "categorical_summary": {}
        }
        
        # Numeric columns
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            stats["numeric_summary"][col] = {
                "mean": float(self.df[col].mean()),
                "median": float(self.df[col].median()),
                "std": float(self.df[col].std()),
                "min": float(self.df[col].min()),
                "max": float(self.df[col].max()),
                "25%": float(self.df[col].quantile(0.25)),
                "75%": float(self.df[col].quantile(0.75))
            }
        
        # Categorical columns
        categorical_cols = self.df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            stats["categorical_summary"][col] = {
                "unique_values": int(self.df[col].nunique()),
                "most_common": self.df[col].value_counts().head(5).to_dict(),
                "mode": str(self.df[col].mode()[0]) if len(self.df[col].mode()) > 0 else None
            }
        
        return stats
    
    def _get_distribution_analysis(self) -> Dict[str, Any]:
        """Analyze class distribution."""
        distribution = {}
        
        # Category distribution
        if 'category' in self.df.columns:
            category_counts = self.df['category'].value_counts()
            distribution['category'] = {
                "counts": category_counts.to_dict(),
                "percentages": (category_counts / len(self.df) * 100).round(2).to_dict(),
                "num_classes": int(self.df['category'].nunique()),
                "balance_ratio": float(category_counts.min() / category_counts.max())
            }
        
        # Priority distribution
        if 'priority' in self.df.columns:
            priority_counts = self.df['priority'].value_counts()
            distribution['priority'] = {
                "counts": priority_counts.to_dict(),
                "percentages": (priority_counts / len(self.df) * 100).round(2).to_dict(),
                "num_classes": int(self.df['priority'].nunique())
            }
        
        # Status distribution
        if 'status' in self.df.columns:
            status_counts = self.df['status'].value_counts()
            distribution['status'] = {
                "counts": status_counts.to_dict(),
                "percentages": (status_counts / len(self.df) * 100).round(2).to_dict()
            }
        
        return distribution
    
    def _get_data_quality_report(self) -> Dict[str, Any]:
        """Assess data quality."""
        quality = {
            "completeness": {},
            "duplicates": {},
            "outliers": {}
        }
        
        # Missing values
        missing = self.df.isnull().sum()
        quality["completeness"] = {
            "missing_counts": missing[missing > 0].to_dict(),
            "missing_percentages": (missing[missing > 0] / len(self.df) * 100).round(2).to_dict(),
            "total_missing": int(missing.sum()),
            "completeness_score": float((1 - missing.sum() / (len(self.df) * len(self.df.columns))) * 100)
        }
        
        # Duplicates
        duplicates = self.df.duplicated()
        quality["duplicates"] = {
            "count": int(duplicates.sum()),
            "percentage": float(duplicates.sum() / len(self.df) * 100),
            "unique_samples": int(len(self.df) - duplicates.sum())
        }
        
        return quality
    
    def _get_text_analysis(self) -> Dict[str, Any]:
        """Analyze text columns."""
        text_analysis = {}
        
        text_columns = ['description', 'subject', 'text', 'content']
        for col in text_columns:
            if col in self.df.columns:
                lengths = self.df[col].str.len()
                word_counts = self.df[col].str.split().str.len()
                
                text_analysis[col] = {
                    "length_statistics": {
                        "min": int(lengths.min()),
                        "max": int(lengths.max()),
                        "mean": float(lengths.mean()),
                        "median": float(lengths.median()),
                        "std": float(lengths.std())
                    },
                    "word_count_statistics": {
                        "min": int(word_counts.min()),
                        "max": int(word_counts.max()),
                        "mean": float(word_counts.mean()),
                        "median": float(word_counts.median()),
                        "std": float(word_counts.std())
                    }
                }
        
        return text_analysis
    
    def _get_temporal_analysis(self) -> Dict[str, Any]:
        """Analyze temporal patterns if timestamp columns exist."""
        temporal = {}
        
        if 'created_at' in self.df.columns:
            self.df['created_at'] = pd.to_datetime(self.df['created_at'])
            temporal['date_range'] = {
                "start": str(self.df['created_at'].min()),
                "end": str(self.df['created_at'].max()),
                "duration_days": int((self.df['created_at'].max() - self.df['created_at'].min()).days)
            }
            
            temporal['monthly_distribution'] = self.df.groupby(
                self.df['created_at'].dt.to_period('M')
            ).size().to_dict()
        
        return temporal
    
    def _save_report(self, report: Dict[str, Any]):
        """Save analysis report to multiple formats."""
        # JSON format
        json_path = RESEARCH_DIR / "dataset" / "dataset_analysis.json"
        json_path.parent.mkdir(exist_ok=True, parents=True)
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # CSV summary
        summary_data = {
            "Total Samples": report['metadata']['total_samples'],
            "Total Features": report['metadata']['total_features'],
            "Memory (MB)": report['metadata']['memory_usage_mb'],
            "Missing Values": report['data_quality']['completeness']['total_missing'],
            "Duplicate Samples": report['data_quality']['duplicates']['count'],
            "Completeness Score (%)": report['data_quality']['completeness']['completeness_score']
        }
        
        if 'category' in report['distribution_analysis']:
            summary_data["Number of Categories"] = report['distribution_analysis']['category']['num_classes']
            summary_data["Class Balance Ratio"] = report['distribution_analysis']['category']['balance_ratio']
        
        df_summary = pd.DataFrame([summary_data])
        csv_path = RESEARCH_DIR / "dataset" / "dataset_summary.csv"
        df_summary.to_csv(csv_path, index=False)
        
        logger.info(f"Report saved: {json_path}")
    
    def _generate_all_visualizations(self):
        """Generate all dataset visualizations."""
        output_dir = RESEARCH_DIR / "graphs"
        output_dir.mkdir(exist_ok=True, parents=True)
        
        # 1. Category and Priority Distribution
        self._plot_distributions()
        
        # 2. Text Length Distribution
        self._plot_text_statistics()
        
        # 3. Missing Values Heatmap
        self._plot_missing_values()
        
        # 4. Correlation Matrix (if numeric columns exist)
        self._plot_correlation_matrix()
        
        logger.info("All visualizations generated")
    
    def _plot_distributions(self):
        """Plot category and priority distributions."""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Category distribution
        if 'category' in self.df.columns:
            ax = axes[0]
            category_counts = self.df['category'].value_counts()
            category_counts.plot(kind='bar', ax=ax, color='steelblue', edgecolor='black')
            ax.set_title('Ticket Category Distribution', fontsize=14, fontweight='bold')
            ax.set_xlabel('Category', fontsize=12)
            ax.set_ylabel('Count', fontsize=12)
            ax.tick_params(axis='x', rotation=45)
            
            # Add percentage labels
            total = len(self.df)
            for i, (idx, val) in enumerate(category_counts.items()):
                percentage = val / total * 100
                ax.text(i, val + total*0.01, f'{val}\n({percentage:.1f}%)', 
                       ha='center', va='bottom', fontsize=9)
        
        # Priority distribution
        if 'priority' in self.df.columns:
            ax = axes[1]
            priority_counts = self.df['priority'].value_counts()
            colors = {'Critical': '#e74c3c', 'High': '#e67e22', 'Medium': '#f39c12', 'Low': '#27ae60'}
            bar_colors = [colors.get(x, 'gray') for x in priority_counts.index]
            priority_counts.plot(kind='bar', ax=ax, color=bar_colors, edgecolor='black')
            ax.set_title('Ticket Priority Distribution', fontsize=14, fontweight='bold')
            ax.set_xlabel('Priority', fontsize=12)
            ax.set_ylabel('Count', fontsize=12)
            ax.tick_params(axis='x', rotation=0)
            
            # Add percentage labels
            total = len(self.df)
            for i, (idx, val) in enumerate(priority_counts.items()):
                percentage = val / total * 100
                ax.text(i, val + total*0.01, f'{val}\n({percentage:.1f}%)', 
                       ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        output_path = RESEARCH_DIR / "graphs" / "class_distribution.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_text_statistics(self):
        """Plot text length distributions."""
        text_cols = [col for col in ['description', 'subject'] if col in self.df.columns]
        
        if not text_cols:
            return
        
        fig, axes = plt.subplots(1, len(text_cols), figsize=(7*len(text_cols), 5))
        if len(text_cols) == 1:
            axes = [axes]
        
        for idx, col in enumerate(text_cols):
            ax = axes[idx]
            lengths = self.df[col].str.len()
            
            ax.hist(lengths, bins=50, color='lightcoral', edgecolor='black', alpha=0.7)
            ax.axvline(lengths.mean(), color='red', linestyle='--', linewidth=2,
                      label=f'Mean: {lengths.mean():.0f}')
            ax.axvline(lengths.median(), color='blue', linestyle='--', linewidth=2,
                      label=f'Median: {lengths.median():.0f}')
            ax.set_title(f'{col.capitalize()} Length Distribution', fontsize=14, fontweight='bold')
            ax.set_xlabel('Length (characters)', fontsize=12)
            ax.set_ylabel('Frequency', fontsize=12)
            ax.legend(fontsize=10)
            ax.grid(alpha=0.3)
        
        plt.tight_layout()
        output_path = RESEARCH_DIR / "graphs" / "text_length_distribution.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_missing_values(self):
        """Plot missing values heatmap."""
        missing = self.df.isnull().sum()
        missing = missing[missing > 0].sort_values(ascending=False)
        
        if len(missing) == 0:
            return
        
        plt.figure(figsize=(10, 6))
        plt.barh(range(len(missing)), missing.values, color='salmon', edgecolor='black')
        plt.yticks(range(len(missing)), missing.index)
        plt.xlabel('Number of Missing Values', fontsize=12)
        plt.title('Missing Values by Feature', fontsize=14, fontweight='bold')
        plt.grid(axis='x', alpha=0.3)
        
        # Add value labels
        for i, val in enumerate(missing.values):
            percentage = val / len(self.df) * 100
            plt.text(val + len(self.df)*0.01, i, f'{val} ({percentage:.1f}%)', 
                    va='center', fontsize=9)
        
        plt.tight_layout()
        output_path = RESEARCH_DIR / "graphs" / "missing_values.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_correlation_matrix(self):
        """Plot correlation matrix for numeric features."""
        numeric_df = self.df.select_dtypes(include=[np.number])
        
        if numeric_df.shape[1] < 2:
            return
        
        plt.figure(figsize=(10, 8))
        corr = numeric_df.corr()
        sns.heatmap(corr, annot=True, cmap='coolwarm', center=0,
                   square=True, linewidths=1, cbar_kws={"shrink": 0.8})
        plt.title('Feature Correlation Matrix', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        output_path = RESEARCH_DIR / "graphs" / "correlation_matrix.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _generate_latex_tables(self, report: Dict[str, Any]):
        """Generate LaTeX tables for research paper."""
        latex_dir = RESEARCH_DIR / "paper_assets" / "latex"
        latex_dir.mkdir(exist_ok=True, parents=True)
        
        # Table 1: Dataset Statistics
        with open(latex_dir / "dataset_statistics.tex", 'w') as f:
            f.write("\\begin{table}[ht]\n")
            f.write("\\centering\n")
            f.write("\\caption{Dataset Statistics}\n")
            f.write("\\label{tab:dataset_stats}\n")
            f.write("\\begin{tabular}{|l|r|}\n")
            f.write("\\hline\n")
            f.write("\\textbf{Metric} & \\textbf{Value} \\\\\n")
            f.write("\\hline\n")
            f.write(f"Total Samples & {report['metadata']['total_samples']:,} \\\\\n")
            f.write(f"Total Features & {report['metadata']['total_features']} \\\\\n")
            f.write(f"Memory Usage (MB) & {report['metadata']['memory_usage_mb']:.2f} \\\\\n")
            
            if 'category' in report['distribution_analysis']:
                f.write(f"Number of Categories & {report['distribution_analysis']['category']['num_classes']} \\\\\n")
                f.write(f"Class Balance Ratio & {report['distribution_analysis']['category']['balance_ratio']:.3f} \\\\\n")
            
            f.write(f"Missing Values & {report['data_quality']['completeness']['total_missing']} \\\\\n")
            f.write(f"Duplicate Samples & {report['data_quality']['duplicates']['count']} \\\\\n")
            f.write(f"Completeness Score (\\%) & {report['data_quality']['completeness']['completeness_score']:.2f} \\\\\n")
            f.write("\\hline\n")
            f.write("\\end{tabular}\n")
            f.write("\\end{table}\n")
        
        # Table 2: Category Distribution
        if 'category' in report['distribution_analysis']:
            with open(latex_dir / "category_distribution.tex", 'w') as f:
                f.write("\\begin{table}[ht]\n")
                f.write("\\centering\n")
                f.write("\\caption{Ticket Category Distribution}\n")
                f.write("\\label{tab:category_dist}\n")
                f.write("\\begin{tabular}{|l|r|r|}\n")
                f.write("\\hline\n")
                f.write("\\textbf{Category} & \\textbf{Count} & \\textbf{Percentage (\\%)} \\\\\n")
                f.write("\\hline\n")
                
                counts = report['distribution_analysis']['category']['counts']
                percentages = report['distribution_analysis']['category']['percentages']
                
                for category in counts.keys():
                    f.write(f"{category} & {counts[category]:,} & {percentages[category]:.2f} \\\\\n")
                
                f.write("\\hline\n")
                f.write("\\end{tabular}\n")
                f.write("\\end{table}\n")
        
        logger.info(f"LaTeX tables generated: {latex_dir}")


# Convenience function
def analyze_dataset(dataset_path: str) -> Dict[str, Any]:
    """
    Analyze dataset and generate complete research report.
    
    Args:
        dataset_path: Path to CSV dataset file
    
    Returns:
        Complete analysis report
    """
    analyzer = DatasetAnalyzer(dataset_path)
    return analyzer.generate_complete_report()
