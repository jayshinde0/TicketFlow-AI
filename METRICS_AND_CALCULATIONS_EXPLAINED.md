# 📊 TicketFlow AI - Metrics & Calculations Explained

## 📋 Table of Contents

1. [Model Accuracy Metrics](#model-accuracy-metrics)
2. [Confidence Score Calculation](#confidence-score-calculation)
3. [SLA Calculation](#sla-calculation)
4. [Performance Metrics](#performance-metrics)
5. [Calibration Metrics](#calibration-metrics)
6. [Real-World Examples](#real-world-examples)

---

## 🎯 Model Accuracy Metrics

### 1. Accuracy
**Definition**: Percentage of correct predictions out of total predictions

**Formula**:
```
Accuracy = (Correct Predictions) / (Total Predictions)
         = (TP + TN) / (TP + TN + FP + FN)
```

Where:
- **TP** (True Positive): Correctly predicted positive class
- **TN** (True Negative): Correctly predicted negative class
- **FP** (False Positive): Incorrectly predicted positive (Type I error)
- **FN** (False Negative): Incorrectly predicted negative (Type II error)

**Example**:
```python
# Category Classifier on 100 test tickets
Correct predictions: 87
Total predictions: 100
Accuracy = 87 / 100 = 0.87 = 87%
```

**Code Implementation**:
```python
from sklearn.metrics import accuracy_score

y_true = ["Auth", "Network", "Software", "Auth", "Hardware"]
y_pred = ["Auth", "Network", "Hardware", "Auth", "Hardware"]

accuracy = accuracy_score(y_true, y_pred)
# Result: 0.80 (4 out of 5 correct)
```

---

### 2. Precision
**Definition**: Of all positive predictions, how many were actually correct?

**Formula**:
```
Precision = TP / (TP + FP)
```

**Example**:
```python
# For "Authentication" category
Model predicted "Auth": 50 times
Actually "Auth": 45 times
False positives: 5 times

Precision = 45 / (45 + 5) = 45 / 50 = 0.90 = 90%
```

**Interpretation**: When the model says "Authentication", it's correct 90% of the time.

---

### 3. Recall (Sensitivity)
**Definition**: Of all actual positive cases, how many did we correctly identify?

**Formula**:
```
Recall = TP / (TP + FN)
```

**Example**:
```python
# For "Authentication" category
Actually "Auth" tickets: 50
Model correctly identified: 45
Model missed (FN): 5

Recall = 45 / (45 + 5) = 45 / 50 = 0.90 = 90%
```

**Interpretation**: The model catches 90% of all Authentication tickets.

---

### 4. F1-Score
**Definition**: Harmonic mean of Precision and Recall (balanced metric)

**Formula**:
```
F1 = 2 × (Precision × Recall) / (Precision + Recall)
```

**Example**:
```python
Precision = 0.90
Recall = 0.85

F1 = 2 × (0.90 × 0.85) / (0.90 + 0.85)
   = 2 × 0.765 / 1.75
   = 1.53 / 1.75
   = 0.874 = 87.4%
```

**Why F1?**: Balances precision and recall. Better than accuracy for imbalanced datasets.

---

### 5. Macro F1-Score
**Definition**: Average F1-score across all classes (treats all classes equally)

**Formula**:
```
Macro F1 = (F1_class1 + F1_class2 + ... + F1_classN) / N
```

**Example**:
```python
# 10 categories
F1_Auth = 0.92
F1_Network = 0.88
F1_Software = 0.85
... (7 more categories)

Macro F1 = (0.92 + 0.88 + 0.85 + ... + 0.80) / 10 = 0.86
```

**Code Implementation**:
```python
from sklearn.metrics import f1_score

y_true = ["Auth", "Network", "Software", "Auth", "Hardware"]
y_pred = ["Auth", "Network", "Hardware", "Auth", "Hardware"]

macro_f1 = f1_score(y_true, y_pred, average='macro')
# Result: 0.83
```

---

## 🎲 Confidence Score Calculation

### Composite Confidence Formula

The system uses a **weighted combination** of 3 components:

```
Confidence = (0.50 × Model_Probability) 
           + (0.35 × Similarity_Score) 
           + (0.15 × Keyword_Boost)
```

### Component 1: Model Probability (50% weight)

**Source**: Softmax output from Logistic Regression classifier

**Calculation**:
```python
# Logistic Regression outputs probabilities for all 10 categories
probabilities = model.predict_proba(ticket_features)
# Example: [0.92, 0.03, 0.02, 0.01, 0.01, 0.00, 0.00, 0.00, 0.01, 0.00]
#          [Auth, Net,  Soft, Hard, Access, Bill, Email, Sec, Srv, DB]

model_confidence = max(probabilities)  # 0.92 for "Auth"
model_component = 0.50 × 0.92 = 0.46
```

**Why 50%?**: Model prediction is the primary signal, so it gets the highest weight.

---

### Component 2: Similarity Score (35% weight)

**Source**: Cosine similarity from ChromaDB vector search

**Calculation**:
```python
# Find top 3 similar resolved tickets
similar_tickets = chromadb.query(ticket_embedding, n_results=3)

# Get highest similarity score
top_similarity = similar_tickets[0]["similarity_score"]  # 0.85

similarity_component = 0.35 × 0.85 = 0.2975
```

**Cosine Similarity Formula**:
```
similarity = (A · B) / (||A|| × ||B||)

Where:
A = new ticket embedding [0.234, -0.567, 0.891, ...]
B = stored ticket embedding [0.245, -0.543, 0.876, ...]
```

**Range**: 0.0 (completely different) to 1.0 (identical)

**Why 35%?**: Historical data is valuable but secondary to model prediction.

---

### Component 3: Keyword Boost (15% weight)

**Source**: Domain-specific keyword matching

**Calculation**:
```python
# Domain keywords for "Authentication" category
auth_keywords = ["password", "login", "reset", "forgot", "access", 
                 "credentials", "authentication", "sign in"]

# Count matches in ticket text
ticket_text = "I forgot my password and need to reset it"
matches = count_keywords(ticket_text, auth_keywords)  # 3 matches

# Normalize (max 5 keywords = 1.0)
keyword_boost = min(matches / 5.0, 1.0) = min(3/5, 1.0) = 0.60

keyword_component = 0.15 × 0.60 = 0.09
```

**Why 15%?**: Provides additional signal but shouldn't override model.

---

### Final Confidence Calculation

**Step 1: Sum Components**
```python
confidence = model_component + similarity_component + keyword_component
           = 0.46 + 0.2975 + 0.09
           = 0.8475
```

**Step 2: Sentiment Adjustment**
```python
# If user is frustrated (negative sentiment > threshold)
if sentiment == "NEGATIVE" and sentiment_score > 0.70:
    confidence -= 0.08  # Reduce confidence
    
# Example:
confidence = 0.8475 - 0.08 = 0.7675
```

**Step 3: Clamp to [0, 1]**
```python
confidence = max(0.0, min(1.0, confidence))
# Ensures confidence stays between 0% and 100%
```

---

### Confidence Breakdown Example

```python
{
  "confidence_score": 0.8475,
  "confidence_breakdown": {
    "model_prob_component": 0.4600,  # 50% × 0.92
    "similarity_component": 0.2975,  # 35% × 0.85
    "keyword_component": 0.0900      # 15% × 0.60
  },
  "sentiment_adjusted": false,
  "routing_decision": "AUTO_RESOLVE"  # >= 0.85 threshold
}
```

---

### Routing Decision Logic

```python
if category == "Security":
    routing = "ESCALATE_TO_HUMAN"  # Security override
elif sla_breach_probability > 0.75:
    routing = "ESCALATE_TO_HUMAN"  # SLA override
elif confidence >= 0.85:
    routing = "AUTO_RESOLVE"       # High confidence
elif confidence >= 0.60:
    routing = "SUGGEST_TO_AGENT"   # Medium confidence
else:
    routing = "ESCALATE_TO_HUMAN"  # Low confidence
```

**Thresholds**:
- **≥ 0.85 (85%)**: AUTO_RESOLVE - Send response directly to user
- **0.60-0.85 (60-85%)**: SUGGEST_TO_AGENT - Requires human approval
- **< 0.60 (60%)**: ESCALATE_TO_HUMAN - Manual handling needed

---

## ⏰ SLA Calculation

### SLA Limits by Category & Priority

**SLA Matrix** (in minutes):

| Category | Low | Medium | High | Critical |
|----------|-----|--------|------|----------|
| Network | 2880 (48h) | 480 (8h) | 120 (2h) | 30 (30m) |
| Auth | 1440 (24h) | 240 (4h) | 60 (1h) | 15 (15m) |
| Software | 4320 (72h) | 1440 (24h) | 240 (4h) | 60 (1h) |
| Hardware | 4320 (72h) | 1440 (24h) | 240 (4h) | 120 (2h) |
| Security | 30 (30m) | 30 (30m) | 30 (30m) | 5 (5m) |
| Database | 1440 (24h) | 240 (4h) | 60 (1h) | 5 (5m) |
| Email | 2880 (48h) | 480 (8h) | 120 (2h) | 60 (1h) |
| Access | 2880 (48h) | 480 (8h) | 120 (2h) | 30 (30m) |

**Code Implementation**:
```python
SLA_MINUTES = {
    "Network": {"Low": 2880, "Medium": 480, "High": 120, "Critical": 30},
    "Auth": {"Low": 1440, "Medium": 240, "High": 60, "Critical": 15},
    # ... more categories
}

def get_sla_minutes(category: str, priority: str) -> int:
    return SLA_MINUTES[category][priority]
```

---

### SLA Deadline Calculation

**Formula**:
```
SLA_Deadline = Submission_Time + SLA_Minutes
```

**Example**:
```python
# Ticket submitted
submission_time = datetime(2026, 3, 21, 10, 0, 0)  # 10:00 AM

# Category: Authentication, Priority: Medium
sla_minutes = 240  # 4 hours

# Calculate deadline
sla_deadline = submission_time + timedelta(minutes=240)
# Result: 2026-03-21 14:00:00 (2:00 PM)
```

**Code Implementation**:
```python
from datetime import datetime, timedelta

def get_sla_deadline(category, priority, submitted_at):
    sla_minutes = get_sla_minutes(category, priority)
    return submitted_at + timedelta(minutes=sla_minutes)

# Example
deadline = get_sla_deadline("Auth", "Medium", datetime.now())
```

---

### SLA Time Remaining

**Formula**:
```
Minutes_Remaining = (SLA_Deadline - Current_Time) / 60
```

**Example**:
```python
# Current time
now = datetime(2026, 3, 21, 12, 30, 0)  # 12:30 PM

# SLA deadline
deadline = datetime(2026, 3, 21, 14, 0, 0)  # 2:00 PM

# Calculate remaining time
delta = deadline - now  # timedelta(hours=1, minutes=30)
minutes_remaining = delta.total_seconds() / 60
# Result: 90 minutes
```

**Urgency Levels**:
```python
if minutes_remaining < 0:
    urgency = "critical"  # BREACHED!
elif minutes_remaining < sla_minutes * 0.20:  # < 20% time left
    urgency = "warning"   # At risk
else:
    urgency = "ok"        # On track
```

---

### SLA Breach Probability

**ML Model Features** (11 total):
1. Category (one-hot encoded, 10 dimensions)
2. Priority (ordinal: 0-3)
3. User tier (ordinal: 0-3)
4. Submission hour (0-23)
5. Submission day of week (0-6)
6. Word count
7. Urgency keyword count
8. Sentiment score (0.0-1.0)
9. Current queue length
10. Similar ticket avg resolution hours
11. Is weekend (binary)
12. Is outside business hours (binary)

**Model**: Random Forest Classifier (200 trees)

**Output**: Probability of SLA breach (0.0-1.0)

**Example**:
```python
ticket_features = {
    "category": "Network",
    "priority": "High",
    "user_tier": "Standard",
    "submission_hour": 17,  # 5 PM
    "submission_day_of_week": 4,  # Friday
    "word_count": 45,
    "urgency_keyword_count": 2,
    "sentiment_score": 0.65,  # Slightly negative
    "current_queue_length": 12,  # Busy queue
    "similar_ticket_avg_resolution_hours": 3.5,
    "is_weekend": False,
    "is_outside_business_hours": True  # After 5 PM
}

breach_probability = sla_model.predict(ticket_features)
# Result: 0.72 (72% chance of breach)
```

**Interpretation**:
- **< 0.25**: Low risk (likely to meet SLA)
- **0.25-0.50**: Moderate risk
- **0.50-0.75**: High risk (needs attention)
- **> 0.75**: Critical risk (escalate immediately)

---

## 📈 Performance Metrics

### Confusion Matrix

**Definition**: Table showing actual vs predicted classifications

**Example** (3-class simplified):

```
                Predicted
              Auth  Network  Software
Actual Auth     45      3        2      (50 total)
      Network    2     38        5      (45 total)
      Software   1      4       40      (45 total)
```

**Interpretation**:
- **Diagonal** (45, 38, 40): Correct predictions
- **Off-diagonal**: Misclassifications
- Auth confused with Network: 3 times
- Network confused with Software: 5 times

**Accuracy from Confusion Matrix**:
```
Accuracy = (45 + 38 + 40) / (50 + 45 + 45)
         = 123 / 140
         = 0.879 = 87.9%
```

**Normalized Confusion Matrix** (by row):
```
                Predicted
              Auth  Network  Software
Actual Auth    0.90    0.06      0.04
      Network  0.04    0.84      0.11
      Software 0.02    0.09      0.89
```

**Code Implementation**:
```python
from sklearn.metrics import confusion_matrix

y_true = ["Auth", "Network", "Software", "Auth", "Network"]
y_pred = ["Auth", "Network", "Hardware", "Auth", "Network"]

cm = confusion_matrix(y_true, y_pred, labels=["Auth", "Network", "Software", "Hardware"])
```

---

### Expected Calibration Error (ECE)

**Definition**: Measures how well predicted probabilities match actual accuracy

**Formula**:
```
ECE = Σ (n_bin / n_total) × |accuracy_bin - confidence_bin|
```

**Example**:

| Confidence Bin | Avg Confidence | Actual Accuracy | Count | Contribution |
|----------------|----------------|-----------------|-------|--------------|
| 0.0-0.1 | 0.05 | 0.10 | 5 | 0.05 × |0.10-0.05| = 0.0025 |
| 0.1-0.2 | 0.15 | 0.20 | 8 | 0.08 × |0.20-0.15| = 0.0040 |
| ... | ... | ... | ... | ... |
| 0.8-0.9 | 0.85 | 0.87 | 45 | 0.45 × |0.87-0.85| = 0.0090 |
| 0.9-1.0 | 0.95 | 0.96 | 30 | 0.30 × |0.96-0.95| = 0.0030 |

```
ECE = 0.0025 + 0.0040 + ... + 0.0090 + 0.0030 = 0.0425 = 4.25%
```

**Interpretation**:
- **ECE < 0.05 (5%)**: Well-calibrated (confidence matches accuracy)
- **ECE 0.05-0.10**: Moderately calibrated
- **ECE > 0.10**: Poorly calibrated (confidence unreliable)

**Perfect Calibration**: When model says 90% confident, it's correct 90% of the time.

---

### AUC-ROC (Area Under ROC Curve)

**Used for**: Binary classification (SLA breach prediction)

**Definition**: Probability that model ranks a random positive example higher than a random negative example

**Range**: 0.0 to 1.0
- **1.0**: Perfect classifier
- **0.9-1.0**: Excellent
- **0.8-0.9**: Good
- **0.7-0.8**: Fair
- **0.5**: Random guessing
- **< 0.5**: Worse than random

**Example**:
```python
# SLA breach prediction
y_true = [0, 0, 1, 1, 0, 1, 0, 1]  # 0=no breach, 1=breach
y_scores = [0.1, 0.3, 0.7, 0.9, 0.2, 0.8, 0.4, 0.95]

from sklearn.metrics import roc_auc_score
auc = roc_auc_score(y_true, y_scores)
# Result: 0.92 (Excellent!)
```

---

## 🎯 Real-World Examples

### Example 1: High Confidence Auto-Resolve

**Ticket**: "I forgot my password and need to reset it"

**Step 1: Model Prediction**
```python
model_probabilities = {
    "Auth": 0.92,
    "Network": 0.03,
    "Software": 0.02,
    "Hardware": 0.01,
    # ... other categories
}
model_confidence = 0.92
model_component = 0.50 × 0.92 = 0.46
```

**Step 2: Similarity Search**
```python
similar_tickets = [
    {"ticket_id": "TKT-A3F8", "similarity": 0.89},
    {"ticket_id": "TKT-B7K2", "similarity": 0.85},
    {"ticket_id": "TKT-C9M1", "similarity": 0.78}
]
top_similarity = 0.89
similarity_component = 0.35 × 0.89 = 0.3115
```

**Step 3: Keyword Matching**
```python
auth_keywords = ["password", "login", "reset", "forgot", "access"]
matches = 3  # "forgot", "password", "reset"
keyword_boost = min(3/5, 1.0) = 0.60
keyword_component = 0.15 × 0.60 = 0.09
```

**Step 4: Final Confidence**
```python
confidence = 0.46 + 0.3115 + 0.09 = 0.8615 = 86.15%
```

**Step 5: Routing Decision**
```python
if confidence >= 0.85:
    routing = "AUTO_RESOLVE"
```

**Result**: ✅ AUTO_RESOLVE - Response sent directly to user

---

### Example 2: Medium Confidence Agent Review

**Ticket**: "VPN connection keeps timing out with error 800"

**Step 1: Model Prediction**
```python
model_probabilities = {
    "Network": 0.78,
    "Software": 0.12,
    "Hardware": 0.05,
    # ... other categories
}
model_confidence = 0.78
model_component = 0.50 × 0.78 = 0.39
```

**Step 2: Similarity Search**
```python
similar_tickets = [
    {"ticket_id": "TKT-N5K9", "similarity": 0.72},
    {"ticket_id": "TKT-N8L3", "similarity": 0.68},
    {"ticket_id": "TKT-N2M7", "similarity": 0.65}
]
top_similarity = 0.72
similarity_component = 0.35 × 0.72 = 0.252
```

**Step 3: Keyword Matching**
```python
network_keywords = ["vpn", "connection", "network", "timeout", "error"]
matches = 4  # "vpn", "connection", "timeout", "error"
keyword_boost = min(4/5, 1.0) = 0.80
keyword_component = 0.15 × 0.80 = 0.12
```

**Step 4: Final Confidence**
```python
confidence = 0.39 + 0.252 + 0.12 = 0.762 = 76.2%
```

**Step 5: Routing Decision**
```python
if 0.60 <= confidence < 0.85:
    routing = "SUGGEST_TO_AGENT"
```

**Result**: 🔍 SUGGEST_TO_AGENT - Requires human approval

---

### Example 3: Low Confidence Escalation

**Ticket**: "Database access denied - production deployment blocked"

**Step 1: Security Override**
```python
if category == "Database":
    # Database tickets always escalate (business rule)
    routing = "ESCALATE_TO_HUMAN"
    confidence = 0.0  # Override confidence
```

**Result**: ⚠️ ESCALATE_TO_HUMAN - Manual handling required

---

### Example 4: SLA Breach Risk

**Ticket Details**:
```python
category = "Network"
priority = "High"
submission_time = datetime(2026, 3, 21, 17, 30, 0)  # 5:30 PM Friday
sla_minutes = 120  # 2 hours
```

**SLA Calculation**:
```python
deadline = submission_time + timedelta(minutes=120)
# Result: 2026-03-21 19:30:00 (7:30 PM)
```

**Breach Probability**:
```python
features = {
    "category": "Network",
    "priority": "High",
    "submission_hour": 17,  # After hours
    "submission_day": 4,  # Friday
    "queue_length": 15,  # Busy
    "is_outside_business_hours": True
}

breach_prob = sla_model.predict(features)
# Result: 0.78 (78% chance of breach)
```

**Override Decision**:
```python
if breach_prob > 0.75:
    routing = "ESCALATE_TO_HUMAN"  # SLA override
```

**Result**: ⚠️ ESCALATE_TO_HUMAN - High breach risk

---

## 📊 Summary Table

| Metric | Formula | Range | Good Value | Purpose |
|--------|---------|-------|------------|---------|
| Accuracy | (TP+TN)/(TP+TN+FP+FN) | 0-1 | >0.85 | Overall correctness |
| Precision | TP/(TP+FP) | 0-1 | >0.85 | Positive prediction quality |
| Recall | TP/(TP+FN) | 0-1 | >0.85 | Coverage of positives |
| F1-Score | 2×(P×R)/(P+R) | 0-1 | >0.85 | Balanced metric |
| Confidence | 0.5×M + 0.35×S + 0.15×K | 0-1 | >0.85 | Routing decision |
| ECE | Σ(n/N)×\|acc-conf\| | 0-1 | <0.05 | Calibration quality |
| AUC-ROC | Area under curve | 0-1 | >0.90 | Binary classifier quality |
| SLA Minutes | Lookup table | varies | N/A | Deadline calculation |
| Breach Prob | ML model output | 0-1 | <0.25 | SLA risk assessment |

---

**Key Takeaways**:
1. **Accuracy** measures overall correctness (87% for category classifier)
2. **Confidence** is a weighted combination of model, similarity, and keywords
3. **SLA** is calculated from category + priority lookup table
4. **Routing** decisions use confidence thresholds (85%, 60%) with overrides
5. **Calibration** ensures confidence scores are reliable (ECE < 5%)