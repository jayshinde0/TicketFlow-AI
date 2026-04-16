# How to Restart Backend After .env Changes

## Problem
When you change `.env` file settings (like `OLLAMA_MODEL`), the backend server needs a **full restart** for changes to take effect. The `--reload` flag only reloads on code changes, not environment variable changes.

## Solution: Full Restart

### Step 1: Stop the Backend
Press `Ctrl+C` in the terminal where uvicorn is running.

**Wait for this message:**
```
INFO:     Stopping reloader process [XXXX]
```

### Step 2: Verify It's Stopped
Make sure the process is completely stopped. If it's still running, press `Ctrl+C` again.

### Step 3: Start Fresh
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Step 4: Verify LLM Configuration
Look for these startup messages:
```
═══ TicketFlow AI Backend Starting ═══
MongoDB connected and indexes created.
🤖 LLM provider: Ollama (local)
📦 Ollama model: mistral:latest
🔗 Ollama URL: http://localhost:11434
APScheduler started: root_cause(5min), sla_check(2min), escalation(5min)
TicketFlow AI is ready!
```

## Current Configuration

Your `.env` is now set to:
```env
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral:latest
```

## Verification

After restart, test by creating a ticket. You should see:
- ✅ AI-generated response (not "Retrieved from knowledge base")
- ✅ No "LLM unavailable" warning

## Troubleshooting

### If you still see "LLM unavailable":

1. **Check Ollama is running:**
   ```bash
   ollama list
   ```

2. **Test Ollama directly:**
   ```bash
   ollama run mistral:latest "Say hello"
   ```

3. **Test from Python:**
   ```bash
   python test_ollama_connection.py
   ```

4. **Check backend logs** for error messages about Ollama connection

### Common Issues:

- ❌ **Backend not fully restarted** - Must stop and start, not just reload
- ❌ **Ollama not running** - Start with `ollama serve`
- ❌ **Wrong model name** - Check `ollama list` for exact model names
- ❌ **Port conflict** - Make sure nothing else is using port 11434

## Quick Test Command

After restarting backend, run:
```bash
curl http://localhost:8000/health
```

Should return:
```json
{"status":"ok","service":"TicketFlow AI"}
```
