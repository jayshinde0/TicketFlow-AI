# ChromaDB Server Setup Guide

## Overview
By default, TicketFlow AI uses ChromaDB in **local persistent mode** (stores data in `./chroma_data` folder). This works fine for development but you can optionally run ChromaDB as a **separate server** for better performance and production-like setup.

## Current Status
✅ ChromaDB CLI is installed (version 1.4.1)
✅ Local persistent storage is working in `./chroma_data`

## Option 1: Keep Using Local Storage (Current Setup)
**No action needed!** Your current setup works perfectly. The warning message is just informational.

## Option 2: Run ChromaDB as a Separate Server

### Step 1: Start ChromaDB Server

**On Windows (PowerShell):**
```powershell
cd backend
.\run_chromadb.ps1
```

**On Windows (Bash/Git Bash):**
```bash
cd backend
bash run_chromadb.sh
```

**Or run directly:**
```bash
cd backend
chroma run --host localhost --port 8001 --path ./chroma_data
```

### Step 2: Verify Server is Running
You should see output like:
```
INFO:     Uvicorn running on http://localhost:8001
INFO:     Application startup complete.
```

### Step 3: Test Connection
Open a new terminal and test:
```bash
curl http://localhost:8001/api/v1/heartbeat
```

Expected response: `{"nanosecond heartbeat": ...}`

### Step 4: Restart Your Backend
Once ChromaDB server is running, restart your FastAPI backend:
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should now see:
```
ChromaDB connected at localhost:8001
```

Instead of the warning message!

## Configuration

ChromaDB settings are in `backend/.env`:
```env
CHROMA_HOST=localhost
CHROMA_PORT=8001
```

## Troubleshooting

### Port Already in Use
If port 8001 is busy, change it in `.env`:
```env
CHROMA_PORT=8002
```

Then update the run command:
```bash
chroma run --host localhost --port 8002 --path ./chroma_data
```

### Connection Refused
Make sure:
1. ChromaDB server is running in a separate terminal
2. Port matches in `.env` and the run command
3. No firewall blocking localhost connections

### Data Migration
Your existing data in `./chroma_data` will be used automatically when you start the ChromaDB server with `--path ./chroma_data`.

## Production Deployment

For production, consider:
1. Running ChromaDB in a Docker container
2. Using a reverse proxy (nginx)
3. Enabling authentication
4. Using a dedicated server/VM

Example Docker command:
```bash
docker run -d \
  --name chromadb \
  -p 8001:8000 \
  -v ./chroma_data:/chroma/chroma \
  chromadb/chroma:latest
```

## Summary

**Current Setup (Local):**
- ✅ Works out of the box
- ✅ No separate process needed
- ⚠️ Shows warning message (harmless)

**Server Setup (Optional):**
- ✅ Better performance
- ✅ Production-like architecture
- ✅ No warning messages
- ⚠️ Requires separate terminal/process
