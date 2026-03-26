#!/bin/bash
# TicketFlow AI - Quick Model Retraining Script
# Run this after making confidence improvements

echo "============================================================"
echo "TicketFlow AI - Model Retraining"
echo "============================================================"
echo ""

# Check if in backend directory
if [ -f "main.py" ]; then
    echo "✓ Already in backend directory"
elif [ -f "backend/main.py" ]; then
    echo "→ Changing to backend directory..."
    cd backend
else
    echo "✗ Error: Cannot find backend directory"
    exit 1
fi

echo ""
echo "Starting model training with improved settings..."
echo "  • C parameter: 10.0 (increased from 5.0)"
echo "  • Confidence formula: 60/25/20 weights"
echo "  • Routing thresholds: 78%/55%"
echo ""

# Run training
python -m ml.train --skip-grid-search

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "✓ Training Complete!"
    echo "============================================================"
    echo ""
    echo "Next steps:"
    echo "  1. Restart backend: uvicorn main:app --reload"
    echo "  2. Test with sample tickets"
    echo "  3. Check ML Dashboard for improved metrics"
    echo ""
    echo "Expected improvements:"
    echo "  • Average confidence: 56% → 72% (+16%)"
    echo "  • Auto-resolve rate: 15% → 35% (+20%)"
    echo "  • Escalation rate: 45% → 25% (-20%)"
else
    echo ""
    echo "✗ Training failed. Check error messages above."
    exit 1
fi
