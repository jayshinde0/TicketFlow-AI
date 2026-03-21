# check_services.ps1 - Windows PowerShell health check for TicketFlow AI services

Write-Host "🔍 Checking TicketFlow AI Services..." -ForegroundColor Cyan
Write-Host ""

$runningServices = 0
$requiredServices = 4

# Function to test port
function Test-Port {
    param($Port)
    $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
    return $connection.TcpTestSucceeded
}

# Function to test HTTP endpoint
function Test-HttpEndpoint {
    param($Url)
    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

# Check Backend
Write-Host "1️⃣  Backend (FastAPI)" -ForegroundColor Yellow
if (Test-HttpEndpoint "http://localhost:8000/health") {
    Write-Host "   ✅ Backend is running on port 8000" -ForegroundColor Green
    try {
        $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -ErrorAction SilentlyContinue
        Write-Host "   Response: $($health | ConvertTo-Json -Compress)" -ForegroundColor Gray
    } catch {}
    $runningServices++
} else {
    Write-Host "   ❌ Backend is NOT running on port 8000" -ForegroundColor Red
    Write-Host "   → Start with: cd backend; uvicorn main:app --reload" -ForegroundColor Gray
}
Write-Host ""

# Check MongoDB
Write-Host "2️⃣  MongoDB" -ForegroundColor Yellow
if (Test-Port 27017) {
    Write-Host "   ✅ MongoDB is running on port 27017" -ForegroundColor Green
    $runningServices++
} else {
    Write-Host "   ❌ MongoDB is NOT running on port 27017" -ForegroundColor Red
    Write-Host "   → Start with: docker run -d -p 27017:27017 --name mongodb mongo:7.0" -ForegroundColor Gray
    Write-Host "   → Or check MongoDB Atlas connection" -ForegroundColor Gray
}
Write-Host ""

# Check ChromaDB
Write-Host "3️⃣  ChromaDB" -ForegroundColor Yellow
if (Test-HttpEndpoint "http://localhost:8001/api/v1/heartbeat") {
    Write-Host "   ✅ ChromaDB is running on port 8001" -ForegroundColor Green
    $runningServices++
} elseif (Test-Port 8001) {
    Write-Host "   ⚠️  ChromaDB port is open but not responding" -ForegroundColor Yellow
    Write-Host "   → Might be starting up..." -ForegroundColor Gray
} else {
    Write-Host "   ❌ ChromaDB is NOT running on port 8001" -ForegroundColor Red
    Write-Host "   → Start with: docker run -d -p 8001:8000 --name chromadb chromadb/chroma:latest" -ForegroundColor Gray
}
Write-Host ""

# Check Frontend
Write-Host "4️⃣  Frontend (React)" -ForegroundColor Yellow
if (Test-HttpEndpoint "http://localhost:3000") {
    Write-Host "   ✅ Frontend is running on port 3000" -ForegroundColor Green
    $runningServices++
} elseif (Test-Port 3000) {
    Write-Host "   ⚠️  Frontend port is open but not responding" -ForegroundColor Yellow
    Write-Host "   → Might be starting up..." -ForegroundColor Gray
} else {
    Write-Host "   ❌ Frontend is NOT running on port 3000" -ForegroundColor Red
    Write-Host "   → Start with: cd frontend; npm start" -ForegroundColor Gray
}
Write-Host ""

# Check Ollama (optional)
Write-Host "5️⃣  Ollama (Optional - for LLM responses)" -ForegroundColor Yellow
if (Test-HttpEndpoint "http://localhost:11434/api/tags") {
    Write-Host "   ✅ Ollama is running on port 11434" -ForegroundColor Green
    try {
        $models = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -ErrorAction SilentlyContinue
        Write-Host "   Models installed: $($models.models.Count)" -ForegroundColor Gray
    } catch {}
} else {
    Write-Host "   ⚠️  Ollama is NOT running (optional)" -ForegroundColor Yellow
    Write-Host "   → Install: https://ollama.ai" -ForegroundColor Gray
    Write-Host "   → Start: ollama serve" -ForegroundColor Gray
    Write-Host "   → Pull model: ollama pull mistral-nemo" -ForegroundColor Gray
}
Write-Host ""

# Check Docker containers
Write-Host "🐳 Docker Containers:" -ForegroundColor Yellow
try {
    $containers = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>$null
    if ($containers) {
        Write-Host $containers -ForegroundColor Gray
    } else {
        Write-Host "   No Docker containers running" -ForegroundColor Gray
    }
} catch {
    Write-Host "   Docker not available or not running" -ForegroundColor Gray
}
Write-Host ""

# Summary
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "Required services running: $runningServices / $requiredServices" -ForegroundColor White
Write-Host ""

if ($runningServices -eq $requiredServices) {
    Write-Host "🎉 All required services are running!" -ForegroundColor Green
    Write-Host "   → Open http://localhost:3000 in your browser" -ForegroundColor White
    Write-Host "   → API Docs: http://localhost:8000/docs" -ForegroundColor White
} else {
    Write-Host "⚠️  Some services are not running. Start them using the commands above." -ForegroundColor Yellow
}
Write-Host ""

# Quick commands
Write-Host "💡 Quick Commands:" -ForegroundColor Cyan
Write-Host "   Backend:  cd backend; uvicorn main:app --reload" -ForegroundColor Gray
Write-Host "   Frontend: cd frontend; npm start" -ForegroundColor Gray
Write-Host "   MongoDB:  docker run -d -p 27017:27017 --name mongodb mongo:7.0" -ForegroundColor Gray
Write-Host "   ChromaDB: docker run -d -p 8001:8000 --name chromadb chromadb/chroma:latest" -ForegroundColor Gray
Write-Host ""
