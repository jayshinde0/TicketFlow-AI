# 📊 Metrics Quick Reference Card

## 🎯 Confidence Score Formula

```
┌─────────────────────────────────────────────────────────────┐
│         CONFIDENCE SCORE CALCULATION                        │
└─────────────────────────────────────────────────────────────┘

Confidence = (50% × Model) + (35% × Similarity) + (15% × Keywords)

┌──────────────────┐
│ Model Prob (50%) │ ← Logistic Regression softmax output
│    0.92          │    Example: 92% confident it's "Auth"
│    × 0.50        │
│    = 0.46        │
└──────────────────┘
         +
┌──────────────────┐
│ Similarity (35%) │ ← ChromaDB cosine similarity
│    0.85          │    Example: 85% similar to past ticket
│    × 0.35        │
│    = 0.2975      │
└──────────────────┘
         +
┌──────────────────┐
│ Keywords (15%)   │ ← Domain keyword matching
│    0.60          │    Example: 3 out of 5 keywords matched
│    × 0.15        │
│    = 0.09        │
└──────────────────┘
         =
┌──────────────────┐
│ Final: 0.8475    │ = 84.75% confidence
└──────────────────┘

Adjustments:
- Frustrated user (negative sentiment): -0.08
- Clamp to [0.0, 1.0]
```

---

## 🚦 Routing Decision Tree

```
┌─────────────────────────────────────────────────────────────┐
│                  ROUTING LOGIC                              │
└─────────────────────────────────────────────────────────────┘

                    New Ticket
                        ↓
            ┌───────────┴───────────┐
            │                       │
      Category = Security?    Category = Database?
            │                       │
           YES                     YES
            │                       │
            ↓                       ↓
    ┌──────────────────┐    ┌──────────────────┐
    │ ESCALATE_TO_HUMAN│    │ ESCALATE_TO_HUMAN│
    │ (Security Rule)  │    │ (Database Rule)  │
    └──────────────────┘    └──────────────────┘
            │
           NO
            ↓
    SLA Breach Prob > 75%?
            │
           YES → ESCALATE_TO_HUMAN (SLA Override)
            │
           NO
            ↓
    Calculate Confidence Score
            ↓
    ┌───────────────────────────────────┐
    │ Confidence >= 0.85 (85%)?         │
    │         YES → AUTO_RESOLVE        │
    │                                   │
    │ Confidence >= 0.60 (60%)?         │
    │         YES → SUGGEST_TO_AGENT    │
    │                                   │
    │ Confidence < 0.60?                │
    │         YES → ESCALATE_TO_HUMAN   │
    └───────────────────────────────────┘
```

---

## ⏰ SLA Calculation

```
┌─────────────────────────────────────────────────────────────┐
│                  SLA DEADLINE                               │
└─────────────────────────────────────────────────────────────┘

SLA_Deadline = Submission_Time + SLA_Minutes

Example:
Submitted: 2026-03-21 10:00:00
Category: Authentication
Priority: Medium
SLA: 240 minutes (4 hours)

Deadline = 10:00:00 + 4 hours = 14:00:00 (2:00 PM)

┌─────────────────────────────────────────────────────────────┐
│                  TIME REMAINING                             │
└─────────────────────────────────────────────────────────────┘

Minutes_Remaining = (Deadline - Current_Time) / 60

Current: 12:30:00
Deadline: 14:00:00
Remaining = 90 minutes

Urgency Level:
├─ < 0 minutes: CRITICAL (Breached!)
├─ < 20% of SLA: WARNING (At risk)
└─ >= 20% of SLA: OK (On track)
```

---

## 📊 Accuracy Metrics

```
┌─────────────────────────────────────────────────────────────┐
│              CONFUSION MATRIX                               │
└─────────────────────────────────────────────────────────────┘

                    Predicted
                Auth  Network  Software
Actual  Auth     45      3        2       = 50
       Network    2     38        5       = 45
       Software   1      4       40       = 45

Accuracy = (45 + 38 + 40) / 140 = 87.9%

┌─────────────────────────────────────────────────────────────┐
│              PRECISION & RECALL                             │
└─────────────────────────────────────────────────────────────┘

For "Auth" category:
┌────────────────────────────────────┐
│ Precision = TP / (TP + FP)         │
│           = 45 / (45 + 3 + 1)      │
│           = 45 / 49 = 0.918 = 92%  │
│                                    │
│ Recall = TP / (TP + FN)            │
│        = 45 / (45 + 3 + 2)         │
│        = 45 / 50 = 0.90 = 90%      │
│                                    │
│ F1 = 2 × (P × R) / (P + R)         │
│    = 2 × (0.92 × 0.90) / 1.82      │
│    = 0.909 = 91%                   │
└────────────────────────────────────┘
```

---

## 🎲 Model Probabilities

```
┌─────────────────────────────────────────────────────────────┐
│           LOGISTIC REGRESSION OUTPUT                        │
└─────────────────────────────────────────────────────────────┘

Ticket: "I forgot my password"

Softmax Probabilities:
┌────────────────────────────────────┐
│ Authentication:  0.92 ████████████ │ ← Predicted
│ Network:         0.03 █            │
│ Software:        0.02 █            │
│ Hardware:        0.01 ▌            │
│ Access:          0.01 ▌            │
│ Email:           0.00 ▌            │
│ Security:        0.00 ▌            │
│ Database:        0.00 ▌            │
│ Billing:         0.00 ▌            │
│ ServiceRequest:  0.01 ▌            │
└────────────────────────────────────┘
                    Sum = 1.00

Confidence = max(probabilities) = 0.92
```

---

## 📈 Calibration Example

```
┌─────────────────────────────────────────────────────────────┐
│           CALIBRATION CURVE                                 │
└─────────────────────────────────────────────────────────────┘

Perfect Calibration: Predicted confidence = Actual accuracy

Confidence Bin  | Avg Conf | Actual Acc | Gap
----------------|----------|------------|------
0.0 - 0.1       |   0.05   |    0.10    | 0.05
0.1 - 0.2       |   0.15   |    0.18    | 0.03
0.2 - 0.3       |   0.25   |    0.27    | 0.02
0.3 - 0.4       |   0.35   |    0.38    | 0.03
0.4 - 0.5       |   0.45   |    0.47    | 0.02
0.5 - 0.6       |   0.55   |    0.58    | 0.03
0.6 - 0.7       |   0.65   |    0.67    | 0.02
0.7 - 0.8       |   0.75   |    0.77    | 0.02
0.8 - 0.9       |   0.85   |    0.87    | 0.02
0.9 - 1.0       |   0.95   |    0.96    | 0.01

ECE = Average Gap = 0.025 = 2.5% ✅ Well-calibrated!
```

---

## 🎯 SLA Breach Prediction

```
┌─────────────────────────────────────────────────────────────┐
│           RANDOM FOREST FEATURES                            │
└─────────────────────────────────────────────────────────────┘

Input Features (11 total):
1. Category (one-hot, 10 dims)    ← Network, Auth, etc.
2. Priority (0-3)                 ← Low=0, Critical=3
3. User Tier (0-3)                ← Free=0, Enterprise=3
4. Submission Hour (0-23)         ← 17 = 5 PM
5. Day of Week (0-6)              ← 4 = Friday
6. Word Count                     ← 45 words
7. Urgency Keywords               ← 2 keywords
8. Sentiment Score (0-1)          ← 0.65 (negative)
9. Queue Length                   ← 12 tickets
10. Avg Resolution Hours          ← 3.5 hours
11. Is Weekend (0/1)              ← 0 = No
12. Outside Hours (0/1)           ← 1 = Yes

         ↓
┌─────────────────────┐
│ Random Forest       │
│ (200 trees)         │
└─────────────────────┘
         ↓
Breach Probability: 0.72 (72%)

Interpretation:
├─ < 0.25: Low risk
├─ 0.25-0.50: Moderate risk
├─ 0.50-0.75: High risk
└─ > 0.75: Critical risk → ESCALATE!
```

---

## 📊 Performance Summary

```
┌─────────────────────────────────────────────────────────────┐
│              MODEL PERFORMANCE                              │
└─────────────────────────────────────────────────────────────┘

Category Classifier (Logistic Regression):
├─ Accuracy: 87%
├─ Macro F1: 0.86
├─ Precision: 0.87
├─ Recall: 0.85
└─ ECE: 0.025 (2.5%)

Priority Classifier (Random Forest):
├─ Accuracy: 84%
├─ Macro F1: 0.83
├─ Precision: 0.85
└─ Recall: 0.82

SLA Predictor (Random Forest):
├─ AUC-ROC: 0.89
├─ Precision @ 0.70: 0.82
├─ Recall @ 0.70: 0.78
└─ F1 @ 0.70: 0.80

Response Generator (Mistral-Nemo):
├─ Model: 7B parameters
├─ Context: RAG with ChromaDB
├─ Avg Response Time: 2-3 seconds
└─ Quality: Human-evaluated
```

---

## 🔢 Key Thresholds

```
┌─────────────────────────────────────────────────────────────┐
│              SYSTEM THRESHOLDS                              │
└─────────────────────────────────────────────────────────────┘

Confidence Routing:
├─ AUTO_RESOLVE: >= 0.85 (85%)
├─ SUGGEST_TO_AGENT: 0.60 - 0.85 (60-85%)
└─ ESCALATE_TO_HUMAN: < 0.60 (60%)

SLA Breach Risk:
├─ Low: < 0.25 (25%)
├─ Moderate: 0.25 - 0.50
├─ High: 0.50 - 0.75
└─ Critical: > 0.75 (75%) → ESCALATE

Sentiment:
├─ Positive: > 0.10
├─ Neutral: -0.10 to 0.10
└─ Negative: < -0.10 → Confidence -0.08

Similarity:
├─ High: > 0.80 (80%)
├─ Medium: 0.60 - 0.80
└─ Low: < 0.60 (60%)

Model Retraining:
├─ Accuracy drops below: 0.80 (80%)
├─ Minimum feedback samples: 50
└─ Auto-trigger: Yes
```

---

## 📐 Formulas Cheat Sheet

```
┌─────────────────────────────────────────────────────────────┐
│              QUICK FORMULAS                                 │
└─────────────────────────────────────────────────────────────┘

Accuracy = (TP + TN) / (TP + TN + FP + FN)

Precision = TP / (TP + FP)

Recall = TP / (TP + FN)

F1-Score = 2 × (Precision × Recall) / (Precision + Recall)

Confidence = 0.5×Model + 0.35×Similarity + 0.15×Keywords

SLA_Deadline = Submission_Time + SLA_Minutes

Minutes_Remaining = (Deadline - Now) / 60

Cosine_Similarity = (A · B) / (||A|| × ||B||)

ECE = Σ (n_bin / n_total) × |accuracy_bin - confidence_bin|

Keyword_Boost = min(matches / 5.0, 1.0)
```

---

**Quick Reference**: Keep this card handy for understanding system metrics and calculations! 🚀
