# TicketFlow AI - Complete Setup Guide

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Python 3.11+
- Node.js 16+
- MongoDB (local or Atlas)
- Ollama with Mistral-Nemo
- 8GB RAM minimum

---

## 📦 Step 1: Install Dependencies

### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### Frontend Setup
```bash
cd frontend
npm install
```

---

## 🗄️ Step 2: Setup MongoDB

### Option A: MongoDB Atlas (Cloud - Recommended)
1. Go to [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Create free account
3. Create cluster
4. Get connection string
5. Update `backend/.env`:
   ```
   MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/?appName=Cluster0
   ```

### Option B: Local MongoDB
```bash
# Install MongoDB Community Edition
# Windows: Download from mongodb.com
# Mac: brew install mongodb-community
# Linux: sudo apt install mongodb

# Start MongoDB
mongod --dbpath ./data/db

# Connection string in backend/.env:
MONGODB_URL=mongodb://localhost:27017
```

---

## 🤖 Step 3: Setup Ollama (LLM)

### Install Ollama
```bash
# Windows/Mac: Download from ollama.com
# Linux:
curl -fsSL https://ollama.com/install.sh | sh
```

### Pull Mistral-Nemo Model
```bash
ollama pull mistral-nemo
```

### Start Ollama Server
```bash
ollama serve
```

Verify: `curl http://localhost:11434/api/tags`

---

## 🎨 Step 4: Setup ChromaDB (Vector Database)

ChromaDB runs in HTTP client mode (no separate server needed).

The backend will create collections automatically on first run.

---

## ⚙️ Step 5: Configure Environment

### Create `backend/.env`
```bash
cd backend
cp .env.example .env
```

### Edit `backend/.env`:
```env
# MongoDB
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=ticketflow_ai

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production

# Ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral-nemo

# ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8001

# Thresholds
CONFIDENCE_HIGH_THRESHOLD=0.85
CONFIDENCE_LOW_THRESHOLD=0.60
```

---

## 🎓 Step 6: Train ML Models

```bash
cd backend
python ml/train.py
```

This will:
- Generate 5,000 synthetic training samples
- Train category classifier (Logistic Regression)
- Train priority classifier (Random Forest)
- Train SLA predictor
- Save models to `ml/artifacts/`
- Output training metrics

Expected output:
```
Category Classifier — Test F1 (macro): 0.8500
Priority Classifier — Test F1 (macro): 0.8200
SLA Predictor — Test AUC-ROC: 0.8100
```

---

## 👥 Step 7: Seed Users

```bash
cd backend
python seed_users.py
```

This creates:
- Admin: `admin@ticketflow.ai` / `admin123`
- Agent: `agent1@ticketflow.ai` / `agent123`
- Senior Engineer: `senior1@ticketflow.ai` / `senior123`
- Test User: `user@ticketflow.ai` / `user123`

---

## 🚀 Step 8: Start Services

### Terminal 1: Ollama
```bash
ollama serve
```

### Terminal 2: Backend
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Verify: `curl http://localhost:8000/health`

### Terminal 3: Frontend
```bash
cd frontend
npm start
```

Opens: `http://localhost:3000`

---

## ✅ Step 9: Verify Setup

### 1. Check Backend Health
```bash
curl http://localhost:8000/health
# Should return: {"status":"ok","service":"TicketFlow AI"}
```

### 2. Check Ollama
```bash
curl http://localhost:11434/api/tags
# Should list mistral-nemo model
```

### 3. Test Ticket Submission
```bash
curl -X POST http://localhost:8000/api/tickets/ \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Printer not working",
    "description": "The office printer is offline and wont print my documents."
  }'
```

Should return ticket with `ai_analysis` including `generated_response`.

### 4. Login to Frontend
1. Go to `http://localhost:3000`
2. Login as agent: `agent1@ticketflow.ai` / `agent123`
3. Navigate to Agent Queue
4. Should see tickets with AI analysis

---

## 🔧 Troubleshooting

### Issue: "Cannot connect to MongoDB"
```bash
# Check MongoDB is running
mongosh
# Or for Atlas, verify connection string in .env
```

### Issue: "Ollama not reachable"
```bash
# Start Ollama
ollama serve

# Verify
curl http://localhost:11434/api/tags
```

### Issue: "Models not found"
```bash
# Retrain models
cd backend
python ml/train.py
```

### Issue: "All tickets classified as Security"
```bash
# The model needs better training data
# Edit backend/ml/data_loader.py line ~120
# Add "forgot password" examples to Auth templates
# Then retrain:
python ml/train.py
```

### Issue: "WebSocket error in browser"
```bash
# Clear browser cache
# Hard refresh: Ctrl+Shift+R
# Restart frontend:
cd frontend
rm -rf node_modules/.cache
npm start
```

### Issue: "CORS errors"
```bash
# Restart backend
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📊 System Requirements

### Minimum:
- CPU: 4 cores
- RAM: 8GB
- Disk: 10GB free
- Internet: For MongoDB Atlas

### Recommended:
- CPU: 8 cores
- RAM: 16GB
- Disk: 20GB free
- GPU: Optional (speeds up ML inference)

---

## 🎯 Default Ports

- Frontend: `3000`
- Backend: `8000`
- MongoDB: `27017`
- Ollama: `11434`
- ChromaDB: `8001` (HTTP client mode)

---

## 📝 Quick Commands Reference

```bash
# Start everything
cd backend && python -m uvicorn main:app --reload &
cd frontend && npm start &
ollama serve &

# Stop everything
# Ctrl+C in each terminal

# Retrain models
cd backend && python ml/train.py

# Seed users
cd backend && python seed_users.py

# Check logs
cd backend && tail -f uvicorn_startup.log

# Clear caches
cd frontend && rm -rf node_modules/.cache
```

---

## 🎓 Next Steps

1. **Submit test tickets** to see AI in action
2. **Login as agent** to review AI suggestions
3. **Approve tickets** to build knowledge base
4. **Monitor analytics** dashboard for insights
5. **Retrain models** after collecting feedback

---

## 📚 Additional Resources

- **System Architecture**: See `SYSTEM_ARCHITECTURE.md`
- **API Documentation**: `http://localhost:8000/docs`
- **Ollama Docs**: [ollama.com/docs](https://ollama.com/docs)
- **MongoDB Docs**: [mongodb.com/docs](https://www.mongodb.com/docs)

---

## ✅ Setup Complete!

Your TicketFlow AI system is now ready to:
- ✅ Accept ticket submissions
- ✅ Classify with ML models
- ✅ Generate responses with Mistral-Nemo
- ✅ Route intelligently with HITL
- ✅ Learn from agent feedback
- ✅ Improve over time

**Test it now**: Submit a ticket and watch the AI magic happen! 🚀
