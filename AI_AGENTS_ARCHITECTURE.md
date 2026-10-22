# AI Agents Architecture - TicketFlow AI

## 🤖 Multi-Agent System Overview

TicketFlow AI uses a **sophisticated multi-agent architecture** where 10 specialized AI agents work together in a coordinated pipeline to intelligently process support tickets. Each agent has a specific responsibility and passes its output to the next agent in sequence.

---

## 📊 Agent Execution Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    TICKET SUBMISSION                             │
│              (User submits: Subject + Description)               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  WAVE 0: INPUT VALIDATION                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 🛡️ Text Validation Agent                                 │   │
│  │ • Detects gibberish and invalid input                    │   │
│  │ • Rejects if not meaningful                              │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  WAVE 1: PREPROCESSING (Parallel Execution)                      │
│  ┌───────────────────────────┐  ┌──────────────────────────┐    │
│  │ 1️⃣ NLP Agent              │  │ 2️⃣ Sentiment Agent       │    │
│  │ • Text cleaning           │  │ • Emotion detection      │    │
│  │ • Tokenization            │  │ • Frustration analysis   │    │
│  │ • Lemmatization           │  │ • Sentiment scoring      │    │
│  └───────────────────────────┘  └──────────────────────────┘    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  WAVE 2: CLASSIFICATION (Sequential)                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 3️⃣ Classification Agent (Hybrid)                         │   │
│  │ • Category prediction (ML + Rules)                       │   │
│  │ • Priority assignment                                    │   │
│  │ • Confidence scoring                                     │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  WAVE 3: ENRICHMENT (Parallel Execution)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ 4️⃣ Retrieval │  │ 5️⃣ Security  │  │ 6️⃣ Explainability  │  │
│  │    Agent     │  │    Agent     │  │    Agent (LIME)     │  │
│  │ • RAG search │  │ • Threat     │  │ • Feature          │  │
│  │ • Similar    │  │   detection  │  │   importance       │  │
│  │   tickets    │  │ • Pattern    │  │ • Model           │  │
│  │ • ChromaDB   │  │   analysis   │  │   explanation     │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  WAVE 4: SLA & CONFIDENCE (Sequential)                           │
│  ┌───────────────────────────┐  ┌──────────────────────────┐    │
│  │ 7️⃣ SLA Prediction Agent   │  │ 8️⃣ Confidence Agent      │    │
│  │ • Breach probability      │  │ • Composite scoring     │    │
│  │ • Deadline calculation    │  │ • Multi-factor analysis │    │
│  │ • Time estimation         │  │ • HITL decision         │    │
│  └───────────────────────────┘  └──────────────────────────┘    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  WAVE 5: RESPONSE GENERATION (Sequential)                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 9️⃣ LLM Response Agent                                    │   │
│  │ • Context building (ticket + similar tickets)           │   │
│  │ • Ollama/Qwen LLM generation                            │   │
│  │ • Hallucination detection                               │   │
│  │ • Template fallback if needed                           │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  WAVE 6: SAFETY & ROUTING (Sequential)                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 🔟 Safety Guardrails Agent                               │   │
│  │ • Content moderation                                     │   │
│  │ • PII detection                                          │   │
│  │ • Harmful content filtering                             │   │
│  │ • Response sanitization                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ROUTING DECISION                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ AUTO_RESOLVE │  │ SUGGEST_TO   │  │ ESCALATE_TO_HUMAN   │  │
│  │ (High conf)  │  │ _AGENT       │  │ (Low conf/Security) │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔍 Detailed Agent Descriptions

### 🛡️ Agent 0: Text Validation Agent
**File**: `backend/services/text_validation_service.py`  
**Type**: Pre-processor  
**Execution**: WAVE 0 (Before all other agents)

**Purpose**: Validate input quality and reject gibberish/invalid text

**Responsibilities**:
- Detect keyboard mashing (e.g., "asdfghjkl")
- Check minimum word count (at least 3 meaningful words)
- Validate text structure (consonant-vowel balance)
- Detect excessive digits or repetition
- Ensure recognizable English words (≥30%)
- Reject impossible character patterns

**Input**: 
- Raw ticket text (subject + description)

**Output**: 
- `(is_valid: bool, error_message: str)`
- If invalid → HTTP 400 error returned to user
- If valid → Continue to Wave 1

**Connection to Next Agent**:
- If **valid** → Passes text to **NLP Agent (Wave 1)**
- If **invalid** → Pipeline stops, user receives error message

---

### 1️⃣ Agent 1: NLP Preprocessing Agent
**File**: `backend/services/nlp_service.py`  
**Type**: Text Processor  
**Execution**: WAVE 1 (Parallel with Sentiment Agent)

**Purpose**: Clean and normalize text for ML processing

**Responsibilities**:
1. **Basic Cleaning**:
   - Remove URLs, emails, IP addresses
   - Expand contractions (can't → cannot)
   - Fix repeated characters (soooo → so)
   - Remove special characters

2. **Tokenization & Lemmatization**:
   - Using spaCy (en_core_web_sm)
   - Convert to lowercase
   - Remove stopwords
   - Lemmatize words (running → run)
   - Filter short tokens (<2 chars)

3. **Feature Extraction**:
   - Word count
   - Character count
   - Urgency keyword count
   - Question/exclamation marks
   - Average word length
   - Sentence count

**Input**:
- Raw ticket text

**Output**:
```python
{
    "cleaned_text": "laptop connect vpn",  # Lemmatized
    "language": "en",
    "is_english": True,
    "features": {
        "word_count": 45,
        "urgency_keyword_count": 2,
        "question_mark_count": 1,
        ...
    },
    "original_cleaned": "laptop won't connect to vpn"  # URL-removed only
}
```

**Connection to Next Agent**:
- Cleaned text → **Classification Agent (Wave 2)**
- Features → Used by all downstream agents

**Cache**: Results cached to avoid re-processing same text

---

### 2️⃣ Agent 2: Sentiment Analysis Agent
**File**: `backend/services/sentiment_service.py`  
**Type**: Emotion Analyzer  
**Execution**: WAVE 1 (Parallel with NLP Agent)

**Purpose**: Detect user emotion and frustration level

**Responsibilities**:
- Analyze sentiment (POSITIVE/NEUTRAL/NEGATIVE)
- Calculate sentiment score (0.0 = negative, 1.0 = positive)
- Detect frustration indicators:
  - All caps words
  - Excessive punctuation (!!!, ???)
  - Negative urgency words
  - Complaint patterns

**Input**:
- Raw ticket text

**Output**:
```python
{
    "sentiment_label": "NEGATIVE",
    "sentiment_score": 0.23,  # 0.0-1.0
    "is_frustrated": True
}
```

**How It Works**:
1. Counts frustrated keywords (frustrated, angry, upset)
2. Counts all-caps words
3. Analyzes punctuation patterns
4. Applies sentiment lexicon scoring
5. Combines factors into final score

**Connection to Next Agent**:
- Sentiment score → **Classification Agent** (affects priority)
- Frustration flag → **Confidence Agent** (affects routing decision)

---

### 3️⃣ Agent 3: Hybrid Classification Agent
**File**: `backend/services/hybrid_classifier_service.py`  
**Type**: Category & Priority Classifier  
**Execution**: WAVE 2 (Sequential, depends on Wave 1)

**Purpose**: Predict ticket category and assign priority

**Responsibilities**:
1. **Category Classification**:
   - ML Model: TF-IDF + Logistic Regression
   - Categories: Network, Software, Hardware, Access, Billing, Email, Security, ServiceRequest, Database
   - Returns probabilities for all categories

2. **Priority Assignment**:
   - ML Model: Random Forest
   - Priorities: Critical, High, Medium, Low
   - Considers: category, sentiment, urgency keywords

3. **Rule-Based Overrides**:
   - Security → Always Critical priority
   - Frustrated user + high urgency → Increase priority
   - Keyword-based category boost

**Input**:
- Cleaned text (from NLP Agent)
- Sentiment score (from Sentiment Agent)
- Text features (word count, urgency keywords)

**Output**:
```python
{
    "category": "Network",
    "category_probabilities": {
        "Network": 0.87,
        "Software": 0.08,
        "Hardware": 0.03,
        ...
    },
    "model_confidence": 0.87,
    "priority": "High",
    "priority_confidence": 0.82,
    "hybrid_override": False  # True if rule override used
}
```

**Hybrid Approach**:
```
IF ml_confidence < 0.55:
    Use keyword-based fallback
ELSE IF category == "Security":
    Override priority = Critical
ELSE:
    Use ML predictions
```

**Connection to Next Agent**:
- Category + Priority → **Retrieval Agent** (search similar tickets)
- Category + Priority → **SLA Agent** (calculate deadline)
- Confidence → **Confidence Agent** (routing decision)

---

### 4️⃣ Agent 4: Retrieval Agent (RAG)
**File**: `backend/services/retrieval_service.py`  
**Type**: Similarity Search  
**Execution**: WAVE 3 (Parallel with Security & Explainability)

**Purpose**: Find similar resolved tickets using Retrieval-Augmented Generation (RAG)

**Responsibilities**:
1. **Embedding Generation**:
   - Model: Sentence Transformers (all-MiniLM-L6-v2)
   - Convert ticket text to 384-dim vector

2. **Similarity Search**:
   - Database: ChromaDB (vector store)
   - Query: Find top-K most similar tickets
   - Filter: Only resolved tickets in same category

3. **Context Building**:
   - Extract solutions from similar tickets
   - Calculate similarity scores
   - Rank by relevance

**Input**:
- Cleaned text
- Category (from Classification Agent)
- Top-K (default: 3)

**Output**:
```python
{
    "similar_tickets": [
        {
            "ticket_id": "TKT-XYZ123",
            "summary": "VPN connection issue",
            "solution": "Restart VPN client and clear cache",
            "similarity_score": 0.92,
            "resolution_time_hours": 2.5,
            "category": "Network"
        },
        # ... 2 more similar tickets
    ],
    "top_similarity_score": 0.92,
    "avg_resolution_time": 2.3
}
```

**How It Works**:
```
1. Embed ticket text → 384-dim vector
2. Query ChromaDB with vector
3. Filter by category + status=resolved
4. Sort by cosine similarity
5. Return top-K results
```

**Connection to Next Agent**:
- Similar tickets → **LLM Response Agent** (context for generation)
- Similarity scores → **Confidence Agent** (boost confidence)
- Avg resolution time → **SLA Agent** (estimate)

---

### 5️⃣ Agent 5: Security Threat Detection Agent
**File**: `backend/services/security_threat_service.py`  
**Type**: Security Analyzer  
**Execution**: WAVE 3 (Parallel with Retrieval & Explainability)

**Purpose**: Detect security threats and suspicious patterns

**Responsibilities**:
1. **Threat Detection**:
   - Phishing attempts
   - Malware mentions
   - Data breach indicators
   - Unauthorized access patterns
   - Social engineering attempts

2. **Pattern Analysis**:
   - Keyword matching (regex patterns)
   - Suspicious phrase detection
   - Threat severity scoring

3. **Escalation Logic**:
   - Immediate escalation for high-severity threats
   - Security team notification
   - SLA override for security tickets

**Input**:
- Cleaned text
- Original text
- Category (from Classification Agent)

**Output**:
```python
{
    "threat_detected": True,
    "threat_type": "phishing",  # phishing|malware|breach|unauthorized_access
    "severity": "high",  # critical|high|medium|low|none
    "confidence": 0.89,
    "recommended_action": "Escalate to security team immediately",
    "indicators": [
        "Suspicious link in description",
        "Request for credentials",
        "Urgency pressure tactics"
    ],
    "escalation_level": "L3",  # L1|L2|L3
    "escalation_timer_started": True
}
```

**Threat Types**:
- **Phishing**: Credential harvesting attempts
- **Malware**: Virus/ransomware reports
- **Data Breach**: Unauthorized data access
- **Unauthorized Access**: Permission violations
- **Social Engineering**: Manipulation attempts

**Connection to Next Agent**:
- Threat detected → **Confidence Agent** (override to escalate)
- Security category → **SLA Agent** (ultra-short deadline)
- Escalation flag → **Routing Decision** (ESCALATE_TO_HUMAN)

---

### 6️⃣ Agent 6: Explainability Agent (LIME)
**File**: `backend/services/explainability_service.py`  
**Type**: Model Interpreter  
**Execution**: WAVE 3 (Parallel with Retrieval & Security)

**Purpose**: Explain ML model predictions using LIME (Local Interpretable Model-agnostic Explanations)

**Responsibilities**:
1. **Feature Importance**:
   - Which words influenced the prediction?
   - Positive vs negative contributions
   - Word weights visualization

2. **Prediction Explanation**:
   - Why this category was chosen?
   - Top contributing features
   - Alternative predictions considered

**Input**:
- Cleaned text
- Predicted category
- ML model

**Output**:
```python
{
    "predicted_class": "Network",
    "explanation_confidence": 0.87,
    "top_positive_features": [
        {"word": "vpn", "weight": 0.42},
        {"word": "connect", "weight": 0.31},
        {"word": "timeout", "weight": 0.18}
    ],
    "top_negative_features": [
        {"word": "billing", "weight": -0.15},
        {"word": "invoice", "weight": -0.09}
    ]
}
```

**How LIME Works**:
```
1. Take the input text
2. Generate perturbed versions (remove words)
3. Get predictions for all versions
4. Train linear model on perturbations
5. Extract feature weights
6. Return top positive/negative features
```

**Connection to Next Agent**:
- Explanations → Stored in database for auditing
- Feature importance → Used in research analysis
- Not directly used by other agents (for transparency only)

---

### 7️⃣ Agent 7: SLA Prediction Agent
**File**: `backend/services/sla_service.py`  
**Type**: Deadline Calculator  
**Execution**: WAVE 4 (Sequential, after classification)

**Purpose**: Predict SLA breach probability and calculate deadlines

**Responsibilities**:
1. **SLA Deadline Calculation**:
   - Based on category + priority matrix
   - Example: Security + Critical = 5 minutes
   - Example: Software + Low = 72 hours

2. **Breach Probability Prediction**:
   - ML Model: Random Forest
   - Predicts if ticket will miss SLA deadline
   - Considers: queue length, time of day, historical patterns

3. **Time Estimation**:
   - Estimated resolution time
   - Minutes remaining until breach
   - Urgency level (ok/warning/critical)

**Input**:
- Category (from Classification Agent)
- Priority (from Classification Agent)
- Submission timestamp
- Current queue length
- Similar ticket resolution times (from Retrieval Agent)

**Output**:
```python
{
    "sla_minutes": 30,  # Total SLA time
    "sla_deadline": "2026-07-30T10:30:00Z",
    "minutes_remaining": 28.5,
    "is_breached": False,
    "urgency_level": "ok",  # ok|warning|critical
    "breach_probability": 0.15,  # 0.0-1.0
    "estimated_resolution_hours": 0.4
}
```

**SLA Matrix** (minutes):
```
Category       | Critical | High  | Medium | Low   |
---------------|----------|-------|--------|-------|
Security       | 5        | 30    | 30     | 30    |
Database       | 5        | 60    | 240    | 1440  |
Network        | 30       | 120   | 480    | 2880  |
Software       | 60       | 240   | 1440   | 4320  |
```

**Breach Prediction Features**:
- Category + Priority
- Submission hour (after-hours = higher risk)
- Day of week (weekend = higher risk)
- Queue length (long queue = higher risk)
- Word count, urgency keywords
- Sentiment score (frustrated = higher priority)

**Connection to Next Agent**:
- SLA breach probability → **Confidence Agent** (affects routing)
- Urgency level → **Routing Decision**
- Estimated time → Displayed to user

---

### 8️⃣ Agent 8: Confidence Scoring Agent
**File**: `backend/services/confidence_service.py`  
**Type**: Confidence Aggregator  
**Execution**: WAVE 4 (Sequential, after all enrichment)

**Purpose**: Calculate composite confidence score and make HITL routing decision

**Responsibilities**:
1. **Multi-Factor Confidence Calculation**:
   - **Model Confidence** (40%): ML classification probability
   - **Similarity Confidence** (35%): Top similarity score from RAG
   - **Keyword Confidence** (25%): Keyword match strength

2. **Confidence Breakdown**:
   - Decompose score into components
   - Identify weak points
   - Transparency for human review

3. **Routing Decision**:
   - **AUTO_RESOLVE** (confidence ≥ 0.85): High confidence, auto-handle
   - **SUGGEST_TO_AGENT** (0.65-0.84): Medium confidence, show suggestion to agent
   - **ESCALATE_TO_AGENT** (0.50-0.64): Low confidence, agent handles directly
   - **ESCALATE_TO_HUMAN** (<0.50 or security): Very low confidence or critical

**Input**:
- Model confidence (from Classification Agent)
- Top similarity score (from Retrieval Agent)
- Keyword match score (internal calculation)
- Category
- Priority
- Sentiment
- Security threat flag (from Security Agent)
- SLA breach probability (from SLA Agent)

**Output**:
```python
{
    "confidence_score": 0.78,  # 0.0-1.0
    "confidence_breakdown": {
        "model_prob_component": 0.34,  # 0.85 * 0.40
        "similarity_component": 0.31,  # 0.89 * 0.35
        "keyword_component": 0.13      # 0.52 * 0.25
    },
    "routing_decision": "SUGGEST_TO_AGENT",
    "sla_override": False,
    "security_override": False
}
```

**Routing Logic**:
```python
IF security_threat_detected:
    return "ESCALATE_TO_HUMAN"
ELIF category == "Security":
    return "ESCALATE_TO_AGENT"
ELIF sla_breach_probability > 0.80:
    return "ESCALATE_TO_AGENT"  # Need fast handling
ELIF confidence >= 0.85:
    return "AUTO_RESOLVE"
ELIF confidence >= 0.65:
    return "SUGGEST_TO_AGENT"
ELIF confidence >= 0.50:
    return "ESCALATE_TO_AGENT"
ELSE:
    return "ESCALATE_TO_HUMAN"
```

**Connection to Next Agent**:
- Routing decision → **LLM Response Agent** (whether to generate)
- Confidence score → Displayed to user and agents
- Routing → Determines final ticket handling

---

### 9️⃣ Agent 9: LLM Response Generation Agent
**File**: `backend/services/llm_service.py`  
**Type**: Text Generator  
**Execution**: WAVE 5 (Sequential, after routing decision)

**Purpose**: Generate contextual responses using LLM (Ollama/Qwen)

**Responsibilities**:
1. **Context Assembly**:
   - Current ticket description
   - Similar resolved tickets (from Retrieval Agent)
   - Category and priority info
   - User sentiment

2. **Prompt Engineering**:
   - System prompt with role and guidelines
   - Context injection with similar solutions
   - Clear instructions for response format

3. **Response Generation**:
   - Call Ollama API (Qwen/Mistral model)
   - Stream or complete generation
   - Fallback to template if LLM fails

4. **Quality Control**:
   - Hallucination detection (check if response mentions similar tickets)
   - Length validation
   - Relevance checking

**Input**:
- Ticket text
- Category
- Priority
- Similar tickets (from Retrieval Agent)
- Routing decision (from Confidence Agent)

**Output**:
```python
{
    "generated_response": "To resolve your VPN connection issue:\n1. Restart VPN client\n2. Clear cache...",
    "model_used": "qwen2.5:3b",
    "generation_time_ms": 1250,
    "hallucination_detected": False,
    "fallback_used": False,
    "response_length": 245
}
```

**Prompt Template**:
```
System: You are a helpful IT support agent. Provide clear, concise solutions.

Context:
Category: Network
Priority: High
User is frustrated: Yes

Similar resolved tickets:
1. VPN timeout issue - Solution: Restart client and check firewall
2. VPN connection drops - Solution: Update VPN software to latest version

User Issue: {ticket_description}

Provide a helpful response with actionable steps.
```

**Execution Logic**:
```python
IF routing_decision == "AUTO_RESOLVE":
    generate_full_response()
ELIF routing_decision == "SUGGEST_TO_AGENT":
    generate_draft_response()
ELIF routing_decision == "ESCALATE_TO_AGENT":
    generate_basic_suggestion()
ELSE:
    skip_generation()  # Human will handle
```

**Connection to Next Agent**:
- Generated response → **Safety Guardrails Agent** (content moderation)
- Generation metadata → Stored for research logging

---

### 🔟 Agent 10: Safety Guardrails Agent
**File**: `backend/services/safety_guardrails_service.py`  
**Type**: Content Moderator  
**Execution**: WAVE 6 (Sequential, final validation)

**Purpose**: Ensure generated responses are safe, appropriate, and compliant

**Responsibilities**:
1. **Content Moderation**:
   - PII detection (SSN, credit cards, phone numbers)
   - Harmful content filtering
   - Inappropriate language detection
   - Discriminatory content checking

2. **Response Sanitization**:
   - Redact sensitive information
   - Remove inappropriate content
   - Apply content policies

3. **Compliance Checking**:
   - GDPR compliance
   - Company policy adherence
   - Legal disclaimers

**Input**:
- Generated response (from LLM Agent)
- Original ticket
- Metadata

**Output**:
```python
{
    "is_safe": True,
    "violations": [],  # List of detected issues
    "sanitized_response": "...",  # Cleaned version if needed
    "was_sanitized": False,
    "response_hash": "sha256_hash_of_response",
    "compliance_checks": {
        "pii_detected": False,
        "harmful_content": False,
        "policy_compliant": True
    }
}
```

**Safety Checks**:
```python
# PII Patterns
SSN: r'\b\d{3}-\d{2}-\d{4}\b'
Credit Card: r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
Phone: r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
Email: r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

# Harmful Content
Profanity: Custom word list
Discriminatory: Protected characteristics
Violence: Threat detection
```

**Sanitization Example**:
```
Input:  "Call me at 555-123-4567 or email john@example.com"
Output: "Call me at [PHONE_REDACTED] or email [EMAIL_REDACTED]"
```

**Connection to Final Output**:
- Safe response → Stored in database
- Violations → Logged for review
- Sanitized response → Sent to user
- **Final routing decision executed** → Ticket assigned to queue/agent/human

---

## 🔗 Agent Interconnections

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    INPUT: User Ticket                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │   Text Validation Agent       │
         │   (Gateway)                   │
         └───────────────┬───────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
    ┌────▼────┐                   ┌──────▼──────┐
    │   NLP   │                   │  Sentiment  │
    │  Agent  │                   │   Agent     │
    └────┬────┘                   └──────┬──────┘
         │                               │
         └───────────────┬───────────────┘
                         │
                    ┌────▼────┐
                    │ Classi- │
                    │ fication│
                    │  Agent  │
                    └────┬────┘
                         │
         ┌───────────────┼───────────────┬───────────────┐
         │               │               │               │
    ┌────▼────┐    ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
    │Retrieval│    │Security │    │   LIME  │    │   SLA   │
    │  Agent  │    │  Agent  │    │  Agent  │    │  Agent  │
    └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘
         │               │               │               │
         └───────────────┼───────────────┴───────────────┘
                         │
                    ┌────▼────┐
                    │Confiden-│
                    │ce Agent │
                    │(Routing)│
                    └────┬────┘
                         │
                    ┌────▼────┐
                    │   LLM   │
                    │Response │
                    │  Agent  │
                    └────┬────┘
                         │
                    ┌────▼────┐
                    │ Safety  │
                    │Guardrail│
                    │  Agent  │
                    └────┬────┘
                         │
         ┌───────────────┴───────────────┐
         │         ROUTING OUTPUT         │
         │   AUTO / SUGGEST / ESCALATE    │
         └────────────────────────────────┘
```

---

## 📊 Agent Dependencies

| Agent | Depends On | Provides To |
|-------|------------|-------------|
| **Text Validation** | None (first) | All agents (validates input) |
| **NLP** | Text Validation | Classification, All downstream |
| **Sentiment** | Text Validation | Classification, Confidence |
| **Classification** | NLP, Sentiment | Retrieval, Security, SLA, All downstream |
| **Retrieval** | Classification | LLM Response, Confidence |
| **Security** | Classification | Confidence, Routing |
| **LIME** | Classification | Audit/Research only |
| **SLA** | Classification | Confidence, Display |
| **Confidence** | All Wave 3 agents | LLM Response, Routing |
| **LLM Response** | Retrieval, Confidence | Safety Guardrails |
| **Safety Guardrails** | LLM Response | Final Output |

---

## ⏱️ Performance Metrics

### Average Processing Time (per agent)

| Agent | Avg Time | Notes |
|-------|----------|-------|
| Text Validation | <5 ms | Regex-based, very fast |
| NLP | 50-100 ms | spaCy processing |
| Sentiment | 10-20 ms | Rule-based + lexicon |
| Classification | 30-50 ms | TF-IDF + ML inference |
| Retrieval | 100-200 ms | ChromaDB vector search |
| Security | 20-30 ms | Pattern matching |
| LIME | 200-500 ms | Perturbation analysis (optional) |
| SLA | 5-10 ms | Simple calculation |
| Confidence | 5-10 ms | Score aggregation |
| LLM Response | 1-3 seconds | Ollama generation (slowest) |
| Safety Guardrails | 20-50 ms | Pattern matching + validation |

**Total Pipeline Time**: 2-5 seconds (depending on LLM)

---

## 🎯 Human-in-the-Loop (HITL) Decision Matrix

| Confidence | SLA Risk | Security | Sentiment | Routing Decision |
|------------|----------|----------|-----------|------------------|
| ≥ 0.85 | Low | No | Any | ✅ AUTO_RESOLVE |
| 0.65-0.84 | Low | No | Any | 👤 SUGGEST_TO_AGENT |
| 0.50-0.64 | Any | No | Any | 👤 ESCALATE_TO_AGENT |
| < 0.50 | Any | No | Any | 🚨 ESCALATE_TO_HUMAN |
| Any | High | No | Frustrated | 🚨 ESCALATE_TO_AGENT |
| Any | Any | Yes | Any | 🚨 ESCALATE_TO_HUMAN |

---

## 💾 Database Storage

Each agent's output is stored in MongoDB:

```javascript
{
  "ticket_id": "TKT-ABC123",
  "ai_analysis": {
    // Wave 1
    "cleaned_text": "...",
    "sentiment_label": "NEGATIVE",
    "sentiment_score": 0.23,
    
    // Wave 2
    "category": "Network",
    "priority": "High",
    "model_confidence": 0.87,
    
    // Wave 3
    "similar_tickets": [...],
    "threat_analysis": {...},
    "lime_explanation": {...},
    
    // Wave 4
    "sla_breach_probability": 0.15,
    "confidence_score": 0.78,
    "routing_decision": "SUGGEST_TO_AGENT",
    
    // Wave 5-6
    "generated_response": "...",
    "safety_validation": {...}
  }
}
```

---

## 🚀 Extending the System

### Adding a New Agent

1. Create service file: `backend/services/new_agent_service.py`
2. Define agent class with `analyze()` method
3. Integrate into pipeline in `backend/routers/tickets.py`
4. Add to appropriate Wave (parallel or sequential)
5. Update database schema if needed
6. Add to documentation

### Example New Agent: "Duplicate Detection Agent"
```python
# Already exists in the system!
# File: backend/services/duplicate_service.py
# Wave: 3 (parallel)
# Purpose: Find duplicate tickets
```

---

## 📚 Further Reading

- **ML Models**: `backend/ml/models/`
- **Training Scripts**: `backend/ml/train.py`
- **API Documentation**: Run server → http://localhost:8000/docs
- **Research Logging**: `RESEARCH_PAPER_IMPLEMENTATION_GUIDE.md`
- **System Architecture**: `COMPREHENSIVE_PROJECT_ANALYSIS.md`

---

## ✅ Summary

**10 AI Agents** working in **6 waves** to intelligently process support tickets:

1. **Text Validation** → Reject gibberish
2. **NLP** → Clean & normalize text
3. **Sentiment** → Detect emotion
4. **Classification** → Categorize & prioritize
5. **Retrieval** → Find similar tickets (RAG)
6. **Security** → Detect threats
7. **SLA** → Calculate deadlines
8. **Confidence** → Route intelligently (HITL)
9. **LLM Response** → Generate solutions
10. **Safety** → Moderate content

**Result**: Intelligent, context-aware, safe ticket handling with confidence-based human oversight.

---

**Last Updated**: 2026-07-30  
**System Version**: 2.0  
**Architecture**: Multi-Agent Pipeline with HITL
