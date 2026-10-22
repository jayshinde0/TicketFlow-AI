"""
run_model_analysis.py — Simplified script to run complete model comparison and visualization.

This script:
1. Compares Naive Bayes, Logistic Regression, Random Forest, and SVM
2. Generates performance metrics (Accuracy, Precision, Recall, F1)
3. Creates visualizations and reports

Usage:
    python run_model_analysis.py
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger

logger.remove()
logger.add(
    sys.stdout,
    format="{time:HH:mm:ss} | {level} | {message}",
    level="INFO",
    colorize=False,
)


def main():
    """Run complete model analysis pipeline."""
    logger.info("\n" + "=" * 80)
    logger.info("TicketFlow AI - Complete Model Performance Analysis")
    logger.info("=" * 80 + "\n")

    try:
        # Step 1: Run model comparison
        logger.info("STEP 1: Running model comparison...")
        logger.info("-" * 80)
        from ml.model_comparison import run_model_comparison

        results = run_model_comparison()

        # Step 2: Generate visualizations
        logger.info("\n\nSTEP 2: Generating visualizations and reports...")
        logger.info("-" * 80)
        from ml.visualize_comparison import visualize_all

        visualize_all()

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("✓ ANALYSIS COMPLETE!")
        logger.info("=" * 80)

        logger.info("\n📊 Generated Outputs:")
        logger.info("  • Model comparison JSON")
        logger.info("  • Performance comparison charts")
        logger.info("  • Confusion matrices")
        logger.info("  • Per-class performance heatmaps")
        logger.info("  • Training time comparison")
        logger.info("  • Detailed Markdown report")
        logger.info("  • Summary CSV")

        logger.info("\n📁 Location: backend/ml/artifacts/visualizations/")
        logger.info("\n" + "=" * 80 + "\n")

        return 0

    except Exception as e:
        logger.error(f"\n❌ Error during analysis: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
