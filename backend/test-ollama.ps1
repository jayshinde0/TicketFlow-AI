Write-Host "Testing Qwen-2.5-Coder-7b Response Time..." -ForegroundColor Green
Write-Host ""

$startTime = Get-Date

try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:11434/api/generate" `
      -Method Post `
      -Headers @{"Content-Type"="application/json"} `
      -Body (@{
        "model" = "qwen2.5-coder:7b"
        "prompt" = "Brief troubleshooting for VPN timeout"
        "stream" = $false
      } | ConvertTo-Json) `
      -TimeoutSec 60
    
    $endTime = Get-Date
    $duration = [Math]::Round(($endTime - $startTime).TotalMilliseconds)
    
    $data = $response.Content | ConvertFrom-Json
    
    Write-Host "✓ Response Time: $duration ms" -ForegroundColor Green
    Write-Host ""
    Write-Host "Response:" -ForegroundColor Cyan
    Write-Host $data.response
    Write-Host ""
    
    if ($duration -lt 8000) {
        Write-Host "⚠️ VERY FAST - Might be cached" -ForegroundColor Yellow
    } elseif ($duration -lt 15000) {
        Write-Host "✓ GOOD - Normal for Qwen" -ForegroundColor Green
    } elseif ($duration -lt 25000) {
        Write-Host "⚠️ SLOW - Consider Mistral" -ForegroundColor Yellow
    } else {
        Write-Host "❌ VERY SLOW - Use Mistral or optimize" -ForegroundColor Red
    }
}
catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}