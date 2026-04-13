# TicketFlow AI — Backend Deep Dive

## What Is This Project?

TicketFlow AI is an intelligent IT support ticket system. When a user submits a support ticket, the backend automatically classifies it, predicts its priority, decides how to handle it, generates a response, and detects security threats — all without human intervention (unless the system decides a human is needed).

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI (Python) |
| Database | MongoDB |
| Vector Store | ChromaDB |
| ML Models | scikit-learn (Logistic Regression, Random Forest) |
| LLM | Ollama (Mistral-Nemo, local) |
| Embeddings | sentence-transformers |
| Background Jobs | APScheduler |
| Real-time | WebSockets |

---

## The Full Pipeline — Step by Step

When a ticket is submitted via `POST /tickets`, this is exactly what happens:

```
User submits ticket
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                    run_ai_pipeline()                        │
│                                                             │
│  Step 0: NLP Preprocessing (nlp_service)                   │
│    → Clean text, extract features (word count, urgency)    │
│                                                             │
│  Step 1: Sentiment Analysis (sentiment_service)            │
│    → POSITIVE / NEUTRAL / NEGATIVE + frustration flag      │
│                                                             │
│  Step 2: Classification (classifier_service) ← Agent 1    │
│    → Category (10 types) + Priority (Low/Med/High/Crit)    │
│    → If confidence < 0.60 → fallback to Ollama zero-shot   │
│                                                             │
│  Step 3: Vector Retrieval (retrieval_service) ← Agent 2   │
│    → Find top-3 similar past tickets in ChromaDB           │
│    → Returns solutions + similarity scores                 │
│                                                             │
│  Step 4: SLA Prediction (sla_service)                      │
│    → Predict breach probability based on category/priority │
│                                                             │
│  Step 5: HITL Routing (confidence_service) ← Agent 3      │
│    → Compute composite confidence score                    │
│    → Decide: AUTO_RESOLVE / SUGGEST_TO_AGENT / ESCALATE    │
│                                                             │
│  Step 6: LLM Response Generation (llm_service) ← Agent 4  │
│    → Build RAG prompt from ticket + retrieved solution     │
│    → Call Ollama Mistral to generate response              │
│    → Hallucination check (cosine similarity guard)         │
│                                                             │
│  Step 7: Safety Guardrails (safety_guardrails_service)     │
│    → Validate LLM output for harmful content               │
│    → Sanitize or escalate if violations found              │
│                                                             │
│  Step 8: Security Threat Analysis                          │
│    → Rule engine + ML + ChromaDB attack similarity         │
│    → Levels: normal / suspicious / attack                  │
│    → Attacks → force ESCALATE_TO_HUMAN + Critical priority │
│                                                             │
│  Step 9: LIME Explainability (explainability_service)      │
│    → Which words drove the category prediction?            │
│                                                             │
│  Step 10: Duplicate Detection (duplicate_service)          │
│    → Is this ticket already open?                          │
│                                                             │
│  Step 11: Audit Logging (audit_service)                    │
│    → Full pipeline run stored for compliance/retraining    │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
  Ticket stored in MongoDB with full ai_analysis doc
  WebSocket broadcast to frontend dashboard
```

---

## The 3 Routing Outcomes

Every ticket ends up in one of three states:

| Decision | Meaning | When |
|---|---|---|
| `AUTO_RESOLVE` | System sends the LLM response automatically | Confidence ≥ 0.78 |
| `SUGGEST_TO_AGENT` | System suggests a response, agent reviews | Confidence 0.55–0.78 |
| `ESCALATE_TO_HUMAN` | Ticket goes straight to a human agent | Confidence < 0.55, Security tickets, SLA breach risk > 75%, or attack detected |

---

## Confidence Score Formula

The routing decision is driven by a composite confidence score:

```
confidence = (0.60 × model_probability)
           + (0.25 × vector_similarity_score)
           + (0.20 × domain_keyword_boost)

if user is NEGATIVE and very frustrated: confidence -= 0.05
if model_confidence >= 0.90:            confidence += 0.05  (bonus)
```

**Overrides (bypass confidence entirely):**
- Category = `Security` → always ESCALATE
- SLA breach probability > 75% → always ESCALATE
- Security pipeline detects `attack` → always ESCALATE + Critical priority

---

## The 10 Ticket Categories

```
Network | Auth | Security | Database | Billing
Software | Hardware | Email | Access | ServiceRequest
```

Each maps to a department (e.g., Network → NETWORK_OPS, Auth → IDENTITY_MGMT).

---

## ML Models

Two scikit-learn models trained on historical ticket data:

**Category Classifier** — Logistic Regression
- Input: TF-IDF features + metadata (user tier, submission hour)
- Output: category + probability distribution across all 10 classes

**Priority Classifier** — Random Forest
- Input: same feature matrix
- Output: Low / Medium / High / Critical

Both are saved as `.pkl` files in `ml/artifacts/` and loaded lazily on first request.

If ML confidence is too low (< 0.60), the system falls back to **Ollama zero-shot classification** — asking the LLM directly to classify the ticket.

---

## Why LLM (Ollama/Mistral)?

The LLM is used for 3 specific tasks:

1. **Response generation** — Takes the ticket + a retrieved past solution and writes a professional, actionable support reply (RAG pattern)
2. **Knowledge article generation** — When a ticket is resolved, converts it into a structured KB article for future retrieval
3. **Root cause hypothesis** — When many similar tickets spike, generates a one-sentence explanation of what's likely causing the incident

The LLM is NOT used for classification — that's the ML models' job. The LLM only handles natural language generation.

---

## Vector Database (ChromaDB)

ChromaDB stores embeddings of resolved tickets and knowledge base articles.

Used for:
- **Retrieval** — find the 3 most similar past tickets to the current one (gives the LLM context)
- **Duplicate detection** — if a new ticket is too similar to an open one, flag it
- **Security attack similarity** — compare new tickets against known attack patterns

Embeddings are generated by `sentence-transformers` (all-MiniLM-L6-v2).

---

## Security Threat Pipeline

Every ticket runs through two security checks in parallel:

1. **Legacy threat service** — Ollama-based analysis for phishing, malware, social engineering
2. **New AI security pipeline** — Rule engine + ML + ChromaDB attack similarity

Threat levels: `normal` → `suspicious` → `attack`

If `attack` is detected:
- Routing forced to `ESCALATE_TO_HUMAN`
- Priority forced to `Critical`
- Escalation chain created
- WebSocket alert broadcast to all connected agents

---

## Background Jobs (APScheduler)

Three jobs run automatically in the background:

| Job | Interval | What it does |
|---|---|---|
| Root cause detection | Every 5 min | Detects ticket spikes, generates LLM hypothesis |
| SLA warning check | Every 2 min | Alerts agents when tickets are near SLA breach |
| Escalation chain check | Every 5 min | Advances escalation timers |

---

## API Routers

| Router | Prefix | Purpose |
|---|---|---|
| auth | /auth | Register, login, JWT tokens |
| tickets | /tickets | Submit, list, get tickets |
| agents | /agents | Queue, workload, assignment |
| analytics | /analytics | Dashboard stats, charts |
| feedback | /feedback | Agent approve/reject AI suggestions |
| security | /security | Threat center, incident reports |
| admin | /admin | Model retraining, KB management |
| websocket | /ws | Real-time push to frontend |
| queue | /queue | Pipeline queue status |
| simulation | /simulation | Load testing / demo mode |
| images | /images | Ticket image attachments |

---

## Data Flow Summary

```
Frontend (React)
    │  POST /tickets
    ▼
FastAPI Router
    │
    ▼
run_ai_pipeline()  ←── 11 sequential steps
    │
    ▼
MongoDB  ←── stores ticket + full ai_analysis
    │
    ▼
WebSocket broadcast  ←── live dashboard update
    │
    ▼
Agent Dashboard  ←── agent sees ticket + AI suggestion
    │
    ▼
Agent approves/rejects  ←── feedback stored
    │
    ▼
ChromaDB updated  ←── resolved ticket added to knowledge base
    │
    ▼
Models retrained periodically  ←── continuous improvement loop
```

---

## Key Design Decisions

- **Confidence-based HITL** — the system only auto-resolves when it's confident enough. Humans stay in the loop for edge cases.
- **RAG over pure LLM** — the LLM always has a retrieved solution as context, reducing hallucinations. A cosine similarity check catches any hallucinated responses.
- **Security always escalates** — no security ticket is ever auto-resolved, by design.
- **Fallback at every step** — if Ollama is down, if ChromaDB times out, if ML models aren't trained yet — every agent has a fallback so the pipeline never crashes.
- **Audit trail** — every pipeline run is logged with full details for compliance and model retraining.
