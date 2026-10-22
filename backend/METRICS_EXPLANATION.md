# Performance Metrics - Simple Explanation

## 🎯 **The Big Picture**

```
Training Data (70%)        Test Data (15%)
     ↓                          ↓
  Train Model            Make Predictions
     ↓                          ↓
  Learned Patterns        Compare with Truth
                               ↓
                         Calculate Metrics
```

---

## 📊 **Example with Real Numbers**

### **Your Test Data: 2000 Tickets**

#### Confusion Matrix:
```
                    PREDICTED
                Billing    ServiceRequest
ACTUAL  
Billing          1153          203         ← 1356 total Billing
ServiceReq        164          480         ← 644 total ServiceRequest
                 ────          ────
                 1317          683
```

---

## 🔢 **Metric Calculations**

### **1. ACCURACY** (Simplest)
```
Correct predictions = 1153 + 480 = 1633
Total predictions = 2000

Accuracy = 1633 ÷ 2000 = 0.8165 = 81.65%
```

**Meaning:** Out of 100 tickets, 82 are classified correctly.

---

### **2. PRECISION** (How precise are we?)

#### For Billing:
```
Model predicted "Billing": 1317 times
Actually Billing: 1153 times
Actually NOT Billing: 164 times (mistakes)

Precision = 1153 ÷ 1317 = 0.875 = 87.5%
```

**Meaning:** When model says "Billing", it's correct 87.5% of the time.

#### For ServiceRequest:
```
Model predicted "ServiceRequest": 683 times
Actually ServiceRequest: 480 times
Actually NOT ServiceRequest: 203 times (mistakes)

Precision = 480 ÷ 683 = 0.703 = 70.3%
```

**Average Precision = (87.5% + 70.3%) ÷ 2 = 78.9%**

---

### **3. RECALL** (Did we catch them all?)

#### For Billing:
```
Total Billing tickets: 1356
Correctly caught: 1153
Missed (labeled as ServiceRequest): 203

Recall = 1153 ÷ 1356 = 0.850 = 85.0%
```

**Meaning:** We catch 85% of all Billing tickets.

#### For ServiceRequest:
```
Total ServiceRequest tickets: 644
Correctly caught: 480
Missed (labeled as Billing): 164

Recall = 480 ÷ 644 = 0.745 = 74.5%
```

**Average Recall = (85.0% + 74.5%) ÷ 2 = 79.8%**

---

### **4. F1-SCORE** (Balance of Precision & Recall)

#### For Billing:
```
Precision = 0.875
Recall = 0.850

F1 = 2 × (Precision × Recall) ÷ (Precision + Recall)
F1 = 2 × (0.875 × 0.850) ÷ (0.875 + 0.850)
F1 = 2 × 0.74375 ÷ 1.725
F1 = 0.863 = 86.3%
```

#### For ServiceRequest:
```
Precision = 0.703
Recall = 0.745

F1 = 2 × (0.703 × 0.745) ÷ (0.703 + 0.745)
F1 = 0.723 = 72.3%
```

**Average F1 = (86.3% + 72.3%) ÷ 2 = 79.3%**

---

## 🎯 **Simple Analogy**

Imagine a teacher grading exams:

### **Accuracy**
- Out of 100 questions, how many did you answer correctly?
- Your score: 82/100 = 82%

### **Precision**
- When you said "TRUE", how often was it actually true?
- You said TRUE 50 times, but 10 were wrong
- Precision = 40/50 = 80%

### **Recall**
- Of all actual TRUE answers, how many did you find?
- There were 50 TRUE answers, you found 40
- Recall = 40/50 = 80%

### **F1-Score**
- Balance between being careful (Precision) and thorough (Recall)
- F1 = average of both ≈ 80%

---

## 📈 **Why We Need All These Metrics**

### **Example: Why Accuracy Isn't Enough**

**Scenario:** 95 Billing tickets, 5 ServiceRequest tickets

**Bad Model:** Always predicts "Billing"
```
Accuracy = 95/100 = 95% ✅ (looks good!)

But:
Precision for ServiceRequest = 0/0 = undefined
Recall for ServiceRequest = 0/5 = 0% ❌ (never catches them!)

F1 for ServiceRequest = 0% ❌ (reveals the problem!)
```

**This is why we use F1-Score!**

---

## 🔍 **Real Example from Your Project**

### **Before Improvement:**
```
External Test Data: 2000 tickets

Correct Predictions: 1433
Accuracy = 1433 / 2000 = 71.65%
F1-Score = 63.94%

Problem: Model struggles with ServiceRequest (47.3% F1)
```

### **After Improvement (Mixed Training):**
```
External Test Data: 2000 tickets

Correct Predictions: 1633
Accuracy = 1633 / 2000 = 81.65% ✅ (+10%)
F1-Score = 79.31% ✅ (+15%)

ServiceRequest improved: 47.3% → 72.3% F1 ✅ (+25%)
```

---

## 💻 **How It's Implemented**

### **Step 1: Split Data**
```python
# Split into train/test
train_df, val_df, test_df = train_val_test_split(df)
# Test = 15% = 644 tickets (never seen during training)
```

### **Step 2: Train Model**
```python
# Train on training data only
model.fit(X_train, y_train)
```

### **Step 3: Predict on Test Data**
```python
# Make predictions on unseen test data
y_pred = model.predict(X_test)
# y_test = actual labels (ground truth)
```

### **Step 4: Calculate Metrics**
```python
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Calculate all metrics
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred, average='macro')
recall = recall_score(y_test, y_pred, average='macro')
f1 = f1_score(y_test, y_pred, average='macro')

print(f"Accuracy: {accuracy:.2%}")   # 81.65%
print(f"Precision: {precision:.2%}") # 78.9%
print(f"Recall: {recall:.2%}")       # 79.8%
print(f"F1-Score: {f1:.2%}")         # 79.3%
```

---

## 📊 **Visual Summary**

```
TEST DATA (2000 tickets)
    ↓
MODEL PREDICTS
    ↓
COMPARE WITH ACTUAL
    ↓
┌─────────────────────────────────┐
│  CONFUSION MATRIX               │
│                                 │
│         Predicted               │
│      Bill    Service            │
│ Bill  1153     203   ← 1356     │
│ Serv   164     480   ← 644      │
│       ────    ────              │
│       1317     683              │
└─────────────────────────────────┘
    ↓
CALCULATE METRICS
    ↓
┌─────────────────────────────────┐
│ Accuracy:  81.65%               │
│ Precision: 78.9%                │
│ Recall:    79.8%                │
│ F1-Score:  79.3%                │
└─────────────────────────────────┘
```

---

## ✅ **Key Formulas**

| Metric | Formula | Your Result |
|--------|---------|-------------|
| **Accuracy** | Correct / Total | 1633/2000 = **81.65%** |
| **Precision** | TP / (TP + FP) | **78.9%** (avg) |
| **Recall** | TP / (TP + FN) | **79.8%** (avg) |
| **F1-Score** | 2×(P×R)/(P+R) | **79.3%** (avg) |

**Legend:**
- TP = True Positives (correct predictions)
- FP = False Positives (wrong positive predictions)
- FN = False Negatives (missed positives)

---

## 🎓 **For Your Presentation**

### **Slide: Evaluation Methodology**

**Text:**
> "We evaluated our model using standard ML metrics on 2,000 held-out test tickets:
> 
> - **Accuracy (81.65%)**: Overall correctness
> - **Precision (78.9%)**: Prediction reliability  
> - **Recall (79.8%)**: Coverage of all cases
> - **F1-Score (79.3%)**: Balanced performance metric
> 
> These metrics are industry-standard and calculated using scikit-learn library."

**Visual:** Show confusion matrix diagram

---

## 📚 **Further Reading**

- **Confusion Matrix**: Visual representation of predictions
- **Macro vs Weighted Average**: How to handle class imbalance
- **ROC Curve**: Trade-off between true/false positive rates
- **Cross-Validation**: k-fold validation for robust estimates

---

## ❓ **Common Questions**

**Q: Why not just use accuracy?**
A: Accuracy can be misleading with imbalanced data. F1-Score is more reliable.

**Q: What's a good F1-Score?**
A: Industry standard for ticket classification: 75-85%. You achieved 79.3% ✅

**Q: Why "macro" average?**
A: Treats all categories equally, regardless of size. Fair to minority classes.

**Q: How do you ensure fair testing?**
A: Test data is completely separate from training data. Never seen during training.

---

**Now you understand exactly how your 81.65% accuracy was calculated!** ✅
