# 📚 How to Populate the Knowledge Base

## Problem
The Knowledge Base page shows "No articles found" because no tickets have been resolved yet, so no KB articles have been auto-generated.

## Solution
Run the knowledge base seeder script to populate it with 10 sample articles.

---

## 🚀 Quick Start

### Step 1: Navigate to Backend Directory
```bash
cd backend
```

### Step 2: Activate Virtual Environment
**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### Step 3: Run the Seeder Script
```bash
python seed_knowledge_base.py
```

### Step 4: Refresh the Frontend
Go to http://localhost:3000/knowledge-base and refresh the page.

---

## 📋 What Gets Created

The script creates **10 sample knowledge base articles** covering common IT issues:

| Article ID | Title | Category | Difficulty | Usage Count |
|------------|-------|----------|------------|-------------|
| KB-AUTH001 | Password Reset Email Not Received | Auth | Easy | 15 |
| KB-NET001 | VPN Connection Timeout Error 800 | Network | Medium | 23 |
| KB-SOFT001 | Microsoft Teams Installation | Software | Easy | 18 |
| KB-HARD001 | Office Printer Not Responding | Hardware | Medium | 12 |
| KB-EMAIL001 | Outlook Not Syncing New Emails | Email | Easy | 20 |
| KB-ACCESS001 | Shared Drive Access Request | Access | Easy | 16 |
| KB-PERF001 | Computer Running Slow | Software | Medium | 25 |
| KB-WIFI001 | WiFi Keeps Disconnecting | Network | Medium | 19 |
| KB-EXCEL001 | Excel Crashing When Opening Large Files | Software | Medium | 14 |
| KB-LOGIN001 | Account Locked After Failed Logins | Auth | Easy | 22 |

---

## 📊 Article Structure

Each article contains:

- **Title**: Clear, descriptive title
- **Category**: Auth, Network, Software, Hardware, etc.
- **Problem Description**: What the user is experiencing
- **Likely Cause**: Why this issue occurs
- **Solution Steps**: Step-by-step resolution guide (numbered list)
- **Prevention**: How to avoid this issue in the future
- **Tags**: Keywords for search (e.g., password, vpn, email)
- **Difficulty**: Easy, Medium, or Hard
- **Estimated Resolution Time**: How long it takes to resolve
- **Usage Count**: How many times this article has helped

---

## 🔍 Example Article

```json
{
  "article_id": "KB-AUTH001",
  "title": "Password Reset Email Not Received",
  "category": "Auth",
  "problem_description": "User cannot receive password reset email after requesting it through the forgot password link.",
  "likely_cause": "Email is in spam/junk folder, incorrect email address entered, or email server delay.",
  "solution_steps": [
    "Check your spam/junk folder for emails from noreply@company.com",
    "Verify that you entered the correct email address",
    "Wait 5-10 minutes for email delivery (server delays can occur)",
    "Whitelist noreply@company.com in your email settings",
    "Request a new reset link if not received within 10 minutes",
    "Contact IT support at ext. 5555 if issue persists"
  ],
  "prevention": "Add noreply@company.com to your email whitelist to prevent future delivery issues.",
  "tags": ["password", "reset", "email", "authentication", "forgot"],
  "difficulty": "Easy",
  "estimated_resolution_time": "15 minutes",
  "usage_count": 15
}
```

---

## 🎯 Features You Can Test

### 1. Search Functionality
- Search for "password" → Shows KB-AUTH001 and KB-LOGIN001
- Search for "vpn" → Shows KB-NET001
- Search for "slow" → Shows KB-PERF001

### 2. Category Filtering
- Click "Auth" → Shows 2 articles (KB-AUTH001, KB-LOGIN001)
- Click "Network" → Shows 2 articles (KB-NET001, KB-WIFI001)
- Click "Software" → Shows 3 articles (KB-SOFT001, KB-PERF001, KB-EXCEL001)

### 3. Article Expansion
- Click any article card to expand and see full details
- View solution steps, prevention tips, and tags
- See usage count and difficulty level

### 4. Sorting
- Articles are sorted by usage count (most used first)
- KB-PERF001 (25 uses) appears at the top
- KB-HARD001 (12 uses) appears lower

---

## 🔄 How Articles Are Normally Created

In production, articles are **auto-generated** when tickets are resolved:

```
1. User submits ticket
   ↓
2. AI generates solution
   ↓
3. Agent approves solution
   ↓
4. Ticket marked as resolved
   ↓
5. System calls knowledge_builder_service
   ↓
6. Mistral-Nemo LLM generates structured KB article
   ↓
7. Article saved to MongoDB
   ↓
8. Article embedding added to ChromaDB
   ↓
9. Article appears in Knowledge Base page
```

---

## 🛠️ Troubleshooting

### Issue: "ModuleNotFoundError"
**Solution**: Make sure you're in the backend directory and virtual environment is activated
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

### Issue: "Connection refused" or "MongoDB not running"
**Solution**: Start MongoDB first
```bash
mongod --dbpath /path/to/data
```

### Issue: "ChromaDB error"
**Solution**: ChromaDB will use fallback mode. Articles will still be created in MongoDB.

### Issue: Articles not showing in frontend
**Solution**: 
1. Check backend is running: http://localhost:8000/docs
2. Check API endpoint: http://localhost:8000/api/admin/knowledge-base
3. Hard refresh frontend: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
4. Check browser console for errors

---

## 🧹 Clearing the Knowledge Base

If you want to start fresh:

```python
# In Python shell or script
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def clear_kb():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["ticketflow_ai"]
    result = await db["knowledge_articles"].delete_many({})
    print(f"Deleted {result.deleted_count} articles")
    client.close()

asyncio.run(clear_kb())
```

Or run the seeder again (it clears existing articles first).

---

## 📈 Next Steps

After seeding the knowledge base:

1. **Browse Articles**: Navigate to http://localhost:3000/knowledge-base
2. **Test Search**: Try searching for "password", "vpn", "slow"
3. **Filter by Category**: Click category buttons to filter
4. **Expand Articles**: Click articles to see full solution steps
5. **Submit Real Tickets**: Create tickets and resolve them to see auto-generated articles

---

## 🎓 Understanding the Code

### MongoDB Storage
```python
# Articles stored in MongoDB collection
db["knowledge_articles"].insert_one({
    "article_id": "KB-AUTH001",
    "title": "Password Reset Email Not Received",
    # ... other fields
})
```

### ChromaDB Embeddings
```python
# Article content converted to 384-dim vector
article_content = f"{title} {description} {solution_steps}"
embedding = embedding_service.embed(article_content)

# Stored in ChromaDB for semantic search
chromadb.add(
    id="KB-AUTH001",
    embedding=embedding,
    metadata={"category": "Auth", "difficulty": "Easy"}
)
```

### Frontend API Call
```javascript
// Frontend fetches articles
adminAPI.knowledgeBase({ page_size: 50 })
  .then(response => {
    setArticles(response.data.articles);
  });
```

---

## ✅ Expected Output

When you run the seeder, you should see:

```
============================================================
  TicketFlow AI - Knowledge Base Seeder
============================================================
🌱 Seeding Knowledge Base...
Connecting to MongoDB: mongodb://localhost:27017

🗑️  Clearing existing articles...
   Deleted 0 existing articles

📝 Creating sample articles...
   ✅ Created: KB-AUTH001 - Password Reset Email Not Received
   ✅ Created: KB-NET001 - VPN Connection Timeout Error 800
   ✅ Created: KB-SOFT001 - Microsoft Teams Installation
   ✅ Created: KB-HARD001 - Office Printer Not Responding
   ✅ Created: KB-EMAIL001 - Outlook Not Syncing New Emails
   ✅ Created: KB-ACCESS001 - Shared Drive Access Request
   ✅ Created: KB-PERF001 - Computer Running Slow
   ✅ Created: KB-WIFI001 - WiFi Keeps Disconnecting
   ✅ Created: KB-EXCEL001 - Excel Crashing When Opening Large Files
   ✅ Created: KB-LOGIN001 - Account Locked After Failed Logins

✨ Successfully created 10 knowledge base articles!

📊 Articles by Category:
   • Software: 3 articles
   • Network: 2 articles
   • Auth: 2 articles
   • Email: 1 articles
   • Hardware: 1 articles
   • Access: 1 articles

🎯 Knowledge Base is ready!
   Navigate to http://localhost:3000/knowledge-base to view articles
```

---

**That's it! Your Knowledge Base should now be populated with 10 sample articles.** 🚀
