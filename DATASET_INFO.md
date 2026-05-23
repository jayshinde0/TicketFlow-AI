# Customer Support Tickets Dataset Information

## Dataset Overview

**File**: `backend/ml/data/customer_support_tickets.csv`

**Total Tickets**: **8,469**

## Dataset Structure

### Columns (17 total)
1. **Ticket ID** - Unique identifier (int64)
2. **Customer Name** - Customer's full name (object)
3. **Customer Email** - Customer's email address (object)
4. **Customer Age** - Customer's age (int64)
5. **Customer Gender** - Customer's gender (object)
6. **Product Purchased** - Product name (object)
7. **Date of Purchase** - Purchase date (object)
8. **Ticket Type** - Category of the ticket (object)
9. **Ticket Subject** - Brief subject line (object)
10. **Ticket Description** - Detailed description (object)
11. **Ticket Status** - Current status (object)
12. **Resolution** - Resolution details (object) - 2,769 non-null (32.7%)
13. **Ticket Priority** - Priority level (object)
14. **Ticket Channel** - Communication channel (object)
15. **First Response Time** - Time to first response (object) - 5,650 non-null (66.7%)
16. **Time to Resolution** - Time taken to resolve (object) - 2,769 non-null (32.7%)
17. **Customer Satisfaction Rating** - Rating (float64) - 2,769 non-null (32.7%)

## Ticket Type Distribution

| Ticket Type | Count | Percentage |
|-------------|-------|------------|
| Refund request | 1,752 | 20.7% |
| Technical issue | 1,747 | 20.6% |
| Cancellation request | 1,695 | 20.0% |
| Product inquiry | 1,641 | 19.4% |
| Billing inquiry | 1,634 | 19.3% |

**Total**: 8,469 tickets (evenly distributed across 5 categories)

## Ticket Priority Distribution

| Priority | Count | Percentage |
|----------|-------|------------|
| Medium | 2,192 | 25.9% |
| Critical | 2,129 | 25.1% |
| High | 2,085 | 24.6% |
| Low | 2,063 | 24.4% |

**Total**: 8,469 tickets (evenly distributed across 4 priority levels)

## Ticket Status Distribution

| Status | Count | Percentage |
|--------|-------|------------|
| Pending Customer Response | 2,881 | 34.0% |
| Open | 2,819 | 33.3% |
| Closed | 2,769 | 32.7% |

**Total**: 8,469 tickets (evenly distributed across 3 statuses)

## Data Completeness

### Fully Populated Fields (100%)
- Ticket ID
- Customer Name
- Customer Email
- Customer Age
- Customer Gender
- Product Purchased
- Date of Purchase
- Ticket Type
- Ticket Subject
- Ticket Description
- Ticket Status
- Ticket Priority
- Ticket Channel

### Partially Populated Fields
- **First Response Time**: 5,650 / 8,469 (66.7%)
- **Resolution**: 2,769 / 8,469 (32.7%)
- **Time to Resolution**: 2,769 / 8,469 (32.7%)
- **Customer Satisfaction Rating**: 2,769 / 8,469 (32.7%)

*Note: The 32.7% completion rate for resolution-related fields corresponds exactly to the 2,769 "Closed" tickets, indicating that only closed tickets have resolution data.*

## Dataset Size

- **Memory Usage**: ~1.1 MB
- **Rows**: 8,469
- **Columns**: 17

## Mapping to TicketFlow AI Categories

The dataset's "Ticket Type" field maps to our system's categories as follows:

| Dataset Ticket Type | TicketFlow AI Category | Count |
|---------------------|------------------------|-------|
| Technical issue | SOFTWARE | 1,747 |
| Refund request | BILLING | 1,752 |
| Billing inquiry | BILLING | 1,634 |
| Cancellation request | BILLING | 1,695 |
| Product inquiry | GENERAL | 1,641 |

### Our System Categories
- **NETWORK** - Network connectivity, VPN, firewall issues
- **SOFTWARE** - Application bugs, crashes, performance issues
- **DATABASE** - Database errors, query issues, data corruption
- **SECURITY** - Security threats, vulnerabilities, access issues
- **BILLING** - Payment, refunds, invoices, subscriptions
- **HR_FACILITIES** - HR issues, hardware requests, facilities

## Training Data Usage

### ML Model Training
The dataset is used to train three ML models:

1. **Category Classifier** (`backend/ml/models/category_classifier.py`)
   - Predicts ticket category from description
   - Trained on 8,469 tickets

2. **Priority Classifier** (`backend/ml/models/priority_classifier.py`)
   - Predicts ticket priority (Low, Medium, High, Critical)
   - Trained on 8,469 tickets

3. **SLA Predictor** (`backend/ml/models/sla_predictor.py`)
   - Predicts SLA breach probability
   - Trained on 8,469 tickets

### Model Artifacts
Trained models are saved in: `backend/ml/artifacts/`
- `category_model.pkl`
- `priority_model.pkl`
- `sla_model.pkl`
- `tfidf_vectorizer.pkl`

## Sample Ticket

```
Ticket ID: 1
Customer: Marisa Obrien
Email: marisa.obrien@example.com
Type: Technical issue
Subject: Application crashes on startup
Description: The application crashes immediately when I try to open it...
Status: Open
Priority: High
```

## Dataset Quality

### Strengths
✅ Large dataset (8,469 tickets)
✅ Evenly distributed across categories
✅ Evenly distributed across priorities
✅ Complete customer information
✅ Detailed descriptions
✅ Real-world ticket scenarios

### Limitations
⚠️ Only 32.7% of tickets have resolution data
⚠️ Limited to 5 ticket types
⚠️ No timestamp data for ticket creation
⚠️ No agent assignment information
⚠️ No ticket journey/phase tracking

## Usage in TicketFlow AI

### Training Phase
1. Load dataset from CSV
2. Preprocess text (clean, tokenize, vectorize)
3. Train ML models
4. Save model artifacts
5. Evaluate model performance

### Inference Phase
1. User submits new ticket
2. Extract features from description
3. Use trained models to predict:
   - Category
   - Priority
   - SLA breach probability
4. Route ticket based on predictions

### Demo Data Generation
The dataset is also used to generate demo tickets for testing:
- `backend/generate_demo_tickets.py`
- `backend/generate_enhanced_tickets.py`

## Statistics

- **Average tickets per category**: ~1,694
- **Average tickets per priority**: ~2,117
- **Average tickets per status**: ~2,823
- **Closed ticket rate**: 32.7%
- **Open ticket rate**: 33.3%
- **Pending rate**: 34.0%

## Conclusion

The dataset provides a solid foundation for training ML models with:
- **8,469 diverse tickets**
- **5 ticket types** covering common support scenarios
- **4 priority levels** for urgency classification
- **Even distribution** across categories and priorities
- **Complete customer data** for all tickets

This dataset enables TicketFlow AI to accurately classify and route support tickets using machine learning.

---

**Last Updated**: April 17, 2026
**Dataset Version**: 1.0
**Source**: `backend/ml/data/customer_support_tickets.csv`
