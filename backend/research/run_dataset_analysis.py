"""
research/run_dataset_analysis.py — Quick Start Script

Run complete dataset analysis and generate all research assets.

Usage:
    cd backend
    python research/run_dataset_analysis.py
"""

import sys
from pathlib import Path

# Add parent directory to path to import research module
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from research.dataset_analyzer import analyze_dataset
from research.research_logger import research_logger

def main():
    """Run complete dataset analysis."""
    logger.info("="*60)
    logger.info("ConfiTicketAI - Research Data Generation")
    logger.info("="*60)
    
    # Path to dataset
    dataset_path = Path(__file__).parent.parent / "ml" / "data" / "customer_support_tickets.csv"
    
    if not dataset_path.exists():
        logger.error(f"Dataset not found: {dataset_path}")
        logger.info("Please ensure the dataset file exists at the specified path.")
        return
    
    logger.info(f"Dataset found: {dataset_path}")
    logger.info("Starting analysis...")
    
    # Run dataset analysis
    try:
        report = analyze_dataset(str(dataset_path))
        
        logger.success("✓ Dataset analysis complete!")
        logger.info(f"✓ Total samples: {report['metadata']['total_samples']:,}")
        logger.info(f"✓ Total features: {report['metadata']['total_features']}")
        
        if 'category' in report['distribution_analysis']:
            logger.info(f"✓ Number of categories: {report['distribution_analysis']['category']['num_classes']}")
            logger.info(f"✓ Class balance ratio: {report['distribution_analysis']['category']['balance_ratio']:.3f}")
        
        logger.info(f"✓ Completeness score: {report['data_quality']['completeness']['completeness_score']:.2f}%")
        
        logger.info("")
        logger.success("="*60)
        logger.success("Research assets generated successfully!")
        logger.success("="*60)
        logger.info("")
        logger.info("Generated files:")
        logger.info("  📊 research/dataset/dataset_analysis.json")
        logger.info("  📊 research/dataset/dataset_summary.csv")
        logger.info("  📈 research/graphs/class_distribution.png")
        logger.info("  📈 research/graphs/text_length_distribution.png")
        logger.info("  📈 research/graphs/missing_values.png")
        logger.info("  📄 research/paper_assets/latex/*.tex")
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Review generated reports in research/ directory")
        logger.info("  2. Run model training with: python ml/train.py")
        logger.info("  3. Generate complete research report")
        
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        logger.exception("Full traceback:")
        return
    
    logger.info("")
    logger.info("Analysis complete! 🎉")


if __name__ == "__main__":
    main()
