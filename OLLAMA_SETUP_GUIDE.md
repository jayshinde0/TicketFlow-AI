# 🦙 Ollama Setup Guide for TicketFlow AI

## What is Ollama?

Ollama is a local LLM runtime that allows you to run large language models (like Mistral) on your own machine. TicketFlow AI uses it to generate intelligent ticket responses.

---

## 📥 Installation (Windows)

### Step 1: Download Ollama

1. Go to: **https://ollama.com/download**
2. Click "Download for Windows"
3. Run the installer (`OllamaSetup.exe`)
4. Follow the installation wizard

### Step 2: Verify Installation

Open a new PowerShell window and run:
```powershell
ollama --version
```

You should see something like: `ollama version 0.1.x`

---

## 🚀 Quick Start

### 1. Start Ollama Service

Ollama usually starts automatically after installation. To verify:

```powershell
# Check if Ollama is running
Test-NetConnection -ComputerName localhost -Port 11434 -InformationLevel Quiet
```

If it returns `False`, start it manually:
```powershell
ollama serve
```

Keep this terminal open (Ollama runs in the foreground).

### 2. Download Mistral Model

Open a NEW PowerShell window and run:
```powershell
ollama pull mistral
```

This will download the Mistral 7B model (~4GB). It may take 5-10 minutes depending on your internet speed.

### 3. Test the Model

```powershell
ollama run mistral "Hello, how are you?"
```

You should see a response from the AI.

---

## ⚙️ Configuration for TicketFlow AI

Your `.env` file is already configured correctly:
```env
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral:latest
```

No changes needed!

---

## 🔄 Starting Ollama (Daily Use)

### Option 1: Automatic (Recommended)

Ollama should start automatically with Windows. Check the system tray for the Ollama icon.

### Option 2: Manual

If Ollama isn't running:
```powershell
ollama serve
```

---

## 🧪 Testing with TicketFlow AI

### 1. Ensure Ollama is Running

```powershell
# Should return True
Test-NetConnection -ComputerName localhost -Port 11434 -InformationLevel Quiet
```

### 2. Restart Backend

```powershell
cd backend
uvicorn main:app --reload
```

### 3. Submit a Test Ticket

Go to http://localhost:3000 and submit:
```
Subject: Cannot access VPN
Description: Getting connection timeout when trying to connect to company VPN. 
Tried restarting my computer but still not working.
```

You should now see a detailed AI-generated response instead of "Retrieved from knowledge base (LLM unavailable)".

---

## 📊 Expected Behavior

### Before Ollama:
```
⚠ Retrieved from knowledge base (LLM unavailable)
Response: "Please contact support for assistance."
```

### After Ollama:
```
✓ AI Generated Response
Response: "Based on your VPN connection timeout issue, here are the steps to resolve:

1. Check your internet connection stability
2. Verify VPN credentials are correct
3. Try connecting to a different VPN server
4. Disable firewall temporarily to test
5. Contact IT if issue persists

This is a common Network issue that typically resolves with these steps."
```

---

## 🎯 Alternative Models

If Mistral is too large or slow, try smaller models:

### Mistral 7B (Default - Recommended)
```powershell
ollama pull mistral
```
- Size: ~4GB
- Speed: Medium
- Quality: Excellent

### Llama 3.2 3B (Faster, smaller)
```powershell
ollama pull llama3.2:3b
```
- Size: ~2GB
- Speed: Fast
- Quality: Good

Then update `.env`:
```env
OLLAMA_MODEL=llama3.2:3b
```

### Phi-3 Mini (Fastest, smallest)
```powershell
ollama pull phi3:mini
```
- Size: ~2GB
- Speed: Very Fast
- Quality: Decent

---

## 🐛 Troubleshooting

### Issue: "ollama: command not found"

**Solution:** Restart PowerShell or add Ollama to PATH manually:
```powershell
$env:Path += ";C:\Users\$env:USERNAME\AppData\Local\Programs\Ollama"
```

### Issue: "Connection refused on port 11434"

**Solution:** Start Ollama service:
```powershell
ollama serve
```

### Issue: Model download is slow

**Solution:** 
- Use a smaller model (llama3.2:3b or phi3:mini)
- Download during off-peak hours
- Check your internet connection

### Issue: "Out of memory" error

**Solution:**
- Close other applications
- Use a smaller model
- Increase virtual memory in Windows settings

### Issue: Responses are slow

**Solution:**
- Use a smaller/faster model
- Ensure no other heavy applications are running
- Consider GPU acceleration (if you have NVIDIA GPU)

---

## 💡 GPU Acceleration (Optional)

If you have an NVIDIA GPU, Ollama will automatically use it for faster inference. No configuration needed!

To verify GPU usage:
```powershell
ollama run mistral "test" --verbose
```

Look for "GPU: NVIDIA" in the output.

---

## 📈 Performance Expectations

| Model | Size | Speed (tokens/sec) | RAM Usage |
|-------|------|-------------------|-----------|
| Mistral 7B | 4GB | 20-30 | 8GB |
| Llama 3.2 3B | 2GB | 40-60 | 4GB |
| Phi-3 Mini | 2GB | 50-70 | 4GB |

---

## 🔧 Advanced Configuration

### Change Ollama Port

If port 11434 is already in use:

1. Set environment variable:
```powershell
$env:OLLAMA_HOST = "0.0.0.0:11435"
ollama serve
```

2. Update `.env`:
```env
OLLAMA_URL=http://localhost:11435
```

### Run Ollama as Windows Service

For production, you can run Ollama as a background service. See: https://github.com/ollama/ollama/blob/main/docs/windows.md

---

## 📚 Additional Resources

- Official Docs: https://ollama.com/docs
- Model Library: https://ollama.com/library
- GitHub: https://github.com/ollama/ollama
- Discord Community: https://discord.gg/ollama

---

## ✅ Checklist

Before using TicketFlow AI with Ollama:

- [ ] Ollama installed
- [ ] Ollama service running (port 11434)
- [ ] Mistral model downloaded
- [ ] Backend restarted
- [ ] Test ticket submitted successfully
- [ ] AI response generated (not fallback message)

---

## 🎓 For Hackathon Demo

### Quick Demo Script:

1. **Show without Ollama:**
   - Submit ticket → Generic fallback response
   - Point out "LLM unavailable" warning

2. **Start Ollama:**
   ```powershell
   ollama serve
   ```

3. **Show with Ollama:**
   - Submit same ticket → Detailed AI response
   - Highlight personalized steps and context awareness

4. **Explain the difference:**
   - "Without LLM: Generic knowledge base lookup"
   - "With LLM: Context-aware, personalized responses using RAG"

This demonstrates the power of your RAG architecture!

---

**Need help?** Check the troubleshooting section or ask for assistance.
