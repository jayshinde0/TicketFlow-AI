# Fix "LLM Unavailable" Issue - Complete Guide

## Problem
You're seeing: **"⚠ Retrieved from knowledge base (LLM unavailable)"**

This means the backend cannot connect to Ollama to generate AI responses.

## Root Cause
The backend server was started with old `.env` settings and needs a **full restart** (not just reload) to pick up the new configuration.

## ✅ Solution (Step by Step)

### Step 1: Verify Ollama is Running
```bash
ollama list
```

**Expected output:**
```
NAME                   ID              SIZE      MODIFIED
mistral:latest         6577803aa9a0    4.4 GB    X days ago
qwen2.5-coder:7b       dae161e27b0e    4.7 GB    X days ago
```

If Ollama is not running, start it:
```bash
ollama serve
```

### Step 2: Test Ollama Directly
```bash
ollama run mistral:latest "Say hello"
```

**Expected:** Should respond with a greeting.

### Step 3: Verify .env Configuration
Check `backend/.env` has:
```env
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral:latest
```

✅ **This is already configured correctly!**

### Step 4: Test Python Connection
```bash
cd backend
python test_ollama_connection.py
```

**Expected output:**
```
Testing Ollama connection...
URL: http://localhost:11434
Model: mistral:latest
--------------------------------------------------

1. Checking if Ollama is available...
   Result: ✅ Available

2. Testing simple generation...
   ✅ Response received: Hello, I am working!

3. Testing RAG-style generation...
   ✅ RAG Response received (618 chars)

==================================================
✅ All tests passed! Ollama is working correctly.
```

✅ **This test passed - Ollama works from Python!**

### Step 5: FULL RESTART of Backend (CRITICAL!)

**Stop the backend:**
1. Go to the terminal running uvicorn
2. Press `Ctrl+C`
3. Wait for: `INFO:     Stopping reloader process [XXXX]`
4. **Press `Ctrl+C` again if needed** to fully stop

**Start fresh:**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Look for these startup messages:**
```
═══ TicketFlow AI Backend Starting ═══
MongoDB connected and indexes created.
🤖 LLM provider: Ollama (local)
📦 Ollama model: mistral:latest          ← Should show mistral:latest
🔗 Ollama URL: http://localhost:11434
APScheduler started...
TicketFlow AI is ready!
```

### Step 6: Test LLM Health Endpoint
```bash
curl http://localhost:8000/health/llm
```

**Expected response:**
```json
{
  "status": "available",
  "config": {
    "provider": "ollama",
    "model": "mistral:latest",
    "url": "http://localhost:11434"
  },
  "error": null
}
```

### Step 7: Create a Test Ticket
Create a ticket through the UI or API. You should now see:
- ✅ **AI Generated Response** with actual LLM-generated text
- ✅ **NO warning** about "LLM unavailable"
- ✅ Response is contextual and specific to the ticket

## Why This Happens

1. **Environment variables are loaded at startup** - The `llm_provider` is initialized when the app imports modules
2. **--reload only watches code files** - Changes to `.env` don't trigger reload
3. **Must fully restart** - Stop (Ctrl+C) and start again

## Quick Diagnostic Commands

```bash
# 1. Check Ollama is running
ollama list

# 2. Test Ollama directly
ollama run mistral:latest "test"

# 3. Test from Python
python test_ollama_connection.py

# 4. Check backend LLM health (after restart)
curl http://localhost:8000/health/llm

# 5. Check backend is running
curl http://localhost:8000/health
```

## Files Updated

✅ `backend/.env` - Set to use `mistral:latest`
✅ `backend/test_ollama_connection.py` - Created for testing
✅ `backend/main.py` - Added `/health/llm` endpoint
✅ All configuration files ready

## Next Steps

1. **Stop your backend** (Ctrl+C, wait for full stop)
2. **Start it again** (uvicorn main:app --reload --host 0.0.0.0 --port 8000)
3. **Verify startup logs** show "Ollama model: mistral:latest"
4. **Test creating a ticket** - should work now!

## Still Not Working?

If after full restart you still see "LLM unavailable":

1. Check backend logs for error messages
2. Run: `python test_ollama_connection.py` (should pass)
3. Run: `curl http://localhost:8000/health/llm` (should show "available")
4. Check if another process is using port 11434
5. Try restarting Ollama: `ollama serve`

## Success Indicators

✅ Startup logs show correct model name
✅ `/health/llm` returns `"status": "available"`
✅ Test ticket generates AI response
✅ No "LLM unavailable" warnings
