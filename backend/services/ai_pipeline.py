"""
services/ai_pipeline.py — Modular AI Security Detection Pipeline.

5-step pipeline:
  Step 1: Preprocessing     — spaCy / NLTK via nlp_service
  Step 2: Embedding         — sentence-transformers (all-MiniLM-L6-v2)
  Step 3: ML Classification — scikit-learn (Logistic Regression / RandomForest)
  Step 4: Sentiment/Anomaly — RoBERTa (cardiffnlp) keyword fallback
  Step 5: Security Rule Engine — SQL injection, XSS, brute force, DDoS, etc.

Hidden Attack Detection:
  IF ML says "normal" BUT security keywords OR anomaly detected
  THEN reclassify as "suspicious"

Auto Escalation:
  attack   → priority=HIGH, route to SECURITY ADMIN, disable auto-resolve
  suspicious → manual review
  normal   → continue auto-resolution
"""

import asyncio
import time
from typing import Dict, Any, Optional
from loguru import logger

from services.nlp_service import nlp_service
from services.embedding_service import embedding_service
from services.classifier_service import classifier_service
from services.sentiment_service import sentiment_service
from services.rule_engine import rule_engine


# ─── ChromaDB attack similarity check ────────────────────────────────

async def _check_attack_similarity(text: str, threshold: float = 0.75) -> Dict[str, Any]:
    """
    Compare new ticket embedding against stored past attack embeddings in ChromaDB.
    Returns similarity score and whether it exceeds the threshold.
    """
    try:
        import chromadb
        from core.config import settings

        client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
        )
        # Use or create a dedicated attack patterns collection
        try:
            collection = client.get_collection("security_attacks")
        except Exception:
            collection = client.get_or_create_collection("security_attacks")

        count = collection.count()
        if count == 0:
            return {"similar_attack_found": False, "similarity_score": 0.0, "similar_count": 0}

        embedding = await embedding_service.embed_async(text)
        results = collection.query(
            query_embeddings=[embedding.tolist()],
            n_results=min(3, count),
            include=["distances", "metadatas"],
        )

        distances = results.get("distances", [[]])[0]
        # ChromaDB returns L2 distances; convert to cosine-like similarity
        similarities = [max(0.0, 1.0 - d) for d in distances]
        max_sim = max(similarities) if similarities else 0.0

        return {
            "similar_attack_found": max_sim >= threshold,
            "similarity_score": round(max_sim, 4),
            "similar_count": len([s for s in similarities if s >= threshold]),
        }
    except Exception as e:
        logger.debug(f"ChromaDB attack similarity check skipped: {e}")
        return {"similar_attack_found": False, "similarity_score": 0.0, "similar_count": 0}


async def store_attack_embedding(ticket_id: str, text: str, threat_type: str) -> None:
    """
    Store the embedding of a confirmed attack ticket in ChromaDB
    so future tickets can be compared against it.
    """
    try:
        import chromadb
        from core.config import settings

        client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
        )
        collection = client.get_or_create_collection("security_attacks")
        embedding = await embedding_service.embed_async(text)
        collection.upsert(
            ids=[ticket_id],
            embeddings=[embedding.tolist()],
            metadatas=[{"ticket_id": ticket_id, "threat_type": threat_type}],
        )
        logger.info(f"Attack embedding stored for {ticket_id} (type={threat_type})")
    except Exception as e:
        logger.debug(f"Failed to store attack embedding (non-fatal): {e}")


# ─── Redis caching for attack patterns ───────────────────────────────

async def _get_cached_result(cache_key: str) -> Optional[Dict]:
    """Try to get a cached security analysis result from Redis/in-memory cache."""
    try:
        from services.cache_service import cache_service
        # Use the LLM cache slot for generic security pipeline results
        return cache_service.get_llm_response(cache_key)
    except Exception:
        return None


async def _cache_result(cache_key: str, result: Dict, ttl: int = 300) -> None:
    """Cache a security analysis result using the in-memory LLM cache slot."""
    try:
        import json
        from services.cache_service import cache_service
        # Serialize to string for the string-typed LLM cache
        cache_service.set_llm_response(cache_key, json.dumps(result, default=str))
    except Exception:
        pass


# ─── Main Pipeline ────────────────────────────────────────────────────

class SecurityAIPipeline:
    """
    Modular 5-step AI security detection pipeline.

    Produces:
        threat_level:    normal | suspicious | attack
        threat_type:     sql_injection | xss | brute_force | unauthorized_access | ddos | none
        confidence_score: 0.0 – 1.0
        detection_reason: human-readable explanation
        triggered_rules:  list of rule names that fired
        auto_escalate:    bool — should this ticket be escalated immediately?
        safe_response:    pre-built response for attack tickets
        stage_timings:    per-step timing breakdown (ms)
    """

    SAFE_RESPONSE_ATTACK = (
        "This issue has been flagged as a potential security threat and escalated "
        "to the security team. Our security specialists will review and respond "
        "within the defined SLA. Please do not attempt to reproduce the issue."
    )

    SAFE_RESPONSE_SUSPICIOUS = (
        "Your ticket has been flagged for manual security review. A member of our "
        "team will assess and respond shortly."
    )

    async def run(
        self,
        ticket_id: str,
        subject: str,
        description: str,
        ml_category: str = "Software",
        ml_confidence: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Run the full 5-step security pipeline on a ticket.

        Args:
            ticket_id:      Ticket identifier (for logging/caching).
            subject:        Ticket subject line.
            description:    Ticket description body.
            ml_category:    Category predicted by the main classifier.
            ml_confidence:  Confidence from the main classifier.

        Returns:
            Complete security analysis dict.
        """
        start = time.time()
        stage_timings: Dict[str, int] = {}
        combined_text = f"{subject}. {description}"

        # ── Cache check ───────────────────────────────────────────────
        import hashlib
        import json as _json
        cache_key = f"sec_pipeline:{hashlib.md5(combined_text.encode()).hexdigest()}"
        cached_raw = await _get_cached_result(cache_key)
        if cached_raw:
            try:
                cached = _json.loads(cached_raw) if isinstance(cached_raw, str) else cached_raw
                logger.debug(f"Security pipeline cache hit for {ticket_id}")
                return cached
            except Exception:
                pass  # corrupted cache entry — recompute

        # ── Step 1: Preprocessing ─────────────────────────────────────
        t0 = time.time()
        nlp_result = await nlp_service.preprocess_async(combined_text)
        cleaned_text = nlp_result["cleaned_text"]
        stage_timings["preprocessing_ms"] = int((time.time() - t0) * 1000)

        # ── Step 2: Embedding ─────────────────────────────────────────
        t0 = time.time()
        try:
            _embedding = await asyncio.wait_for(
                embedding_service.embed_async(cleaned_text), timeout=10.0
            )
        except Exception as e:
            logger.debug(f"Embedding step skipped: {e}")
            _embedding = None
        stage_timings["embedding_ms"] = int((time.time() - t0) * 1000)

        # ── Step 3: ML Classification (security-specific) ─────────────
        # We re-use the existing classifier but interpret the result
        # through a security lens (is it Security category? high confidence?)
        t0 = time.time()
        ml_threat_level = "normal"
        if ml_category == "Security":
            ml_threat_level = "suspicious"  # Security category → at least suspicious
        if ml_category == "Security" and ml_confidence >= 0.80:
            ml_threat_level = "attack"
        stage_timings["ml_classification_ms"] = int((time.time() - t0) * 1000)

        # ── Step 4: Sentiment / Anomaly Check ─────────────────────────
        t0 = time.time()
        try:
            sentiment_result = await asyncio.wait_for(
                sentiment_service.analyze_async(combined_text), timeout=8.0
            )
        except Exception:
            sentiment_result = {"sentiment_label": "NEUTRAL", "sentiment_score": 0.5, "is_frustrated": False}

        # Anomaly: very negative + security-adjacent text → suspicious
        anomaly_detected = (
            sentiment_result["sentiment_label"] == "NEGATIVE"
            and sentiment_result["sentiment_score"] > 0.80
        )
        stage_timings["sentiment_anomaly_ms"] = int((time.time() - t0) * 1000)

        # ── Step 5: Security Rule Engine ──────────────────────────────
        t0 = time.time()
        rule_result = rule_engine.evaluate(combined_text, ml_threat_level)
        stage_timings["rule_engine_ms"] = int((time.time() - t0) * 1000)

        # ── Hidden Attack Detection ───────────────────────────────────
        # IF ML says "normal" BUT anomaly detected → reclassify as suspicious
        threat_level = rule_result["threat_level"]
        if threat_level == "normal" and anomaly_detected:
            threat_level = "suspicious"
            if rule_result["threat_type"] == "none":
                rule_result["threat_type"] = "unauthorized_access"
            rule_result["triggered_rules"].append("anomaly_detected")
            rule_result["detection_reason"] += " Anomalous sentiment pattern detected."

        # ── ChromaDB similarity boost ─────────────────────────────────
        t0 = time.time()
        chroma_result = await _check_attack_similarity(combined_text)
        stage_timings["chroma_similarity_ms"] = int((time.time() - t0) * 1000)

        if chroma_result["similar_attack_found"]:
            # Boost threat level if similar to past attacks
            if threat_level == "normal":
                threat_level = "suspicious"
            elif threat_level == "suspicious":
                threat_level = "attack"
            rule_result["triggered_rules"].append("similar_to_past_attack")
            rule_result["detection_reason"] += (
                f" Similar to {chroma_result['similar_count']} past attack(s) "
                f"(score={chroma_result['similarity_score']:.2f})."
            )

        # ── Compute final confidence score ────────────────────────────
        base_confidence = ml_confidence
        if rule_result["triggered_rules"]:
            base_confidence = min(1.0, base_confidence + rule_result["confidence_boost"])
        if chroma_result["similar_attack_found"]:
            base_confidence = min(1.0, base_confidence + chroma_result["similarity_score"] * 0.2)
        confidence_score = round(base_confidence, 4)

        # ── Auto escalation logic ─────────────────────────────────────
        auto_escalate = threat_level == "attack"
        disable_auto_resolve = threat_level in ("attack", "suspicious")

        # Determine safe response
        if threat_level == "attack":
            safe_response = self.SAFE_RESPONSE_ATTACK
        elif threat_level == "suspicious":
            safe_response = self.SAFE_RESPONSE_SUSPICIOUS
        else:
            safe_response = None

        # ── Build result ──────────────────────────────────────────────
        total_ms = int((time.time() - start) * 1000)
        stage_timings["total_ms"] = total_ms

        result = {
            # Core threat metadata
            "threat_level": threat_level,
            "threat_type": rule_result["threat_type"],
            "confidence_score": confidence_score,
            "detection_reason": rule_result["detection_reason"],
            "triggered_rules": rule_result["triggered_rules"],
            "matched_evidence": rule_result.get("matched_evidence", []),

            # Escalation
            "auto_escalate": auto_escalate,
            "disable_auto_resolve": disable_auto_resolve,
            "safe_response": safe_response,

            # Supporting data
            "anomaly_detected": anomaly_detected,
            "sentiment_label": sentiment_result["sentiment_label"],
            "chroma_similarity": chroma_result,
            "ml_category": ml_category,
            "ml_confidence": ml_confidence,

            # Timing
            "stage_timings": stage_timings,
        }

        # Cache result (5 min TTL — attack patterns don't change quickly)
        await _cache_result(cache_key, result, ttl=300)

        # Store attack embedding for future comparisons
        if threat_level == "attack":
            asyncio.create_task(
                store_attack_embedding(ticket_id, combined_text, rule_result["threat_type"])
            )

        logger.info(
            f"Security pipeline [{ticket_id}]: level={threat_level}, "
            f"type={rule_result['threat_type']}, "
            f"confidence={confidence_score:.3f}, time={total_ms}ms"
        )

        return result


# Module-level singleton
security_pipeline = SecurityAIPipeline()
