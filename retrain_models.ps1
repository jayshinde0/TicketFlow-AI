# TicketFlow AI - Quick Model Retraining Script
# Run this after making confidence improvements

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "TicketFlow AI - Model Retraining" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if in backend directory
if (Test-Path "main.py") {
    Write-Host "✓ Already in backend directory" -ForegroundColor Green
} elseif (Test-Path "backend/main.py") {
    Write-Host "→ Changing to backend directory..." -ForegroundColor Yellow
    Set-Location backend
} else {
    Write-Host "✗ Error: Cannot find backend directory" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting model training with improved settings..." -ForegroundColor Cyan
Write-Host "  • C parameter: 10.0 (increased from 5.0)" -ForegroundColor White
Write-Host "  • Confidence formula: 60/25/20 weights" -ForegroundColor White
Write-Host "  • Routing thresholds: 78%/55%" -ForegroundColor White
Write-Host ""

# Run training
python -m ml.train --skip-grid-search

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "✓ Training Complete!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Restart backend: uvicorn main:app --reload" -ForegroundColor White
    Write-Host "  2. Test with sample tickets" -ForegroundColor White
    Write-Host "  3. Check ML Dashboard for improved metrics" -ForegroundColor White
    Write-Host ""
    Write-Host "Expected improvements:" -ForegroundColor Cyan
    Write-Host "  • Average confidence: 56% → 72% (+16%)" -ForegroundColor White
    Write-Host "  • Auto-resolve rate: 15% → 35% (+20%)" -ForegroundColor White
    Write-Host "  • Escalation rate: 45% → 25% (-20%)" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "✗ Training failed. Check error messages above." -ForegroundColor Red
    exit 1
}
