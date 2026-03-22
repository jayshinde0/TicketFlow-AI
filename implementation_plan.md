# TicketFlow-AI — Confidence-Based HITL Enhancement

## Feature Audit Report

The full codebase has been scanned: 7 backend routers, 16 services, 4 model schemas, 3 ML classifiers, 4 core modules, 2 task files, 3 utils, 11 frontend pages, and all configuration files.

---

### FEATURE 1 — Automatic Ticket Classification

| Sub-feature | Status | Notes |
|---|---|---|
| 1a. Priority | ✅ FULLY IMPLEMENTED | `PriorityClassifier` (Random Forest) in [ml/models/priority_classifier.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/ml/models/priority_classifier.py). Labels: Low/Medium/High/Critical. TF-IDF features. Urgency keywords handled in `data_loader.py:assign_priority()`. Enterprise tier boost in [confidence_service.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/services/confidence_service.py). |
| 1b. Category | ✅ FULLY IMPLEMENTED | `CategoryClassifier` (Logistic Regression) in [ml/models/category_classifier.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/ml/models/category_classifier.py). 10 categories: Network/Auth/Software/Hardware/Access/Billing/Email/Security/ServiceRequest/Database. TF-IDF vectorizer. Keyword fallback exists. |
| 1b. Ollama fallback | ❌ NOT IMPLEMENTED | No zero-shot Ollama classification fallback for low-confidence categories. |
| 1c. Time Sensitivity | ❌ NOT IMPLEMENTED | No IMMEDIATE/SAME_DAY/STANDARD classification. SLA deadlines exist in [sla_service.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/services/sla_service.py) but not the explicit time sensitivity label. |

> **Action**: Add time sensitivity classification. Add Ollama zero-shot fallback for low-confidence (<0.60) category predictions.

---

### FEATURE 2 — HITL Routing with Confidence Score

| Sub-feature | Status | Notes |
|---|---|---|
| 2a. Confidence formula | ✅ FULLY IMPLEMENTED | [confidence_service.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/services/confidence_service.py): `0.5×model + 0.35×sim + 0.15×keyword`. Exact match to spec. |
| 2b. Three-tier routing | ✅ FULLY IMPLEMENTED | ≥0.85 → AUTO_RESOLVE, ≥0.60 → SUGGEST_TO_AGENT, <0.60 → ESCALATE_TO_HUMAN. Thresholds in [.env](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/.env). |
| 2c. One-click approve | ✅ FULLY IMPLEMENTED | [feedback.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/models/feedback.py) router: approve/edit/reject/escalate endpoints. Frontend [TicketDetail.jsx](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/frontend/src/pages/TicketDetail.jsx) has approve/reject/edit buttons. |
| 2c. Keyboard shortcuts | ❌ NOT IMPLEMENTED | No keyboard shortcuts (A/R/E) on agent view. |
| 2c. SLA countdown timer | ❌ NOT IMPLEMENTED | SLA data available but no live countdown timer on ticket cards. |
| 2c. Classification reasoning | ✅ PARTIALLY | LIME explanation exists in [explainability_service.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/services/explainability_service.py). Confidence breakdown shown. Missing: top-3 similar tickets in agent view. |

> **Action**: Add keyboard shortcuts, SLA countdown timer, and show top-3 similar tickets in agent queue view.

---

### FEATURE 3 — Secure Auto-Resolution

| Sub-feature | Status | Notes |
|---|---|---|
| 3a. Ollama response | ✅ FULLY IMPLEMENTED | [llm_service.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/services/llm_service.py) calls Ollama `/api/generate` with RAG prompt. Hallucination detection via cosine sim. Fallback to retrieved solution. |
| 3b. Regex safety check | ❌ NOT IMPLEMENTED | No regex filtering for card numbers, SSN, passwords in generated responses. |
| 3b. Higher threshold for SECURITY/BILLING | ❌ PARTIALLY | Security always escalates (threshold=0). Billing uses default 0.85. Need 0.92 for Billing auto-resolve. |
| 3b. Auto-resolution logging | ✅ PARTIALLY | [audit_service.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/services/audit_service.py) logs all pipeline runs. Missing: response SHA256 hash. |

> **Action**: Add regex safety guardrail. Raise Billing auto-resolve threshold to 0.92. Add SHA256 hash to audit logs.

---

### FEATURE 4 — Priority Queue

| Sub-feature | Status | Notes |
|---|---|---|
| 4a. Priority queue | ❌ NOT IMPLEMENTED | No asyncio+heapq priority queue. Tickets processed inline in the POST endpoint. |
| 4b. Concurrent processing | ❌ PARTIALLY | Some `asyncio.wait_for()` used but classification + retrieval NOT run in parallel via `asyncio.gather()`. |
| 4c. `/admin/queue` page | ❌ NOT IMPLEMENTED | No queue monitor page exists. |

> **Action**: Add priority queue with heapq, parallelize classification + retrieval, add `/admin/queue` page.

---

### FEATURE 5 — Simulation Mode

| Sub-feature | Status | Notes |
|---|---|---|
| 5a-d. Full simulation | ❌ NOT IMPLEMENTED | No simulation mode. [generate_demo_tickets.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/generate_demo_tickets.py) exists but is a CLI script, not an interactive simulation. |

> **Action**: Build full `/admin/simulation` page with WebSocket-driven real-time visualization.

---

### FEATURE 6 — Response Time Optimization

| Sub-feature | Status | Notes |
|---|---|---|
| 6a. Caching | ❌ NOT IMPLEMENTED | No cachetools LRU cache on TF-IDF vectors, similarity results, or Ollama responses. |
| 6b. Async pipeline | ❌ PARTIALLY | Classification and retrieval run sequentially, not with `asyncio.gather()`. |
| 6c. Performance logging | ❌ PARTIALLY | `processing_time_ms` stored per ticket but no per-stage breakdown (preprocessing_ms, classification_ms, etc.). No `performance_logs` collection. |
| 6d. Latency panel | ❌ NOT IMPLEMENTED | No p50/p95/p99 latency widget on admin dashboard. |

> **Action**: Add LRU caching, parallelize pipeline, add per-stage timing, add latency widget.

---

### FEATURE 7 — Department Routing

| Sub-feature | Status | Notes |
|---|---|---|
| 7a. Department taxonomy | ❌ NOT IMPLEMENTED | Categories exist (10 domains) but no department-to-category mapping as specified (NETWORK, SOFTWARE, DATABASE, SECURITY, BILLING, HR_FACILITIES). |
| 7b. Assignment logic | ❌ NOT IMPLEMENTED | Agent `skills` field exists on user model but no automatic department-based assignment algorithm. |
| 7c. Cross-department tagging | ❌ NOT IMPLEMENTED | No primary/secondary department fields on tickets. |

> **Action**: Build department taxonomy, mapping, and assignment logic.

---

### FEATURE 8 — Security Threat Detection

| Sub-feature | Status | Notes |
|---|---|---|
| 8a-d. Threat detection | ❌ NOT IMPLEMENTED | Security category exists and auto-escalates, but no Ollama-based threat analysis, no disguised attack pre-filter, no threat type classification. |
| 8e. `/admin/security` | ❌ NOT IMPLEMENTED | No security threat feed page. |

> **Action**: Build full security threat detection pipeline and `/admin/security` page.

---

### FEATURE 9 — Attack Escalation Chain

| Sub-feature | Status | Notes |
|---|---|---|
| 9a. Escalation tiers | ❌ NOT IMPLEMENTED | No timed escalation chain (L1 → L2 → L3). |
| 9b. Response playbooks | ❌ NOT IMPLEMENTED | No checkable playbook steps per threat type. |
| 9c. Post-incident form | ❌ NOT IMPLEMENTED | No root cause / affected user count form for security incidents. |

> **Action**: Build escalation chain with APScheduler, playbooks, and post-incident form.

---

### FEATURE 10 — Multi-Domain Model Training

| Sub-feature | Status | Notes |
|---|---|---|
| 10a. Synthetic data via Ollama | ❌ NOT IMPLEMENTED | Synthetic data exists in [data_loader.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/ml/data_loader.py) (10K templates) but not generated via Ollama. |
| 10b. Model architecture | ✅ FULLY IMPLEMENTED | Category: TF-IDF + Logistic Regression. Priority: TF-IDF + Random Forest. Both use correct architectures. |
| 10c. Unseen ticket handling | ❌ PARTIALLY | No Ollama zero-shot fallback for conf<0.60. No empty/short text guards. Language detection exists in [nlp_service.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/services/nlp_service.py). |
| 10d. Continuous learning | ✅ FULLY IMPLEMENTED | [retraining_service.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/services/retraining_service.py) has full pipeline: feedback count → retrain → F1 comparison → promote/reject. Threshold=200 in config. |
| 10d. Retraining widget | ❌ NOT IMPLEMENTED | No retraining status widget on admin dashboard (retrain button exists but no progress/status display). |

> **Action**: Add Ollama zero-shot fallback, short/empty text guards, retraining status widget.

---

### FEATURE 11 — Ollama Integration Layer

| Sub-feature | Status | Notes |
|---|---|---|
| 11a. OllamaProvider class | ❌ NOT IMPLEMENTED | [llm_service.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/services/llm_service.py) has Ollama calls but not abstracted into a clean provider class with typed methods. |
| 11b. Config | ✅ FULLY IMPLEMENTED | `OLLAMA_MODEL` and `OLLAMA_URL` from [.env](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/.env). 30s timeout. |
| 11b. Retry logic | ❌ NOT IMPLEMENTED | No retry-on-timeout. Single attempt only. |
| 11c. Prompt templates | ❌ NOT IMPLEMENTED | Prompts hardcoded in [llm_service.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/services/llm_service.py). Not in separate template files. |

> **Action**: Create `OllamaProvider` abstraction, add retry logic, extract prompts to template files.

---

### FEATURE 12 — Department-Wise Assignment

| Sub-feature | Status | Notes |
|---|---|---|
| 12a. Agent registry | ✅ PARTIALLY | [UserDocument](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/models/user.py#69-96) has: `skills[]`, `current_load`, `max_load`, `is_active`. Missing: `department[]`, `expertise_tags[]`, `availability_status`. |
| 12b. Assignment algorithm | ❌ NOT IMPLEMENTED | Manual assignment via `/api/agents/{ticket_id}/assign` exists. No automatic algorithm. |
| 12c. Load balancing | ❌ NOT IMPLEMENTED | `current_load` field exists but no auto-increment/decrement. No auto-reassign on inactivity. |

> **Action**: Extend agent model, build auto-assignment, add load balancing.

---

### FEATURE 13 — Dashboard Pages

| Sub-feature | Status | Notes |
|---|---|---|
| `/admin/queue` | ❌ NOT IMPLEMENTED | No priority queue monitor page. |
| `/admin/simulation` | ❌ NOT IMPLEMENTED | No simulation mode page. |
| `/admin/security` | ❌ NOT IMPLEMENTED | No security threat feed page. |
| Latency panel widget | ❌ NOT IMPLEMENTED | |
| Retraining status widget | ❌ NOT IMPLEMENTED | |
| Agent workload panel | ❌ PARTIALLY | `/api/agents/workload` endpoint exists. No widget on admin dashboard. |
| Security threat badge | ❌ NOT IMPLEMENTED | |

---

## Implementation Plan

### Items That Already Exist and Will NOT Be Touched

- Category classification (Logistic Regression + TF-IDF)
- Priority classification (Random Forest + TF-IDF)
- Confidence formula (0.5×model + 0.35×sim + 0.15×keyword)
- Three-tier routing (AUTO_RESOLVE / SUGGEST_TO_AGENT / ESCALATE_TO_HUMAN)
- HITL approve/edit/reject/escalate feedback flow
- Ollama RAG response generation with hallucination detection
- Sentence transformer embedding service
- ChromaDB retrieval service
- SLA prediction and deadline tracking
- Continuous learning / retraining pipeline (F1-based promotion)
- WebSocket connection manager
- All existing frontend pages, layouts, and styles
- All existing MongoDB collections, indexes, and schemas
- All existing API routes and their behavior

### Items That Are Partial and Will Be Extended

- [llm_service.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/services/llm_service.py) → add retry logic, extract to OllamaProvider (existing code preserved)
- [ticket.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/models/ticket.py) model → add `time_sensitivity`, `department`, `threat_analysis` fields
- [user.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/models/user.py) model → add `department[]`, `expertise_tags[]`, `availability_status`
- [tickets.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/routers/tickets.py) router → parallelize pipeline, add per-stage timing
- [config.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/core/config.py) → add new env vars (concurrency limit, department config, etc.)
- [.env](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/.env) → add new configuration values
- [database.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/core/database.py) → add new collection accessors
- [AdminPanel.jsx](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/frontend/src/pages/AdminPanel.jsx) → add new widget sections (no restructuring)
- [App.jsx](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/frontend/src/App.jsx) → add new routes for `/admin/queue`, `/admin/security`, `/admin/simulation`
- [api.js](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/frontend/src/services/api.js) → add new API helpers for new endpoints

### Items That Need To Be Implemented From Scratch

- Time sensitivity classification service
- Ollama zero-shot fallback for classification
- Security threat detection service
- Disguised attack pre-filter
- Escalation chain with APScheduler
- Response playbooks and post-incident form
- Department routing service
- Agent auto-assignment algorithm
- Priority queue (asyncio + heapq)
- LRU caching layer
- Performance logging service
- Regex safety guardrails service
- OllamaProvider abstraction class
- Prompt template files
- Frontend: `/admin/queue`, `/admin/security`, `/admin/simulation` pages
- Frontend: HITL UI enhancements (keyboard shortcuts, SLA countdown)
- Admin dashboard widgets (latency, retraining status, workload, security badge)

---

## Proposed Changes

### Phase 1 — Core ML Pipeline Gaps

#### Ollama Integration

##### [NEW] [ollama_provider.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/services/ollama_provider.py)
Clean abstraction layer: [generate()](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/utils/helpers.py#12-15), `classify_zero_shot()`, `analyze_threat()`, [generate_response()](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/services/llm_service.py#135-209). 30s timeout, 2 retries on timeout. Fallback when unreachable.

##### [NEW] Prompt templates directory `backend/prompts/`
- `rag_response.txt` — extracted from [llm_service.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/services/llm_service.py)
- `knowledge_article.txt` — extracted from [llm_service.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/services/llm_service.py)
- `root_cause.txt` — extracted from [llm_service.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/services/llm_service.py)
- `zero_shot_category.txt` — new prompt for classification fallback
- `threat_analysis.txt` — new prompt for security analysis

##### [MODIFY] [llm_service.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/services/llm_service.py)
Refactor to use `OllamaProvider` internally. Keep all existing method signatures. Add retry logic. Load prompts from template files.

---

#### Time Sensitivity & Safety

##### [NEW] [time_sensitivity_service.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/services/time_sensitivity_service.py)
Rules: CRITICAL+SECURITY → IMMEDIATE, HIGH+TECHNICAL → SAME_DAY, LOW+FEATURE_REQUEST → STANDARD, others computed from urgency keyword density.

##### [NEW] [safety_guardrails_service.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/services/safety_guardrails_service.py)
Regex checks for card numbers, SSN, passwords/API keys. Returns sanitized response or escalation flag. SHA256 hash of responses.

##### [MODIFY] [ticket.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/models/ticket.py)
Add `time_sensitivity` field to [AIAnalysis](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/models/ticket.py#93-142). Add `threat_analysis` sub-model. Add `department` field.

##### [MODIFY] [tickets.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/routers/tickets.py)
Integrate time sensitivity after classification. Add safety guardrails check before storing auto-resolved response. Parallelize classify + retrieve with `asyncio.gather()`. Add per-stage timing.

##### [MODIFY] [config.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/core/config.py)
Add: `BILLING_AUTO_RESOLVE_THRESHOLD=0.92`, `MAX_CONCURRENT_PIPELINES=20`, department taxonomy config.

##### [MODIFY] [.env](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/.env)
Add new env vars for pipeline concurrency, department config, etc.

---

### Phase 2 — Security Layer

##### [NEW] [security_threat_service.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/services/security_threat_service.py)
Stage 1: category check. Stage 2: Ollama threat analysis (phishing, social engineering, credential harvesting, etc.). Disguised attack pre-filter (URL detection, suspicious phrases). Returns structured JSON with threat_detected, threat_type, confidence, recommended_action.

##### [NEW] [escalation_service.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/services/escalation_service.py)
Timed escalation: L1 (Security Agent) → L2 (15 min, Team Lead) → L3 (30 min, Admin). APScheduler jobs. In-app alerts via WebSocket.

##### [NEW] [security.py router](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/routers/security.py)
Endpoints: GET /api/security/threats, GET /api/security/stats, POST /api/security/playbook/{ticket_id}, POST /api/security/incident-report/{ticket_id}.

##### [MODIFY] [database.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/core/database.py)
Add: `get_security_threats_collection()`, `get_escalation_logs_collection()`, `get_incident_reports_collection()`, `get_performance_logs_collection()`.

##### [MODIFY] [main.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/main.py)
Register new security router. Add escalation timer APScheduler jobs.

---

### Phase 3 — Routing & Assignment

##### [NEW] [department_service.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/services/department_service.py)
Department taxonomy: NETWORK, SOFTWARE, DATABASE, SECURITY, BILLING, HR_FACILITIES. Category → department mapping. Keyword-boosted scoring. Cross-department tagging.

##### [NEW] [assignment_service.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/services/assignment_service.py)
Auto-assignment: filter by department + ONLINE → lowest load → expertise match → fallback to department lead. Real-time load tracking (increment on assign, decrement on resolve).

##### [MODIFY] [user.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/models/user.py)
Add fields: `department: List[str]`, `expertise_tags: List[str]`, `availability_status: str`.

##### [MODIFY] [agents.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/routers/agents.py)
Add auto-assignment endpoint. Add agent availability status update endpoint.

---

### Phase 4 — New Frontend Pages

##### [NEW] [AdminQueueMonitor.jsx](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/frontend/src/pages/AdminQueueMonitor.jsx)
Priority queue monitor: live queue depth (waiting/processing/completed), processing rate, avg wait time per priority, CRITICAL alert if waiting >5 min.

##### [NEW] [AdminSecurity.jsx](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/frontend/src/pages/AdminSecurity.jsx)
Threat feed, threat type pie chart, false positive rate tracker, attack timeline.

##### [NEW] [AdminSimulation.jsx](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/frontend/src/pages/AdminSimulation.jsx)
Ticket generator, real-time pipeline visualization via WebSocket, controls (start/pause/stop, speed multiplier), end-of-simulation report.

##### [MODIFY] [App.jsx](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/frontend/src/App.jsx)
Add routes: `/admin/queue`, `/admin/security`, `/admin/simulation`.

##### [MODIFY] [api.js](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/frontend/src/services/api.js)
Add API helpers: `securityAPI`, `queueAPI`, `simulationAPI`.

##### [MODIFY] [Sidebar.jsx](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/frontend/src/components/Sidebar.jsx)
Add navigation links for new admin pages. Add security threat count badge.

##### [MODIFY] [AdminPanel.jsx](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/frontend/src/pages/AdminPanel.jsx)
Add new widget sections (no restructuring of existing layout): latency panel, retraining status progress bar, agent workload summary, security threat badge.

---

### Phase 5 — Optimization & Learning

##### [NEW] [cache_service.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/services/cache_service.py)
LRU caching via `cachetools`: TF-IDF vectors (TTL 1hr), top-k similarity (TTL 30min), Ollama responses (SHA256 key, TTL 1hr).

##### [NEW] [performance_service.py](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/services/performance_service.py)
Per-ticket timing: preprocessing_ms, classification_ms, similarity_ms, routing_ms, total_ms. Store in `performance_logs` collection. Endpoints for p50/p95/p99 over last 24 hours.

##### [NEW] [queue.py router](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/routers/queue.py)
Endpoints: GET /api/queue/status (depth, rate, wait times), WebSocket /ws/queue for live updates.

##### [NEW] [simulation.py router](file:///c:/Users/Amey/OneDrive/Desktop/TicketFlow-AI/backend/routers/simulation.py)
Endpoints: POST /api/simulation/start, POST /api/simulation/stop, GET /api/simulation/status. WebSocket /ws/simulation for live feed.

---

## Verification Plan

### Automated Tests

No existing test suite was found. New pytest tests will be created for every new endpoint:

```bash
# From backend/ directory:
cd c:\Users\Amey\OneDrive\Desktop\TicketFlow-AI\backend
python -m pytest tests/ -v
```

Tests to create in `backend/tests/`:
- `test_time_sensitivity.py` — unit tests for time sensitivity classification rules
- `test_safety_guardrails.py` — regex pattern matching tests (card numbers, SSN, passwords)
- `test_ollama_provider.py` — mock Ollama API tests (retry, timeout, fallback)
- `test_security_threat.py` — threat detection pipeline tests
- `test_department_routing.py` — department mapping and assignment tests
- `test_priority_queue.py` — queue ordering tests (CRITICAL > HIGH > MEDIUM > LOW)
- `test_cache_service.py` — cache hit/miss and TTL tests

### Existing Endpoint Regression

After every phase, verify existing endpoints still work:
```bash
# Start the backend server
cd c:\Users\Amey\OneDrive\Desktop\TicketFlow-AI\backend
python -m uvicorn main:app --reload --port 8000

# Test health endpoint
curl http://localhost:8000/health

# Test ticket submission (no auth required)
curl -X POST http://localhost:8000/api/tickets/ \
  -H "Content-Type: application/json" \
  -d '{"subject":"Test ticket","description":"This is a test ticket to verify the pipeline still works correctly after changes"}'
```

### Manual Verification

> [!IMPORTANT]
> The following manual tests require MongoDB, ChromaDB, and optionally Ollama to be running. Please confirm your local setup before testing.

1. **Frontend Smoke Test**: Start frontend with `npm start` from `frontend/`, verify all existing pages load without errors
2. **New Pages Test**: Navigate to `/admin/queue`, `/admin/security`, `/admin/simulation` — verify they render
3. **Ticket Pipeline**: Submit a ticket via the UI, verify it gets classified with time sensitivity and threat analysis
4. **Security Threat**: Submit a ticket mentioning "phishing" or "unauthorized access" — verify it gets threat-analyzed
5. **Admin Dashboard Widgets**: Navigate to admin panel — verify new widgets (latency, retraining status, workload) appear
