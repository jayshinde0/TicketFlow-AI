# TicketFlow AI - Complete System Architecture

## 🎯 What Happens When You Submit a Ticket

### User Journey: From Submission to Resolution

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USER SUBMITS TICKET                                          │
│    Frontend: TicketForm.jsx                                     │
│    → POST /api/tickets/                                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. BACKEND RECEIVES REQUEST                                     │
│    File: backend/routers/tickets.py                             │
│    Function: submit_ticket()                                    │
│    → Generates ticket ID (TKT-XXXXXX)                           │
│    → Calls run_ai_pipeline()                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. AI PIPELINE STARTS (10 Agents)                               │
│    File: backend/routers/tickets.py                             │
│    Function: run_ai_pipeline()                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ AGENT 0: NLP PREPROCESSING                                      │
│ File: backend/services/nlp_service.py                           │
│ Technology: spaCy (en_core_web_sm)                              │
│                                                                 │
│ Input: "I forgot my password and need to reset it"             │
│ Process:                                                        │
│   - Tokenization: ["I", "forgot", "my", "password", ...]       │
│   - Lemmatization: ["forget", "password", "need", "reset"]     │
│   - Stop word removal: ["forgot", "password", "reset"]         │
│   - Feature extraction: word_count, urgency_keywords           │
│                                                                 │
│ Output:                                                         │
│   cleaned_text: "forgot password need reset"                   │
│   word_count: 8                                                 │
│   urgency_keyword_count: 1                                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ AGENT 1: SENTIMENT ANALYSIS                                     │
│ File: backend/services/sentiment_service.py                     │
│ Technology: HuggingFace Transformers                            │
│ Model: cardiffnlp/twitter-roberta-base-sentiment               │
│                                                                 │
│ Input: "I forgot my password and need to reset it"             │
│ Process:                                                        │
│   - Tokenize text                                               │
│   - Pass through RoBERTa model                                  │
│   - Get sentiment probabilities                                 │
│   - Detect frustration (NEGATIVE + high score)                  │
│                                                                 │
│ Output:                                                         │
│   sentiment_label: "NEUTRAL"                                    │
│   sentiment_score: 0.45                                         │
│   is_frustrated: false                                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ AGENT 2: CATEGORY & PRIORITY CLASSIFICATION                     │
│ File: backend/services/classifier_service.py                    │
│ Technology: Scikit-learn                                        │
│ Models:                                                         │
│   - TF-IDF Vectorizer (text → numbers)                          │
│   - Logistic Regression (category)                              │
│   - Random Forest (priority)                                    │
│                                                                 │
│ Input: "forgot password need reset"                            │
│ Process:                                                        │
│   1. TF-IDF Transform:                                          │
│      Text → 384-dimensional vector                              │
│      ["forgot": 0.82, "password": 0.91, "reset": 0.76, ...]    │
│                                                                 │
│   2. Category Prediction:                                       │
│      Logistic Regression on TF-IDF features                     │
│      Outputs probabilities for 10 categories                    │
│                                                                 │
│   3. Priority Prediction:                                       │
│      Random Forest with category + features                     │
│      Outputs: Low/Medium/High/Critical                          │
│                                                                 │
│ Output:                                                         │
│   category: "Auth" (or "Security" if model poorly trained)     │
│   model_confidence: 0.92                                        │
│   category_probabilities: {                                     │
│     "Auth": 0.92,                                               │
│     "Security": 0.04,                                           │
│     "Software": 0.02                                            │
│   }                                                             │
│   priority: "Medium"                                            │
│   priority_confidence: 0.88                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ AGENT 3: EMBEDDING & RETRIEVAL (RAG)                            │
│ File: backend/services/embedding_service.py                     │
│       backend/services/retrieval_service.py                     │
│ Technology: Sentence Transformers + ChromaDB                    │
│ Model: all-MiniLM-L6-v2                                         │
│                                                                 │
│ Input: "forgot password need reset"                            │
│ Process:                                                        │
│   1. Generate Embedding:                                        │
│      Text → 384-dimensional vector                              │
│      [0.23, -0.45, 0.67, ..., 0.12]  (384 numbers)             │
│                                                                 │
│   2. Query ChromaDB:                                            │
│      - Search in "resolved_tickets" collection                  │
│      - Find top 3 most similar past tickets                     │
│      - Use cosine similarity                                    │
│                                                                 │
│   3. Retrieve Solutions:                                        │
│      Past ticket: "Cannot login, forgot password"              │
│      Similarity: 0.94 (94% similar)                             │
│      Solution: "To reset password: 1. Go to..."                │
│                                                                 │
│ Output:                                                         │
│   similar_tickets: [                                            │
│     {                                                           │
│       ticket_id: "TKT-OLD123",                                  │
│       similarity_score: 0.94,                                   │
│       solution: "To reset password: 1. Go to login page..."    │
│     },                                                          │
│     { ... 2 more similar tickets ... }                          │
│   ]                                                             │
│   top_similarity_score: 0.94                                    │
│   embedding: [0.23, -0.45, ...]                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ AGENT 4: SLA PREDICTION                                         │
│ File: backend/services/sla_service.py                           │
│ Technology: Rule-based + ML predictor                           │
│                                                                 │
│ Input:                                                          │
│   category: "Auth"                                              │
│   priority: "Medium"                                            │
│   user_tier: "Standard"                                         │
│   time_of_day: 14 (2 PM)                                        │
│   queue_length: 10                                              │
│                                                                 │
│ Process:                                                        │
│   1. Lookup SLA Limit:                                          │
│      Auth + Medium = 240 minutes (4 hours)                      │
│                                                                 │
│   2. Predict Breach Probability:                                │
│      Random Forest model considers:                             │
│      - Category urgency                                         │
│      - Current queue length                                     │
│      - Time of day (peak hours?)                                │
│      - Historical resolution times                              │
│                                                                 │
│ Output:                                                         │
│   sla_breach_probability: 0.15 (15% chance)                     │
│   sla_minutes: 240                                              │
│   estimated_resolution_hours: 0.5                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ AGENT 5: HITL ROUTING DECISION                                  │
│ File: backend/services/hitl_service.py                          │
│       backend/services/confidence_service.py                    │
│ Technology: Multi-factor confidence scoring                     │
│                                                                 │
│ Input:                                                          │
│   model_confidence: 0.92                                        │
│   top_similarity_score: 0.94                                    │
│   priority_confidence: 0.88                                     │
│   sentiment_score: 0.45                                         │
│   category: "Auth"                                              │
│   sla_breach_probability: 0.15                                  │
│                                                                 │
│ Process:                                                        │
│   1. Calculate Composite Confidence:                            │
│      confidence = (0.92 × 0.40) +  // model confidence 40%     │
│                   (0.94 × 0.30) +  // similarity 30%            │
│                   (0.88 × 0.20) +  // priority 20%              │
│                   (0.55 × 0.10)    // sentiment 10%             │
│      confidence = 0.89 (89%)                                    │
│                                                                 │
│   2. Check Overrides:                                           │
│      ❌ Security category? No                                   │
│      ❌ Frustrated user? No                                     │
│      ❌ SLA breach risk > 75%? No (15%)                         │
│      ❌ Database category? No                                   │
│                                                                 │
│   3. Apply Routing Logic:                                       │
│      IF confidence >= 0.85 AND no overrides:                    │
│        → AUTO_RESOLVE                                           │
│      ELIF confidence >= 0.60:                                   │
│        → SUGGEST_TO_AGENT                                       │
│      ELSE:                                                      │
│        → ESCALATE_TO_HUMAN                                      │
│                                                                 │
│ Output:                                                         │
│   routing_decision: "AUTO_RESOLVE"                              │
│   confidence_score: 0.89                                        │
│   confidence_breakdown: {                                       │
│     model_prob_component: 0.368,                                │
│     similarity_component: 0.282,                                │
│     priority_component: 0.176,                                  │
│     sentiment_component: 0.055                                  │
│   }                                                             │
│   sla_override: false                                           │
│   security_override: false                                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ AGENT 6: LLM RESPONSE GENERATION (RAG)                          │
│ File: backend/services/llm_service.py                           │
│ Technology: Ollama (Mistral-Nemo 7B)                            │
│ Running: localhost:11434                                        │
│                                                                 │
│ Input:                                                          │
│   ticket_text: "I forgot my password and need to reset it"     │
│   category: "Auth"                                              │
│   retrieved_solution: "To reset password: 1. Go to login..."   │
│   routing_decision: "AUTO_RESOLVE"                              │
│                                                                 │
│ Process:                                                        │
│   1. Build RAG Prompt:                                          │
│      """                                                        │
│      You are a professional IT support specialist.              │
│                                                                 │
│      User ticket: I forgot my password and need to reset it     │
│      Category: Auth                                             │
│                                                                 │
│      Similar resolved ticket solution:                          │
│      To reset password: 1. Go to login page...                  │
│                                                                 │
│      Write a professional support response in 3-4 sentences.    │
│      Be specific and actionable. Use numbered steps.            │
│      """                                                        │
│                                                                 │
│   2. Call Ollama API:                                           │
│      POST http://localhost:11434/api/generate                   │
│      {                                                          │
│        "model": "mistral-nemo",                                 │
│        "prompt": "...",                                         │
│        "temperature": 0.3,                                      │
│        "max_tokens": 250                                        │
│      }                                                          │
│                                                                 │
│   3. Mistral-Nemo Generates Response:                           │
│      LLM reads prompt + retrieved solution                      │
│      Generates new response based on context                    │
│      Output: "To reset your password: 1. Go to..."             │
│                                                                 │
│   4. Hallucination Detection:                                   │
│      - Generate embedding of LLM response                       │
│      - Generate embedding of retrieved solution                 │
│      - Calculate cosine similarity                              │
│      - If similarity < 0.55 → Hallucination detected!           │
│      - Fallback to retrieved solution                           │
│                                                                 │
│ Output:                                                         │
│   generated_response: "To reset your password:                  │
│     1. Go to the login page and click 'Forgot Password'         │
│     2. Enter your email address (john.doe@company.com)          │
│     3. Check your spam/junk folder for the reset email          │
│     4. If not received within 5 minutes, contact IT support     │
│     The reset link expires in 1 hour for security."             │
│                                                                 │
│   hallucination_detected: false                                 │
│   fallback_used: false                                          │
│   model_used: "mistral-nemo"                                    │
│   generation_time_ms: 2847                                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ AGENT 7: LIME EXPLAINABILITY                                    │
│ File: backend/services/explainability_service.py                │
│ Technology: LIME (Local Interpretable Model-agnostic)           │
│                                                                 │
│ Input: "forgot password need reset"                            │
│ Process:                                                        │
│   1. Generate 200 perturbed samples:                            │
│      - "forgot password need"                                   │
│      - "password need reset"                                    │
│      - "forgot need reset"                                      │
│      ... (200 variations)                                       │
│                                                                 │
│   2. Get predictions for each sample                            │
│   3. Train local linear model                                   │
│   4. Extract feature weights                                    │
│                                                                 │
│ Output:                                                         │
│   top_positive_features: [                                      │
│     {"word": "password", "weight": 0.82},                       │
│     {"word": "forgot", "weight": 0.76},                         │
│     {"word": "reset", "weight": 0.65}                           │
│   ]                                                             │
│   top_negative_features: [...]                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ AGENT 8: DUPLICATE DETECTION                                    │
│ File: backend/services/duplicate_service.py                     │
│                                                                 │
│ Process:                                                        │
│   - Search for similar OPEN tickets in last 7 days              │
│   - If similarity > 0.95 → Exact duplicate                      │
│   - If similarity > 0.85 → Possible duplicate                   │
│                                                                 │
│ Output:                                                         │
│   is_duplicate: false                                           │
│   duplicate_of: null                                            │
│   is_possible_duplicate: false                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ AGENT 9: AUDIT LOGGING                                          │
│ File: backend/services/audit_service.py                         │
│                                                                 │
│ Process:                                                        │
│   - Log complete pipeline execution                             │
│   - Store all predictions and confidences                       │
│   - Track model versions                                        │
│   - Record processing time                                      │
│                                                                 │
│ Storage: MongoDB "audit_logs" collection                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ AGENT 10: NOTIFICATION                                          │
│ File: backend/services/notification_service.py                  │
│                                                                 │
│ Process:                                                        │
│   - Send WebSocket message to connected agents                  │
│   - Broadcast new ticket alert                                  │
│   - Update dashboard in real-time                               │
│                                                                 │
│ WebSocket: ws://localhost:8000/ws/dashboard                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. STORE TICKET IN MONGODB                                      │
│    Database: ticketflow_ai                                      │
│    Collection: tickets                                          │
│                                                                 │
│    Document Structure:                                          │
│    {                                                            │
│      ticket_id: "TKT-ABC123",                                   │
│      subject: "Forgot my password",                             │
│      description: "I forgot my password...",                    │
│      status: "open",                                            │
│      created_at: "2026-03-21T15:30:00Z",                        │
│      ai_analysis: {                                             │
│        category: "Auth",                                        │
│        priority: "Medium",                                      │
│        confidence_score: 0.89,                                  │
│        routing_decision: "AUTO_RESOLVE",                        │
│        generated_response: "To reset your password: 1. Go...", │
│        similar_tickets: [...],                                  │
│        lime_explanation: {...},                                 │
│        processing_time_ms: 3521                                 │
│      }                                                          │
│    }                                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. RETURN RESPONSE TO USER                                      │
│    File: backend/routers/tickets.py                             │
│                                                                 │
│    HTTP 201 Created                                             │
│    {                                                            │
│      ticket_id: "TKT-ABC123",                                   │
│      message: "Your ticket has been automatically resolved!",   │
│      status: "open",                                            │
│      ai_analysis: { ... },                                      │
│      estimated_resolution_hours: 0.5                            │
│    }                                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. FRONTEND DISPLAYS RESPONSE                                   │
│    File: frontend/src/components/ticket/TicketForm.jsx          │
│                                                                 │
│    User sees:                                                   │
│    ✅ Ticket Submitted Successfully!                            │
│    🎫 Ticket ID: TKT-ABC123                                     │
│    🤖 AI Analysis:                                              │
│       Category: Auth                                            │
│       Priority: Medium                                          │
│       Confidence: 89%                                           │
│       Routing: AUTO_RESOLVE                                     │
│                                                                 │
│    💬 Resolution:                                               │
│    To reset your password:                                      │
│    1. Go to the login page and click "Forgot Password"          │
│    2. Enter your email address...                               │
│    3. Check your spam/junk folder...                            │
│    4. If not received within 5 minutes, contact IT support      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. AGENT REVIEWS IN AGENT QUEUE                                 │
│    File: frontend/src/pages/AgentQueue.jsx                      │
│          frontend/src/components/agent/ReviewPanel.jsx          │
│                                                                 │
│    Agent sees:                                                  │
│    - Ticket in queue with confidence badge                      │
│    - Clicks ticket → Review panel opens                         │
│    - Sees generated response                                    │
│    - Sees similar tickets                                       │
│    - Sees LIME explanation                                      │
│    - Decides: Approve / Edit / Reject                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. AGENT APPROVES TICKET                                        │
│    File: backend/routers/feedback.py                            │
│    Function: approve_suggestion()                               │
│                                                                 │
│    Process:                                                     │
│    1. Mark ticket as resolved in MongoDB                        │
│    2. Store feedback for retraining                             │
│    3. Add solution to ChromaDB for future RAG                   │
│    4. Update audit log                                          │
│    5. Send notification                                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 9. SOLUTION STORED IN CHROMADB                                  │
│    File: backend/services/retrieval_service.py                  │
│    Function: add_resolved_ticket()                              │
│                                                                 │
│    ChromaDB Storage:                                            │
│    Collection: "resolved_tickets"                               │
│    {                                                            │
│      id: "TKT-ABC123",                                          │
│      embedding: [0.23, -0.45, ...],  // 384-dim vector         │
│      document: "forgot password need reset",                    │
│      metadata: {                                                │
│        solution: "To reset your password: 1. Go...",            │
│        category: "Auth",                                        │
│        priority: "Medium",                                      │
│        resolution_time_hours: 0.5                               │
│      }                                                          │
│    }                                                            │
│                                                                 │
│    Future tickets with similar text will retrieve this!         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 10. CONTINUOUS LEARNING LOOP                                    │
│     File: backend/services/retraining_service.py                │
│                                                                 │
│     After 200 feedback records:                                 │
│     1. Fetch corrected labels from feedback collection          │
│     2. Retrain category + priority classifiers                  │
│     3. Evaluate on test set                                     │
│     4. Save new models if performance improves                  │
│     5. Update version number                                    │
│     6. Notify agents of retraining completion                   │
│                                                                 │
│     Model improves over time with agent feedback!               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Key Files and Their Roles

### Backend Core
- `backend/main.py` - FastAPI app entry point, registers routers
- `backend/core/config.py` - All configuration settings
- `backend/core/database.py` - MongoDB connection manager
- `backend/core/security.py` - JWT authentication
- `backend/core/websocket_manager.py` - WebSocket connection manager

### Routers (API Endpoints)
- `backend/routers/tickets.py` - **MAIN FILE** - Ticket CRUD + AI pipeline
- `backend/routers/feedback.py` - Agent approve/edit/reject actions
- `backend/routers/auth.py` - Login/register endpoints
- `backend/routers/agents.py` - Agent management
- `backend/routers/analytics.py` - Dashboard metrics
- `backend/routers/admin.py` - Admin operations
- `backend/routers/websocket.py` - WebSocket connections

### AI Services (The 10 Agents)
- `backend/services/nlp_service.py` - Agent 0: Text preprocessing (spaCy)
- `backend/services/sentiment_service.py` - Agent 1: Sentiment analysis (HuggingFace)
- `backend/services/classifier_service.py` - Agent 2: Category/Priority (Scikit-learn)
- `backend/services/embedding_service.py` - Agent 3a: Text embeddings (Sentence Transformers)
- `backend/services/retrieval_service.py` - Agent 3b: Similar ticket retrieval (ChromaDB)
- `backend/services/sla_service.py` - Agent 4: SLA prediction
- `backend/services/confidence_service.py` - Agent 5a: Confidence calculation
- `backend/services/hitl_service.py` - Agent 5b: HITL routing decision
- `backend/services/llm_service.py` - **Agent 6: LLM response generation (Mistral-Nemo)** ⭐
- `backend/services/explainability_service.py` - Agent 7: LIME explanations
- `backend/services/duplicate_service.py` - Agent 8: Duplicate detection
- `backend/services/audit_service.py` - Agent 9: Audit logging
- `backend/services/notification_service.py` - Agent 10: Real-time notifications

### ML Models
- `backend/ml/train.py` - Training pipeline for all models
- `backend/ml/data_loader.py` - Synthetic data generation
- `backend/ml/feature_engineering.py` - TF-IDF vectorizer
- `backend/ml/models/category_classifier.py` - Logistic Regression for categories
- `backend/ml/models/priority_classifier.py` - Random Forest for priority
- `backend/ml/models/sla_predictor.py` - SLA breach predictor
- `backend/ml/artifacts/` - Trained model files (.pkl)

### Frontend
- `frontend/src/pages/AgentQueue.jsx` - Agent workspace
- `frontend/src/components/agent/ReviewPanel.jsx` - **Shows AI response** ⭐
- `frontend/src/components/ticket/TicketForm.jsx` - Ticket submission
- `frontend/src/hooks/useWebSocket.js` - Real-time updates
- `frontend/src/services/api.js` - API client

---

## 🤖 Yes, the Response is Generated by Mistral-Nemo LLM!

### How LLM Generation Works:

1. **Retrieval-Augmented Generation (RAG)**:
   - System retrieves similar past tickets from ChromaDB
   - Extracts the solution from most similar ticket
   - Passes it as context to LLM

2. **Prompt Engineering**:
   ```
   You are a professional IT support specialist.
   
   User ticket: [ticket text]
   Category: [category]
   
   Similar resolved ticket solution: [retrieved solution]
   
   Write a professional support response in 3-4 sentences.
   ```

3. **Mistral-Nemo Generates**:
   - Reads the prompt + context
   - Generates new response based on retrieved solution
   - Adapts language to be professional and actionable

4. **Hallucination Detection**:
   - Compares LLM response to retrieved solution
   - If too different (similarity < 0.55) → Use retrieved solution instead
   - Prevents AI from making up information

### Why RAG is Important:

- **Without RAG**: LLM might hallucinate or give generic answers
- **With RAG**: LLM has real past solutions as reference
- **Result**: Accurate, specific, helpful responses

---

## 🎯 Summary

**When you submit a ticket:**
1. Text is cleaned and analyzed
2. ML models classify category and priority
3. ChromaDB finds similar past tickets
4. **Mistral-Nemo LLM generates response using RAG**
5. Confidence score determines routing
6. Agent reviews and approves
7. Solution stored for future tickets
8. System learns and improves

**The AI response you see is generated by Mistral-Nemo (7B parameter LLM) running locally via Ollama, using Retrieval-Augmented Generation (RAG) with past ticket solutions as context!**
