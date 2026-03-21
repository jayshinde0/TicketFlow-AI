# 🤖 TicketFlow AI - Machine Learning Models Summary

## 📊 Overview

TicketFlow AI uses **3 specialized ML models** for ticket classification and prediction, plus **1 LLM** for response generation.

---

## 🎯 Model 1: Category Classifier

### Algorithm
**Logistic Regression (Multinomial)**

### Purpose
Classifies tickets into 10 categories based on ticket description

### Categories (10 classes)
1. Network
2. Authentication (Auth)
3. Software
4. Hardware
5. Access
6. Billing
7. Email
8. Security
9. Service Request
10. Database

### Configuration
```python
LogisticRegression(
    C=5.0,                    # Regularization (sharper probabilities)
    max_iter=2000,            # Maximum iterations
    class_weight="balanced",  # Handle class imbalance
    solver="lbfgs",           # Optimization algorithm
    multi_class="multinomial", # One-vs-rest classification
    random_state=42,
    n_jobs=-1                 # Use all CPU cores
)
```

### Features
- **TF-IDF vectors** from ticket text (title + description)
- **Vocabulary size**: ~5000-10000 terms
- **Feature engineering**: Text cleaning, lemmatization, stopword removal

### Performance Metrics
- **Accuracy**: ~87%
- **Macro F1-Score**: ~0.86
- **Training samples**: 5,000 (synthetic data)

### Key Characteristics
- **Explainable**: Uses LIME for feature importance
- **Fast inference**: <100ms per prediction
- **Confidence scores**: Probability distribution across all classes
- **Regularization**: C=5.0 gives sharper confidence scores than default

### Why Logistic Regression?
✅ Fast training and inference
✅ Probabilistic outputs (confidence scores)
✅ Interpretable coefficients
✅ Works well with TF-IDF features
✅ Handles multi-class classification efficiently

---

## ⚡ Model 2: Priority Classifier

### Algorithm
**Random Forest Classifier**

### Purpose
Predicts ticket priority level based on content and metadata

### Priority Levels (4 classes)
1. Low
2. Medium
3. High
4. Critical

### Configuration
```python
RandomForestClassifier(
    n_estimators=200,         # Number of decision trees
    class_weight="balanced",  # Handle class imbalance
    max_depth=10,             # Maximum tree depth
    min_samples_split=5,      # Min samples to split node
    min_samples_leaf=2,       # Min samples in leaf node
    random_state=42,
    n_jobs=-1                 # Parallel processing
)
```

### Features (Multi-modal)
1. **TF-IDF vectors** from ticket text
2. **User tier** (0=Free, 1=Basic, 2=Standard, 3=Enterprise)
3. **Submission hour** (0-23)
4. **Word count** (ticket length)
5. **Urgency keyword count** (urgent, critical, asap, etc.)
6. **Sentiment score** (0.0-1.0, higher = more negative)

### Performance Metrics
- **Accuracy**: ~84%
- **Macro F1-Score**: ~0.83
- **Training samples**: 5,000

### Business Rules
- **Security tickets**: Always forced to "Critical" (override)
- **Database tickets**: Typically "Critical" or "High"
- **Frustrated users**: Priority escalation

### Key Characteristics
- **Ensemble method**: 200 decision trees voting
- **Feature importance**: Shows which features drive predictions
- **Robust**: Handles missing features gracefully
- **Balanced**: Class weights handle imbalanced data

### Why Random Forest?
✅ Handles mixed feature types (text + numeric)
✅ Feature importance built-in
✅ Robust to outliers
✅ No feature scaling required
✅ Reduces overfitting through ensemble

---

## ⏰ Model 3: SLA Predictor

### Algorithm
**Random Forest Classifier (Binary)**

### Purpose
Predicts probability of SLA breach and estimates resolution time

### Classes (2)
- **0**: Will be resolved within SLA
- **1**: Will breach SLA deadline

### Configuration
```python
RandomForestClassifier(
    n_estimators=200,
    class_weight="balanced",
    max_depth=10,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1
)
```

### Features (11 total)
1. **Category** (one-hot encoded, 10 dimensions)
2. **Priority** (ordinal: 0=Low, 1=Medium, 2=High, 3=Critical)
3. **User tier** (ordinal: 0-3)
4. **Submission hour** (0-23)
5. **Submission day of week** (0-6)
6. **Word count**
7. **Urgency keyword count**
8. **Sentiment score** (0.0-1.0)
9. **Current queue length** (tickets in queue)
10. **Similar ticket avg resolution hours** (from ChromaDB)
11. **Is weekend** (binary)
12. **Is outside business hours** (binary)

### SLA Limits (minutes by category & priority)

| Category | Low | Medium | High | Critical |
|----------|-----|--------|------|----------|
| Network | 2880 | 480 | 120 | 30 |
| Auth | 1440 | 240 | 60 | 15 |
| Software | 4320 | 1440 | 240 | 60 |
| Hardware | 4320 | 1440 | 240 | 120 |
| Security | 30 | 30 | 30 | 5 |
| Database | 1440 | 240 | 60 | 5 |

### Output
- **Breach probability**: 0.0-1.0 (e.g., 0.75 = 75% chance of breach)
- **Estimated resolution time**: Hours (adjusted based on breach risk)

### Key Characteristics
- **Risk-based**: Predicts likelihood of missing deadline
- **Context-aware**: Considers queue length and historical data
- **Time-sensitive**: Factors in submission time and day
- **Proactive**: Enables early escalation for at-risk tickets

### Why Random Forest?
✅ Handles complex feature interactions
✅ Works with mixed data types
✅ Probability calibration for risk assessment
✅ Feature importance for understanding delays

---

## 🧠 Model 4: Response Generator (LLM)

### Algorithm
**Mistral-Nemo (7B parameters)**

### Purpose
Generates personalized resolution responses using RAG (Retrieval-Augmented Generation)

### Architecture
**RAG Pipeline:**
1. **Embedding**: Convert ticket to vector (sentence-transformers)
2. **Retrieval**: Search ChromaDB for top 3 similar KB articles
3. **Context Building**: Combine retrieved articles
4. **Generation**: Mistral-Nemo generates response with context
5. **Post-processing**: Format and validate response

### Configuration
```python
# Ollama API
model: "mistral-nemo"
temperature: 0.3        # Low for consistent responses
max_tokens: 500         # Response length limit
top_p: 0.9             # Nucleus sampling
```

### Embedding Model
**sentence-transformers/all-MiniLM-L6-v2**
- 384-dimensional embeddings
- Optimized for semantic similarity
- Fast inference (~50ms)

### Vector Database
**ChromaDB**
- Stores KB article embeddings
- Cosine similarity search
- Persistent storage

### Key Characteristics
- **Context-aware**: Uses relevant KB articles
- **Personalized**: Includes user details in response
- **Structured**: Step-by-step resolution format
- **Fast**: ~2-3 seconds end-to-end

### Why Mistral-Nemo?
✅ Open-source (runs locally via Ollama)
✅ 7B parameters (good quality, reasonable speed)
✅ Instruction-tuned for task following
✅ No API costs or data privacy concerns
✅ Supports long context (8K tokens)

---

## 📈 Model Training Pipeline

### Data Generation
```python
# Synthetic data generation
python ml/data_loader.py
# Creates 5,000 samples (500 per category)
```

### Training
```python
# Train all models
python ml/train.py

# Output:
# - ml/artifacts/category_model.pkl
# - ml/artifacts/priority_model.pkl
# - ml/artifacts/sla_model.pkl
# - ml/artifacts/tfidf_vectorizer.pkl
# - ml/artifacts/training_metrics_YYYYMMDD_HHMMSS.json
```

### Evaluation
```python
# Evaluate models
python ml/evaluate.py

# Metrics:
# - Confusion matrices
# - Per-class precision/recall/F1
# - Feature importance
# - Calibration curves
```

---

## 🔄 Continuous Learning

### Feedback Loop
1. **Agent reviews** AI predictions
2. **Approvals/rejections** stored in MongoDB
3. **Feedback accumulates** (target: 50+ samples)
4. **Accuracy monitoring** (threshold: 80%)
5. **Auto-retraining** triggered when accuracy drops

### Retraining Process
```python
# Automatic trigger
if accuracy < 0.80 and feedback_count >= 50:
    retrain_models()

# Manual trigger
POST /api/admin/retrain
```

### Model Versioning
- Timestamped artifacts: `training_metrics_20260321_112938.json`
- Previous models backed up
- Performance comparison across versions

---

## 🎯 Model Selection Rationale

### Why These Algorithms?

#### Logistic Regression (Category)
- **Interpretability**: Coefficients show feature importance
- **Speed**: Fast training and inference
- **Probabilistic**: Natural confidence scores
- **Proven**: Industry standard for text classification

#### Random Forest (Priority & SLA)
- **Versatility**: Handles mixed features (text + numeric)
- **Robustness**: Resistant to overfitting
- **Feature importance**: Built-in explainability
- **No preprocessing**: Works with raw features

#### Mistral-Nemo (Response)
- **Quality**: State-of-the-art language understanding
- **Privacy**: Runs locally (no data sent to cloud)
- **Cost**: Free (no API fees)
- **Control**: Full control over prompts and outputs

---

## 📊 Performance Comparison

| Model | Algorithm | Accuracy | F1-Score | Inference Time | Training Time |
|-------|-----------|----------|----------|----------------|---------------|
| Category | Logistic Regression | 87% | 0.86 | <100ms | ~30s |
| Priority | Random Forest | 84% | 0.83 | <150ms | ~2min |
| SLA | Random Forest | 82% | 0.81 | <150ms | ~2min |
| Response | Mistral-Nemo | N/A | N/A | ~2-3s | Pre-trained |

---

## 🔧 Feature Engineering

### Text Features (TF-IDF)
```python
TfidfVectorizer(
    max_features=5000,      # Top 5000 terms
    ngram_range=(1, 2),     # Unigrams + bigrams
    min_df=2,               # Ignore rare terms
    max_df=0.8,             # Ignore common terms
    sublinear_tf=True       # Log scaling
)
```

### Preprocessing Pipeline
1. **Lowercase** conversion
2. **Remove** special characters
3. **Tokenization** (word-level)
4. **Lemmatization** (reduce to root form)
5. **Stopword removal** (common words)
6. **TF-IDF** vectorization

### Metadata Features
- **User tier**: Encoded as 0-3
- **Time features**: Hour, day of week, weekend flag
- **Text statistics**: Word count, sentence count
- **Sentiment**: TextBlob polarity score
- **Urgency**: Keyword matching (urgent, critical, asap, etc.)

---

## 🎓 Model Explainability

### LIME (Local Interpretable Model-agnostic Explanations)
- Explains individual predictions
- Shows which words influenced classification
- Highlights positive/negative contributions
- Used for category predictions

### Feature Importance
- Random Forest built-in importance scores
- Shows which features drive priority/SLA predictions
- Helps identify data quality issues

### Confidence Scores
- All models output probability distributions
- Confidence threshold: 85% for auto-resolve
- Low confidence triggers human review

---

## 🚀 Deployment

### Model Loading
```python
# Load at startup
category_clf = CategoryClassifier.load()
priority_clf = PriorityClassifier.load()
sla_predictor = SLAPredictor.load()

# Lazy loading for LLM
ollama_client = OllamaClient(base_url="http://localhost:11434")
```

### Inference Pipeline
```python
# 1. Preprocess text
cleaned_text = nlp_service.clean_text(ticket.description)

# 2. Extract features
features = feature_engineer.extract(cleaned_text, metadata)

# 3. Predict category
category, cat_conf, cat_probs = category_clf.predict(features)

# 4. Predict priority
priority, pri_conf = priority_clf.predict(features, category)

# 5. Predict SLA
breach_prob = sla_predictor.predict_breach_probability(features)
resolution_hours = sla_predictor.estimate_resolution_hours(
    category, priority, breach_prob
)

# 6. Generate response (if confidence high enough)
if cat_conf >= 0.85:
    response = llm_service.generate_response(ticket, category)
```

---

## 📚 Dependencies

### Core ML Libraries
```
scikit-learn==1.3.0      # ML algorithms
numpy==1.24.3            # Numerical computing
scipy==1.11.1            # Sparse matrices
joblib==1.3.1            # Model serialization
```

### NLP Libraries
```
nltk==3.8.1              # Text preprocessing
textblob==0.17.1         # Sentiment analysis
spacy==3.6.0             # Advanced NLP
```

### LLM & Embeddings
```
ollama-python==0.1.0     # Ollama client
chromadb==0.4.0          # Vector database
sentence-transformers==2.2.2  # Embeddings
```

### Explainability
```
lime==0.2.0.1            # Model explanations
shap==0.42.1             # Alternative explainability
```

---

## 🎯 Future Improvements

### Short-term
- [ ] Add XGBoost for priority classification (better accuracy)
- [ ] Implement BERT embeddings for category classification
- [ ] Add model ensemble (voting classifier)
- [ ] Hyperparameter tuning with Optuna

### Medium-term
- [ ] Fine-tune Mistral-Nemo on company-specific data
- [ ] Implement active learning (query uncertain samples)
- [ ] Add anomaly detection for unusual tickets
- [ ] Multi-label classification (tickets with multiple issues)

### Long-term
- [ ] Deploy models as microservices
- [ ] A/B testing framework for model comparison
- [ ] Real-time model updates (online learning)
- [ ] Custom transformer model for ticket classification

---

## 📖 References

### Papers
- **Logistic Regression**: "Regularization Paths for Generalized Linear Models via Coordinate Descent" (Friedman et al., 2010)
- **Random Forest**: "Random Forests" (Breiman, 2001)
- **LIME**: "Why Should I Trust You?" (Ribeiro et al., 2016)
- **RAG**: "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" (Lewis et al., 2020)

### Libraries
- scikit-learn: https://scikit-learn.org/
- Ollama: https://ollama.ai/
- ChromaDB: https://www.trychroma.com/
- LIME: https://github.com/marcotcr/lime

---

**Summary**: TicketFlow AI uses a hybrid approach combining traditional ML (Logistic Regression, Random Forest) for classification with modern LLMs (Mistral-Nemo) for response generation. This provides the best of both worlds: fast, interpretable predictions with high-quality natural language responses.
