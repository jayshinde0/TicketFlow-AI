# 🎬 TicketFlow AI - Complete Demo Guide

> Step-by-step walkthrough for screen recording and showcasing all features

## 📋 Table of Contents

1. [Pre-Demo Setup](#pre-demo-setup)
2. [Demo Script](#demo-script)
3. [Sample Tickets](#sample-tickets)
4. [Navigation Flow](#navigation-flow)
5. [Key Features to Highlight](#key-features-to-highlight)

---

## 🚀 Pre-Demo Setup

### 1. Start All Services

```bash
# Terminal 1: MongoDB
mongod --dbpath /path/to/data

# Terminal 2: Ollama
ollama serve

# Terminal 3: Backend
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000

# Terminal 4: Frontend
cd frontend
npm start
```

### 2. Verify Services

- ✅ MongoDB: `mongosh` (should connect)
- ✅ Ollama: `ollama list` (should show mistral-nemo)
- ✅ Backend: http://localhost:8000/docs (should load)
- ✅ Frontend: http://localhost:3000 (should load)

### 3. Login Credentials

| Role  | Email              | Password | Use Case                    |
|-------|-------------------|----------|-----------------------------|
| User  | user@company.com  | user123  | Submit tickets              |
| Agent | agent@company.com | agent123 | Review & approve AI responses |
| Admin | admin@company.com | admin123 | View analytics & retrain models |

---

## 🎯 Demo Script (15-20 minutes)

### PART 1: Introduction (2 minutes)

**Script:**
"Welcome to TicketFlow AI - an intelligent ticket management system powered by a 10-agent AI pipeline. This system combines machine learning, natural language processing, and large language models to automate IT support workflows while keeping humans in the loop for quality control."

"Let me show you how it works from three perspectives: End User, Support Agent, and Administrator."

---

### PART 2: User Experience (5 minutes)

#### Step 1: Login as User

1. Navigate to http://localhost:3000
2. Click "Login" button
3. Enter credentials:
   - Email: `user@company.com`
   - Password: `user123`
4. Click "Sign In"

**Script:**
"First, let's see the end-user experience. I'm logging in as a regular employee who needs IT support."

#### Step 2: View Dashboard

**What you'll see:**
- Welcome message with user name
- Quick stats: Total tickets, Open tickets, Resolved tickets
- Recent tickets list
- Submit new ticket button

**Script:**
"The user dashboard shows a clean overview of all my tickets. I can see I have X open tickets and Y resolved tickets. Let's submit a new support request."

#### Step 3: Submit Ticket #1 (Auto-Resolve Scenario)

1. Click "Submit New Ticket" button
2. Fill in the form:

```
Title: Forgot my password
Description: I forgot my password and need to reset it. I tried the forgot password link but I'm not receiving the reset email. My email is john.doe@company.com. Please help me access my account.
```

3. Click "Submit Ticket"

**Script:**
"I'm submitting a common issue - password reset. Watch what happens next. The AI will process this ticket through 10 specialized agents in real-time."

#### Step 4: Watch AI Processing

**What happens (explain while showing):**
- ⏳ Ticket appears with "Processing..." status
- 🤖 AI agents analyze the ticket:
  - Agent 1: Cleans and preprocesses text
  - Agent 2: Classifies category → "Authentication" (92% confidence)
  - Agent 3: Assigns priority → "Medium" (88% confidence)
  - Agent 4: Predicts SLA → 2 hours
  - Agent 5: Analyzes sentiment → "Neutral"
  - Agent 6: Finds 2 similar resolved tickets
  - Agent 7: Calculates confidence → 89%
  - Agent 8: Generates AI response using RAG
  - Agent 9: Routes to AUTO_RESOLVE (confidence ≥ 85%)
  - Agent 10: Stores for feedback learning

**Script:**
"In just a few seconds, the AI has classified this as an Authentication issue with Medium priority, predicted a 2-hour resolution time, and generated a personalized response. Since the confidence is 89%, it auto-resolved the ticket without human intervention."

#### Step 5: View Ticket Details

1. Click on the newly created ticket
2. Show the ticket detail page

**What to highlight:**
- ✅ Status: "Resolved"
- 🏷️ Category: "Authentication" with 92% confidence
- ⚡ Priority: "Medium" badge
- ⏰ SLA Timer: "1h 58m remaining"
- 🤖 AI-Generated Response:
  ```
  To reset your password:
  1. Go to the login page and click "Forgot Password"
  2. Enter your email address (john.doe@company.com)
  3. Check your spam/junk folder for the reset email
  4. If not received within 5 minutes, contact IT support at ext. 5555
  
  The reset link expires in 1 hour for security.
  ```
- 📊 Confidence Score: 89%
- 🔍 Similar Tickets: 2 similar resolved tickets shown
- 💡 Explanation: "Classified as Authentication based on keywords: password, reset, forgot, access"

**Script:**
"Here's the magic - the AI generated a step-by-step resolution guide by retrieving relevant knowledge base articles and using the Mistral-Nemo language model. The user gets instant help without waiting for an agent."

#### Step 6: Submit Ticket #2 (Agent Review Scenario)

1. Click "Submit New Ticket"
2. Fill in the form:

```
Title: VPN connection timeout
Description: I'm unable to connect to the company VPN since this morning at 9 AM. The VPN client shows "Connecting..." for about 30 seconds then times out with error code 800. I've tried restarting the VPN client and my laptop. Other team members on the same floor seem to be affected too. I'm on Windows 11, using GlobalProtect v6.2.
```

3. Click "Submit Ticket"

**Script:**
"Now let's submit a more complex technical issue that requires agent review."

#### Step 7: Watch Processing (Agent Review)

**What happens:**
- Category: "Network" (78% confidence)
- Priority: "High" (82% confidence)
- SLA: 4 hours
- Sentiment: "Neutral"
- Confidence: 75%
- Routing: SUGGEST_TO_AGENT (60-85% confidence range)

**Script:**
"This ticket has 75% confidence - not high enough for auto-resolve but not low enough to escalate. It goes to the agent review queue where a human can approve or edit the AI's suggestion."

#### Step 8: Submit Ticket #3 (Escalation Scenario)

1. Click "Submit New Ticket"
2. Fill in the form:

```
Title: Database access denied - URGENT
Description: I'm getting "Access Denied" errors when trying to connect to the production database. This is blocking our entire development team from deploying the critical hotfix. We need immediate access restored. This has been happening for the last 30 minutes and we're losing money every minute!
```

3. Click "Submit Ticket"

**Script:**
"Finally, let's submit a critical security-related issue with frustrated sentiment."

#### Step 9: Watch Processing (Escalation)

**What happens:**
- Category: "Database" (85% confidence)
- Priority: "Critical" (95% confidence)
- SLA: 1 hour
- Sentiment: "Negative" (frustrated user detected)
- Overrides: Database category + Frustrated sentiment
- Routing: ESCALATE_TO_HUMAN

**Script:**
"The AI detected this is a Database issue with a frustrated user. Business rules automatically escalate Database and Security tickets to senior engineers, regardless of confidence. The sentiment analysis also triggered an escalation override."

---

### PART 3: Agent Experience (5 minutes)

#### Step 10: Logout and Login as Agent

1. Click user menu → "Logout"
2. Login with:
   - Email: `agent@company.com`
   - Password: `agent123`

**Script:**
"Now let's switch to the agent perspective. Agents review AI suggestions before they're sent to users."

#### Step 11: View Agent Dashboard

**What you'll see:**
- Agent workload stats
- Review queue with pending tickets
- Recent activity
- Performance metrics

**Script:**
"The agent dashboard shows I have 1 ticket in my review queue - the VPN issue we submitted earlier."

#### Step 12: Review Queue

1. Click "Review Queue" in sidebar
2. Show the list of tickets needing review

**What to highlight:**
- Ticket card shows:
  - Title and description preview
  - AI predictions (category, priority, SLA)
  - Confidence score with badge
  - AI-generated response preview
  - Action buttons: Approve, Edit, Reject, Escalate

**Script:**
"Here's the VPN ticket waiting for my review. I can see the AI's classification, the generated response, and the confidence score. Let me review the AI's suggestion."

#### Step 13: Review Ticket Details

1. Click on the VPN ticket
2. Show the review panel

**What to highlight:**
- 📋 Full ticket details
- 🤖 AI Predictions section:
  - Category: Network (78%)
  - Priority: High (82%)
  - SLA: 4 hours
- 💬 AI-Generated Response (full text)
- 🔍 Similar Tickets: 3 similar resolved tickets
- 💡 LIME Explanation: Feature importance chart
- 📊 Confidence breakdown by agent

**Script:**
"The AI suggests this is a Network issue with High priority. The generated response provides troubleshooting steps based on similar tickets. I can see the explanation showing which keywords influenced the classification."

#### Step 14: Approve with Edit

1. Click "Edit Response" button
2. Modify the AI response:

```
[Original AI response]

UPDATE: We've identified a VPN server issue affecting your floor. Our network team is working on it. ETA: 30 minutes.

- IT Support Team
```

3. Click "Approve & Send"

**Script:**
"The AI response is good, but I'll add an update about the server issue. This approval becomes training data - the system learns that this classification was correct."

#### Step 15: View Similar Tickets

1. Scroll to "Similar Resolved Tickets" section
2. Click on one of the similar tickets

**What to highlight:**
- Shows previously resolved tickets with >70% similarity
- Displays resolution that worked before
- Helps agents learn from past solutions

**Script:**
"The duplicate detection agent found 3 similar VPN issues. I can see how they were resolved before, which helps me provide consistent support."

#### Step 16: Reject a Prediction (Demo)

1. Go back to review queue
2. For demonstration, click "Reject" on a ticket
3. Fill in the rejection form:

```
Reason: Incorrect category
Correct Category: Hardware
Correct Priority: Medium
Feedback: This is a hardware issue (laptop), not network
```

4. Click "Submit Feedback"

**Script:**
"If the AI makes a mistake, I can reject it and provide the correct classification. This feedback is stored and used to retrain the models when accuracy drops below 80%."

---

### PART 4: Analytics Dashboard (5 minutes)

#### Step 17: Navigate to Analytics

1. Click "Analytics" in the sidebar

**Script:**
"Now let's look at the analytics dashboard where we can see system performance and insights."

#### Step 18: Overview Metrics

**What to highlight:**
- 📊 Ticket Volume Chart (last 30 days)
  - Line chart showing daily ticket submissions
  - Trend analysis
- 🎯 Resolution Funnel
  - Auto-Resolved: 45%
  - Agent-Approved: 35%
  - Escalated: 20%
- ⏱️ Average Resolution Time: 2.3 hours
- 📈 SLA Compliance: 92%

**Script:**
"We can see ticket volume trends over the last month. The resolution funnel shows that 45% of tickets are auto-resolved by AI, 35% need agent approval, and only 20% require escalation. This means 80% of tickets get AI assistance."

#### Step 19: Category Distribution

**What to highlight:**
- 🥧 Pie Chart showing:
  - Authentication: 25%
  - Network: 20%
  - Software: 18%
  - Hardware: 15%
  - Email: 10%
  - Database: 5%
  - Security: 3%
  - Access: 2%
  - Performance: 1%
  - Other: 1%

**Script:**
"The category distribution shows Authentication and Network issues are most common. This helps us allocate resources and create targeted knowledge base articles."

#### Step 20: Sentiment Analysis

**What to highlight:**
- 📊 Bar Chart:
  - Positive: 15%
  - Neutral: 70%
  - Negative: 15%
- Frustrated user detection rate
- Escalation triggers

**Script:**
"Sentiment analysis helps us identify frustrated users who need priority attention. 15% of tickets show negative sentiment, triggering automatic escalation."

#### Step 21: Agent Workload

**What to highlight:**
- 👥 Agent performance table:
  - Agent name
  - Tickets reviewed
  - Avg review time
  - Approval rate
  - Rejection rate
- Workload distribution chart

**Script:**
"We can track agent performance - how many tickets they review, their average review time, and approval rates. This helps balance workload and identify training needs."

#### Step 22: SLA Risk Alerts

**What to highlight:**
- ⚠️ Tickets at risk of SLA breach
- Color-coded urgency (red, yellow, green)
- Time remaining until deadline
- Recommended actions

**Script:**
"The SLA monitoring shows tickets approaching their deadlines. Red alerts indicate tickets with less than 1 hour remaining, helping agents prioritize their work."

---

### PART 5: ML Performance Dashboard (3 minutes)

#### Step 23: Navigate to ML Performance

1. Click "ML Performance" tab in Analytics

**Script:**
"Let's dive into the machine learning performance metrics to see how accurate our AI agents are."

#### Step 24: Model Metrics

**What to highlight:**
- 📊 Metrics Table:
  - Category Classifier: 87% accuracy, 0.86 F1-score
  - Priority Classifier: 84% accuracy, 0.83 F1-score
  - SLA Predictor: 2.1 hours MAE
- Training history graph
- Model version comparison

**Script:**
"Our category classifier has 87% accuracy, which is excellent for a 10-class problem. The priority classifier achieves 84% accuracy. These metrics are tracked over time to detect model drift."

#### Step 25: Confusion Matrix

**What to highlight:**
- 🎯 Confusion matrix heatmap
- Diagonal shows correct predictions
- Off-diagonal shows misclassifications
- Common confusion pairs (e.g., Network vs Hardware)

**Script:**
"The confusion matrix shows where the model makes mistakes. We can see it sometimes confuses Network issues with Hardware issues, which makes sense since they're related."

#### Step 26: Feature Importance

**What to highlight:**
- 📊 Bar chart of top features:
  - "password" → Authentication
  - "network" → Network
  - "error" → Software
  - "access" → Access
  - "slow" → Performance
- TF-IDF scores

**Script:**
"Feature importance shows which keywords drive predictions. Words like 'password' strongly indicate Authentication issues, while 'network' and 'connection' indicate Network problems."

#### Step 27: Calibration Plot

**What to highlight:**
- 📈 Calibration curve
- Diagonal line = perfect calibration
- Shows if confidence scores match actual accuracy
- Reliability diagram

**Script:**
"The calibration plot shows our confidence scores are well-calibrated. When the model says 90% confidence, it's actually correct 90% of the time. This is crucial for the auto-resolve threshold."

---

### PART 6: Admin Features (2 minutes)

#### Step 28: Logout and Login as Admin

1. Logout
2. Login with:
   - Email: `admin@company.com`
   - Password: `admin123`

**Script:**
"Finally, let's look at admin capabilities for system management."

#### Step 29: Admin Panel

1. Click "Admin Panel" in sidebar

**What to highlight:**
- 🔧 System Health
  - MongoDB: Connected
  - Ollama: Running
  - ChromaDB: Healthy
  - Models: Loaded
- 📊 Database Stats
  - Total tickets: 150
  - Total users: 25
  - Feedback samples: 120
- 🤖 Model Information
  - Last trained: 2 days ago
  - Training samples: 5,000
  - Current accuracy: 87%

**Script:**
"The admin panel shows system health and database statistics. We can see all services are running and models are loaded."

#### Step 30: Trigger Retraining

1. Click "Retrain Models" button
2. Show confirmation dialog
3. Click "Confirm"
4. Watch progress indicator

**What happens:**
- Fetches feedback data from MongoDB
- Combines with original training data
- Retrains all 3 models
- Saves new models to artifacts/
- Updates model version
- Shows completion message

**Script:**
"When model accuracy drops below 80% or we accumulate enough feedback, we can trigger retraining. The system learns from agent corrections and improves over time. This is the continuous learning loop."

---

## 📝 Sample Tickets for Demo

### Auto-Resolve Tickets (High Confidence ≥85%)

#### 1. Password Reset
```
Title: Forgot my password
Description: I forgot my password and need to reset it. I tried the forgot password link but I'm not receiving the reset email. My email is john.doe@company.com. Please help me access my account.

Expected:
- Category: Authentication (92%)
- Priority: Medium (88%)
- SLA: 2 hours
- Routing: AUTO_RESOLVE
```

#### 2. Printer Not Working
```
Title: Office printer not responding
Description: The printer on the 3rd floor (HP LaserJet 4050) is not responding. I've tried turning it off and on, but it still shows offline on my computer. I need to print urgent documents for a meeting in 1 hour.

Expected:
- Category: Hardware (89%)
- Priority: High (86%)
- SLA: 1 hour
- Routing: AUTO_RESOLVE
```

#### 3. Software Installation
```
Title: Need Microsoft Teams installed
Description: I need Microsoft Teams installed on my laptop for remote meetings. I'm a new employee and it wasn't included in my initial setup. My laptop is a Dell Latitude 5520 running Windows 11.

Expected:
- Category: Software (91%)
- Priority: Medium (85%)
- SLA: 4 hours
- Routing: AUTO_RESOLVE
```

### Agent Review Tickets (Medium Confidence 60-85%)

#### 4. VPN Connection Issue
```
Title: VPN connection timeout
Description: I'm unable to connect to the company VPN since this morning at 9 AM. The VPN client shows "Connecting..." for about 30 seconds then times out with error code 800. I've tried restarting the VPN client and my laptop. Other team members on the same floor seem to be affected too. I'm on Windows 11, using GlobalProtect v6.2.

Expected:
- Category: Network (78%)
- Priority: High (82%)
- SLA: 4 hours
- Routing: SUGGEST_TO_AGENT
```

#### 5. Email Sync Problem
```
Title: Outlook not syncing emails
Description: My Outlook is not syncing new emails since yesterday evening. I can send emails but not receive them. I've checked my internet connection and it's working fine. Other applications like Teams and browser work normally. I'm using Outlook 2021 on Windows 10.

Expected:
- Category: Email (72%)
- Priority: Medium (75%)
- SLA: 6 hours
- Routing: SUGGEST_TO_AGENT
```

#### 6. Slow Computer Performance
```
Title: Computer running very slow
Description: My computer has been running extremely slow for the past week. Applications take forever to open, and sometimes the screen freezes for 10-15 seconds. I've tried restarting multiple times but the issue persists. I have important deadlines coming up and this is affecting my productivity.

Expected:
- Category: Performance (68%)
- Priority: Medium (70%)
- SLA: 8 hours
- Routing: SUGGEST_TO_AGENT
```

### Escalation Tickets (Low Confidence <60% or Override)

#### 7. Database Access (Category Override)
```
Title: Database access denied - URGENT
Description: I'm getting "Access Denied" errors when trying to connect to the production database. This is blocking our entire development team from deploying the critical hotfix. We need immediate access restored. This has been happening for the last 30 minutes and we're losing money every minute!

Expected:
- Category: Database (85%)
- Priority: Critical (95%)
- SLA: 1 hour
- Override: Database category → ESCALATE
- Routing: ESCALATE_TO_HUMAN
```

#### 8. Security Breach (Category Override)
```
Title: Suspicious login attempts on my account
Description: I received 15 security alerts about failed login attempts on my account from an IP address in Russia. I haven't traveled recently and I'm currently in the US. I'm worried my account has been compromised. Please investigate immediately and secure my account.

Expected:
- Category: Security (88%)
- Priority: Critical (92%)
- SLA: 30 minutes
- Override: Security category → ESCALATE
- Routing: ESCALATE_TO_HUMAN
```

#### 9. Frustrated User (Sentiment Override)
```
Title: STILL can't access shared drive - 3rd time reporting!
Description: This is the THIRD time I'm reporting this issue and NOBODY has fixed it! I can't access the shared drive and I'm missing deadlines because of this. This is completely unacceptable! I've been waiting for 2 days and I'm extremely frustrated. I need this fixed NOW or I'm escalating to management!

Expected:
- Category: Access (75%)
- Priority: High (80%)
- SLA: 2 hours
- Override: Negative sentiment → ESCALATE
- Routing: ESCALATE_TO_HUMAN
```

---

## 🎬 Navigation Flow Summary

### User Journey
```
Login (User) 
  → Dashboard 
  → Submit Ticket 
  → View Ticket Details 
  → See AI Response 
  → Check Similar Tickets
```

### Agent Journey
```
Login (Agent) 
  → Agent Dashboard 
  → Review Queue 
  → Ticket Details 
  → Review AI Predictions 
  → Approve/Edit/Reject 
  → View Similar Tickets
```

### Admin Journey
```
Login (Admin) 
  → Analytics Dashboard 
  → View Metrics 
  → ML Performance 
  → Admin Panel 
  → Trigger Retraining
```

---

## 🎯 Key Features to Highlight

### 1. Real-time AI Processing
- Show the "Processing..." indicator
- Explain each agent's role
- Highlight speed (2-3 seconds)

### 2. Confidence-Based Routing
- Auto-resolve: ≥85% confidence
- Agent review: 60-85% confidence
- Escalation: <60% or overrides

### 3. RAG Response Generation
- ChromaDB retrieval
- Mistral-Nemo LLM
- Context-aware responses

### 4. Explainable AI
- LIME explanations
- Feature importance
- Confidence breakdown

### 5. Human-in-the-Loop
- Agent review queue
- Approve/reject feedback
- Continuous learning

### 6. Business Rules
- Category overrides (Security, Database)
- Sentiment overrides (Frustrated users)
- SLA prioritization

### 7. Analytics & Insights
- Real-time metrics
- ML performance tracking
- Agent workload monitoring

### 8. Continuous Learning
- Feedback collection
- Auto-retraining triggers
- Model versioning

---

## 📊 Expected Results

After submitting the 9 sample tickets:

| Ticket | Category | Priority | Confidence | Routing |
|--------|----------|----------|------------|---------|
| 1. Password Reset | Auth | Medium | 92% | Auto-Resolve |
| 2. Printer | Hardware | High | 89% | Auto-Resolve |
| 3. Teams Install | Software | Medium | 91% | Auto-Resolve |
| 4. VPN Timeout | Network | High | 78% | Agent Review |
| 5. Outlook Sync | Email | Medium | 72% | Agent Review |
| 6. Slow Computer | Performance | Medium | 68% | Agent Review |
| 7. Database Access | Database | Critical | 85% | Escalate (Override) |
| 8. Security Breach | Security | Critical | 88% | Escalate (Override) |
| 9. Frustrated User | Access | High | 75% | Escalate (Sentiment) |

**Resolution Breakdown:**
- Auto-Resolved: 3 tickets (33%)
- Agent Review: 3 tickets (33%)
- Escalated: 3 tickets (33%)

---

## 🎤 Talking Points

### Opening (30 seconds)
"TicketFlow AI revolutionizes IT support by combining machine learning, NLP, and large language models. It's not just automation - it's intelligent automation with human oversight."

### User Experience (1 minute)
"Users get instant responses for common issues. The AI understands their problem, finds relevant solutions, and generates personalized step-by-step guides. No waiting in queue for simple password resets."

### Agent Experience (1 minute)
"Agents focus on complex issues while AI handles routine tickets. They review AI suggestions, provide feedback, and the system learns from every interaction. It's augmented intelligence, not replacement."

### Analytics (1 minute)
"Real-time dashboards show ticket trends, ML performance, and agent workload. Admins can track accuracy, identify patterns, and trigger retraining when needed. Complete visibility into system performance."

### Closing (30 seconds)
"TicketFlow AI reduces resolution time by 60%, improves agent productivity by 40%, and maintains 92% SLA compliance. It's the future of IT support - intelligent, explainable, and continuously improving."

---

## 📹 Recording Tips

1. **Clear Browser Cache**: Start with a clean slate
2. **Zoom Level**: Set browser to 90% for better visibility
3. **Mouse Highlighting**: Use a cursor highlighter tool
4. **Smooth Transitions**: Pause 2 seconds between actions
5. **Narration**: Speak clearly and explain what you're doing
6. **Error Handling**: If something fails, explain it's a demo environment
7. **Time Management**: Aim for 15-20 minutes total
8. **Call to Action**: End with GitHub link and invitation to contribute

---

**Good luck with your demo! 🚀**
