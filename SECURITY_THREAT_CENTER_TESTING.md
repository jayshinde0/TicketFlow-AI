# 🛡️ Security Threat Center - Testing Guide

## Overview

The Security Threat Center is an AI-powered attack detection system that analyzes tickets in real-time to identify security threats using a 5-step AI pipeline.

---

## 🎯 Features to Test

### 1. AI-Powered Attack Detection
- SQL Injection detection
- XSS (Cross-Site Scripting) detection
- Brute force attack detection
- DDoS pattern detection
- Unauthorized access attempts
- Phishing detection

### 2. Real-Time Monitoring
- WebSocket alerts for security threats
- Live threat dashboard
- Automatic escalation

### 3. Threat Classification
- **Normal**: Safe tickets
- **Suspicious**: Requires manual review
- **Attack**: Immediate escalation

---

## 🚀 How to Access

### Step 1: Login as Admin
```
URL: http://localhost:3000/login
Email: admin@company.com
Password: admin123
```

### Step 2: Navigate to Security Center
```
URL: http://localhost:3000/admin/security
Or: Click "Security" in the admin navigation menu
```

---

## 🧪 Test Scenarios

### Test 1: SQL Injection Attack

**Submit this ticket:**
```
Subject: Database error on login page

Description: I'm getting an error when I try to login with username: 
admin' OR '1'='1' -- 
The system shows "SQL syntax error". Can you help me access my account?
```

**Expected Result:**
- ✅ Threat Level: **ATTACK**
- ✅ Threat Type: **sql_injection**
- ✅ Confidence: 85-95%
- ✅ Auto-escalated: YES
- ✅ Priority: CRITICAL
- ✅ Real-time alert triggered

**Triggered Rules:**
- SQL injection pattern detected
- Suspicious SQL keywords (OR, --, ')
- High confidence ML classification

---

### Test 2: XSS (Cross-Site Scripting) Attack

**Submit this ticket:**
```
Subject: Profile page not displaying correctly

Description: When I update my profile with this bio:
<script>alert('XSS')</script>
The page breaks. Can you fix this? My username is: <img src=x onerror=alert(1)>
```

**Expected Result:**
- ✅ Threat Level: **ATTACK**
- ✅ Threat Type: **xss**
- ✅ Confidence: 80-90%
- ✅ Auto-escalated: YES
- ✅ Triggered Rules: XSS pattern, script tags, event handlers

---

### Test 3: Brute Force Attack

**Submit this ticket:**
```
Subject: Cannot login - account locked

Description: I've been trying to login for the past hour with different passwords. 
I tried my password 50 times but keep getting "invalid credentials". 
My account is now locked. I need immediate access. 
Tried passwords: password123, Password123, PASSWORD123, admin123, etc.
```

**Expected Result:**
- ✅ Threat Level: **SUSPICIOUS** or **ATTACK**
- ✅ Threat Type: **brute_force**
- ✅ Confidence: 70-85%
- ✅ Triggered Rules: Multiple login attempts, password enumeration

---

### Test 4: Unauthorized Access Attempt

**Submit this ticket:**
```
Subject: Need admin access to production database

Description: I need admin privileges to access the production database directly. 
Can you give me root access to db-prod-01.company.com? 
I want to run some queries on the customer_data table. 
Also need SSH access to the server. My IP is 192.168.1.100.
```

**Expected Result:**
- ✅ Threat Level: **SUSPICIOUS**
- ✅ Threat Type: **unauthorized_access**
- ✅ Confidence: 75-85%
- ✅ Triggered Rules: Privilege escalation, sensitive data access

---

### Test 5: DDoS Pattern

**Submit this ticket:**
```
Subject: Website very slow - testing load

Description: I'm testing the website performance by sending 10,000 requests per second 
from multiple IP addresses. The site is responding very slowly. 
I'm using a script to flood the server with traffic. 
Can you increase server capacity? Running stress test from 100 different IPs.
```

**Expected Result:**
- ✅ Threat Level: **ATTACK**
- ✅ Threat Type: **ddos**
- ✅ Confidence: 80-90%
- ✅ Triggered Rules: DDoS keywords, flooding, multiple IPs

---

### Test 6: Phishing Attempt

**Submit this ticket:**
```
Subject: Urgent: Verify your account credentials

Description: Dear user, we detected suspicious activity on your account. 
Please click this link to verify your credentials: http://fake-company-login.com
Enter your username and password to confirm your identity. 
If you don't verify within 24 hours, your account will be suspended.
This is urgent - act now!
```

**Expected Result:**
- ✅ Threat Level: **ATTACK**
- ✅ Threat Type: **phishing**
- ✅ Confidence: 85-95%
- ✅ Triggered Rules: Phishing keywords, urgency, credential request

---

### Test 7: Normal Ticket (Control Test)

**Submit this ticket:**
```
Subject: Printer not working

Description: The office printer on the 3rd floor is not responding. 
I've tried turning it off and on. The printer shows offline on my computer. 
Can you help me get it working? I need to print documents for a meeting.
```

**Expected Result:**
- ✅ Threat Level: **NORMAL**
- ✅ Threat Type: **none**
- ✅ Confidence: 95%+
- ✅ Auto-escalated: NO
- ✅ Normal ticket processing continues

---

## 📊 Security Dashboard Features

### Threat Statistics
- Total threats detected
- Attacks vs Suspicious vs Normal
- Threat types distribution
- Detection confidence average

### Real-Time Monitoring
- Live threat feed
- Recent security events
- Active investigations
- Escalation queue

### Threat Details View
- Ticket information
- AI analysis results
- Triggered rules
- Confidence scores
- Detection timeline

### Response Playbooks
- SQL Injection response guide
- XSS mitigation steps
- Brute force handling
- DDoS response procedures
- Phishing investigation

---

## 🔍 How to Verify Detection

### Method 1: Check Security Dashboard
1. Go to http://localhost:3000/admin/security
2. View "Recent Threats" section
3. Click on a threat to see details

### Method 2: Check Ticket Details
1. Go to ticket queue
2. Open the suspicious ticket
3. Look for "Security Analysis" section
4. Check threat level badge (red = attack, yellow = suspicious)

### Method 3: Check Backend Logs
```powershell
# In backend terminal, look for:
"Security threat detected: attack"
"Triggered rules: ['sql_injection_pattern', 'suspicious_keywords']"
"Auto-escalating ticket to security team"
```

### Method 4: WebSocket Real-Time Alerts
- Watch for real-time notifications
- Security alerts appear immediately
- Check browser console for WebSocket messages

---

## 🎓 AI Pipeline Breakdown

### Step 1: Preprocessing
- Text cleaning and normalization
- Tokenization
- Entity extraction

### Step 2: Embedding Generation
- Converts text to 384-dimensional vector
- Uses sentence-transformers (all-MiniLM-L6-v2)
- Enables semantic similarity comparison

### Step 3: ML Classification
- Logistic Regression / Random Forest
- Trained on security threat patterns
- Outputs threat probability

### Step 4: Sentiment & Anomaly Detection
- RoBERTa sentiment analysis
- Keyword-based anomaly detection
- Urgency and tone analysis

### Step 5: Rule Engine
- Pattern matching for known attacks
- SQL injection regex
- XSS tag detection
- Brute force indicators
- DDoS patterns

### Hidden Attack Detection
```
IF ML says "normal" 
BUT (security keywords found OR anomaly detected)
THEN reclassify as "suspicious"
```

---

## 🛠️ Testing API Endpoints

### Analyze Ticket (POST)
```bash
curl -X POST http://localhost:8000/api/security/analyze-ticket \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "ticket_id": "TKT-0001",
    "subject": "Database error",
    "description": "admin OR 1=1 --",
    "ml_category": "Security",
    "ml_confidence": 0.8
  }'
```

### Get Threats (GET)
```bash
curl http://localhost:8000/api/security/threats?threat_level=attack \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Statistics (GET)
```bash
curl http://localhost:8000/api/security/stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📈 Success Criteria

### For Attack Detection:
- ✅ SQL injection detected with 85%+ confidence
- ✅ XSS patterns identified correctly
- ✅ Brute force attempts flagged
- ✅ Auto-escalation triggered
- ✅ Priority set to CRITICAL
- ✅ Real-time alert sent

### For Normal Tickets:
- ✅ No false positives
- ✅ Normal processing continues
- ✅ No unnecessary escalations

### For Dashboard:
- ✅ Statistics update in real-time
- ✅ Threat details display correctly
- ✅ Playbooks accessible
- ✅ Filters work properly

---

## 🐛 Troubleshooting

### Issue: No threats detected
**Solution:**
- Check if backend is running
- Verify ML models are loaded
- Check backend logs for errors

### Issue: False positives
**Solution:**
- Adjust confidence thresholds in rule_engine.py
- Retrain ML models with more data
- Fine-tune rule patterns

### Issue: WebSocket alerts not working
**Solution:**
- Check WebSocket connection in browser console
- Verify user is logged in as admin/agent
- Restart backend

### Issue: Dashboard not loading
**Solution:**
- Check frontend console for errors
- Verify API endpoints are accessible
- Check authentication token

---

## 🎯 Demo Script for Hackathon

### 1. Introduction (1 minute)
"Our Security Threat Center uses a 5-step AI pipeline to detect attacks in real-time."

### 2. Show Normal Ticket (30 seconds)
Submit printer issue → Show "Normal" classification

### 3. Show SQL Injection Attack (1 minute)
Submit SQL injection ticket → Show immediate detection → Real-time alert → Auto-escalation

### 4. Show Dashboard (1 minute)
Navigate to Security Center → Show statistics → Show threat details → Show playbook

### 5. Explain AI Pipeline (1 minute)
"The system uses ML classification, sentiment analysis, and rule-based detection to identify threats with 85%+ accuracy."

### 6. Show Response (30 seconds)
"Attacks are automatically escalated to security team with safe response message."

---

## 📚 Additional Resources

- `backend/services/ai_pipeline.py` - AI detection logic
- `backend/services/rule_engine.py` - Security rules
- `backend/routers/security.py` - API endpoints
- `frontend/src/pages/AdminSecurity.jsx` - Dashboard UI

---

**Ready to test?** Start with Test 1 (SQL Injection) and work through all scenarios!
