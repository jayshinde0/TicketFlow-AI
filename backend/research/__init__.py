"""
research module — Automatic Research Data Collection System

This module provides comprehensive logging and analysis tools for
generating all data required for research paper publication.

Components:
- ResearchLogger: Main logging interface
- DatasetAnalyzer: Dataset statistics and visualization
- (Coming soon) PreprocessingLogger, RAGEvaluator, HITLLogger, etc.

Usage:
    from research.research_logger import research_logger
    from research.dataset_analyzer import analyze_dataset
    
    # Analyze dataset
    report = analyze_dataset("data/tickets.csv")
    
    # Log experiments
    research_logger.log_training_start("RandomForest", params)
    research_logger.log_evaluation_metrics(y_true, y_pred)
"""

from .research_logger import research_logger, ResearchLogger, RESEARCH_DIR
from .dataset_analyzer import DatasetAnalyzer, analyze_dataset

__all__ = [
    'research_logger',
    'ResearchLogger',
    'DatasetAnalyzer',
    'analyze_dataset',
    'RESEARCH_DIR'
]

__version__ = '1.0.0'
__author__ = 'TicketFlow AI Research Team'
