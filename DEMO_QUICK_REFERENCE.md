# 🎬 TicketFlow AI - Quick Demo Reference Card

## 🔑 Login Credentials

| Role  | Email              | Password | Purpose                    |
|-------|-------------------|----------|----------------------------|
| 👤 User  | user@company.com  | user123  | Submit & view tickets      |
| 👨‍💼 Agent | agent@company.com | agent123 | Review AI suggestions      |
| 👑 Admin | admin@company.com | admin123 | Analytics & system admin   |

## 🎯 Demo Flow (15 minutes)

### Part 1: User (5 min)
1. Login as User
2. View Dashboard
3. Submit 3 tickets:
   - ✅ Password Reset (Auto-Resolve)
   - 🔍 VPN Timeout (Agent Review)
   - ⚠️ Database Access (Escalate)
4. View ticket details & AI responses

### Part 2: Agent (5 min)
1. Login as Agent
2. View Review Queue
3. Review VPN ticket
4. Approve with edit
5. View similar tickets

### Part 3: Analytics (5 min)
1. Login as Admin
2. View Analytics Dashboard
3. Check ML Performance
4. Trigger Retraining

## 📝 Sample Tickets (Copy-Paste Ready)

### Ticket 1: Auto-Resolve ✅
```
Title: Forgot my password

Description: I forgot my password and need to reset it. I tried the forgot password link but I'm not receiving the reset email. My email is john.doe@company.com. Please help me access my account.
```
**Expected:** Auth (92%), Medium, AUTO_RESOLVE

### Ticket 2: Agent Review 🔍
```
Title: VPN connection timeout

Description: I'm unable to connect to the company VPN since this morning at 9 AM. The VPN client shows "Connecting..." for about 30 seconds then times out with error code 800. I've tried restarting the VPN client and my laptop. Other team members on the same floor seem to be affected too. I'm on Windows 11, using GlobalProtect v6.2.
```
**Expected:** Network (78%), High, SUGGEST_TO_AGENT

### Ticket 3: Escalation ⚠️
```
Title: Database access denied - URGENT

Description: I'm getting "Access Denied" errors when trying to connect to the production database. This is blocking our entire development team from deploying the critical hotfix. We need immediate access restored. This has been happening for the last 30 minutes and we're losing money every minute!
```
**Expected:** Database (85%), Critical, ESCALATE_TO_HUMAN

## 🎤 Key Talking Points

### Opening
"TicketFlow AI combines ML, NLP, and LLMs to automate IT support while keeping humans in the loop."

### 10-Agent Pipeline
1. NLP Preprocessing
2. Category Classification
3. Priority Classification
4. SLA Prediction
5. Sentiment Analysis
6. Duplicate Detection
7. Confidence Scoring
8. Response Generation (RAG)
9. HITL Routing
10. Feedback & Retraining

### Confidence Thresholds
- **≥85%**: Auto-Resolve (instant response)
- **60-85%**: Agent Review (human approval)
- **<60%**: Escalate (manual handling)

### Business Rules
- Security tickets → Always escalate
- Database tickets → Always escalate
- Frustrated users → Always escalate

### RAG Architecture
1. Embed ticket description
2. Search ChromaDB (top 3 articles)
3. Build context
4. Generate with Mistral-Nemo
5. Return personalized response

## 📊 Dashboard Navigation

### User Dashboard
- Submit New Ticket
- My Tickets
- Ticket Details
- AI Response
- Similar Tickets

### Agent Dashboard
- Review Queue
- Ticket Details
- AI Predictions
- Approve/Edit/Reject
- Similar Tickets
- LIME Explanation

### Analytics Dashboard
- Ticket Volume Chart
- Resolution Funnel
- Category Distribution
- Sentiment Analysis
- Agent Workload
- SLA Risk Alerts

### ML Performance
- Model Metrics Table
- Confusion Matrix
- Feature Importance
- Calibration Plot
- Training History

## 🎯 Features to Highlight

✅ Real-time AI processing (2-3 seconds)
✅ Confidence-based routing
✅ RAG response generation
✅ Explainable AI (LIME)
✅ Human-in-the-loop feedback
✅ Business rule overrides
✅ Continuous learning
✅ Auto-retraining

## 🚀 Quick Start Commands

```bash
# Generate demo tickets
cd backend
python generate_demo_tickets.py

# Start backend
uvicorn main:app --reload --port 8000

# Start frontend
cd frontend
npm start
```

## 📈 Expected Results

After processing 9 tickets:
- Auto-Resolved: 3 (33%)
- Agent Review: 3 (33%)
- Escalated: 3 (33%)

**Metrics:**
- Avg Resolution Time: 2.3 hours
- SLA Compliance: 92%
- Category Accuracy: 87%
- Priority Accuracy: 84%

## 🎬 Recording Checklist

- [ ] Clear browser cache
- [ ] Set zoom to 90%
- [ ] Enable cursor highlighting
- [ ] Test microphone
- [ ] Close unnecessary tabs
- [ ] Disable notifications
- [ ] Prepare sample tickets
- [ ] Test all services running

## 💡 Pro Tips

1. **Pause between actions** - Give viewers time to see
2. **Explain while doing** - Narrate your actions
3. **Show confidence scores** - Highlight AI transparency
4. **Demonstrate feedback loop** - Show learning
5. **Compare before/after** - Show improvement
6. **Handle errors gracefully** - Explain if something fails
7. **End with CTA** - GitHub link + contribute

## 🔗 Important URLs

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- GitHub: https://github.com/jayshinde0/TicketFlow-AI

---

**Good luck! 🚀 You've got this!**
