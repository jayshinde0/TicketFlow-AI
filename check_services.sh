#!/bin/bash
# check_services.sh - Quick health check for all TicketFlow AI services

echo "🔍 Checking TicketFlow AI Services..."
echo ""

# Check Backend
echo "1️⃣  Backend (FastAPI)"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ Backend is running on port 8000"
    curl -s http://localhost:8000/health | python -m json.tool
else
    echo "   ❌ Backend is NOT running on port 8000"
    echo "   → Start with: cd backend && uvicorn main:app --reload"
fi
echo ""

# Check MongoDB
echo "2️⃣  MongoDB"
if nc -z localhost 27017 > /dev/null 2>&1; then
    echo "   ✅ MongoDB is running on port 27017"
else
    echo "   ❌ MongoDB is NOT running on port 27017"
    echo "   → Start with: docker run -d -p 27017:27017 mongo:7.0"
fi
echo ""

# Check ChromaDB
echo "3️⃣  ChromaDB"
if curl -s http://localhost:8001/api/v1/heartbeat > /dev/null 2>&1; then
    echo "   ✅ ChromaDB is running on port 8001"
else
    echo "   ❌ ChromaDB is NOT running on port 8001"
    echo "   → Start with: docker run -d -p 8001:8000 chromadb/chroma:latest"
fi
echo ""

# Check Frontend
echo "4️⃣  Frontend (React)"
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "   ✅ Frontend is running on port 3000"
else
    echo "   ❌ Frontend is NOT running on port 3000"
    echo "   → Start with: cd frontend && npm start"
fi
echo ""

# Check Ollama (optional)
echo "5️⃣  Ollama (Optional - for LLM responses)"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "   ✅ Ollama is running on port 11434"
    echo "   Models installed:"
    curl -s http://localhost:11434/api/tags | python -m json.tool | grep '"name"' | head -3
else
    echo "   ⚠️  Ollama is NOT running (optional)"
    echo "   → Install: https://ollama.ai"
    echo "   → Start: ollama serve"
    echo "   → Pull model: ollama pull mistral-nemo"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

REQUIRED_SERVICES=0
RUNNING_SERVICES=0

# Count required services
curl -s http://localhost:8000/health > /dev/null 2>&1 && ((RUNNING_SERVICES++))
((REQUIRED_SERVICES++))

nc -z localhost 27017 > /dev/null 2>&1 && ((RUNNING_SERVICES++))
((REQUIRED_SERVICES++))

curl -s http://localhost:8001/api/v1/heartbeat > /dev/null 2>&1 && ((RUNNING_SERVICES++))
((REQUIRED_SERVICES++))

curl -s http://localhost:3000 > /dev/null 2>&1 && ((RUNNING_SERVICES++))
((REQUIRED_SERVICES++))

echo "Required services running: $RUNNING_SERVICES / $REQUIRED_SERVICES"
echo ""

if [ $RUNNING_SERVICES -eq $REQUIRED_SERVICES ]; then
    echo "🎉 All required services are running!"
    echo "   → Open http://localhost:3000 in your browser"
else
    echo "⚠️  Some services are not running. Start them using the commands above."
fi
echo ""
