"""
routers/tickets.py — Core ticket CRUD and full AI pipeline endpoint.
POST /api/tickets/ runs all 5 AI agents in orchestrated sequence.
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from loguru import logger

from core.database import get_tickets_collection
from core.security import get_current_user, get_current_user_optional
from models.ticket import (
    TicketCreate,
    TicketListResponse,
    TicketListItem,
    TicketResponse,
    TicketSubmitResponse,
    TicketStatusUpdate,
    TicketStatus,
    TicketMetadata,
    AIAnalysis,
    ResolutionData,
)
from services.nlp_service import nlp_service
from services.classifier_service import classifier_service
from services.hybrid_classifier_service import (
    enhanced_hybrid_classifier,
)  # NEW: Hybrid classifier
from services.embedding_service import embedding_service
from services.retrieval_service import retrieval_service
from services.sentiment_service import sentiment_service
from services.sla_service import sla_service
from services.confidence_service import confidence_service
from services.hitl_service import hitl_service
from services.llm_service import llm_service
from services.duplicate_service import duplicate_service
from services.explainability_service import explainability_service
from services.audit_service import audit_service
from services.notification_service import notification_service
from services.time_sensitivity_service import time_sensitivity_service
from services.safety_guardrails_service import safety_guardrails_service
from services.llm_provider_factory import llm_provider as ollama_provider
from services.nlp_cache import nlp_cache
from services.security_threat_service import security_threat_service
from services.escalation_service import escalation_service
from services.ai_pipeline import security_pipeline
from services.journey_service import journey_service  # NEW: Journey tracking
from services.text_validation_service import text_validation_service  # NEW: Gibberish detection
from utils.helpers import generate_ticket_id, utcnow, paginate, tier_to_int
from utils.text_cleaner import count_urgency_keywords
from core.config import settings
from ml.data_loader import ALL_CATEGORIES

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])


async def run_ai_pipeline(
    ticket_id: str,
    subject: str,
    description: str,
    user_tier: str = "Standard",
    now: Optional[datetime] = None,
) -> dict:
    """
    Wave-based concurrent AI pipeline for ticket processing.

    Execution waves:
    - Wave 0 (validation): Text quality and gibberish detection
    - Wave 1 (parallel): NLP preprocessing + Sentiment analysis
    - Wave 2 (sequential): Hybrid classification + optional zero-shot fallback
    - Wave 3 (parallel): Retrieval + Security pipeline + LIME + Duplicate + Legacy threat
    - Wave 4 (sequential): SLA prediction
    - Wave 5 (sequential): Time sensitivity + HITL routing
    - Wave 6 (sequential): LLM response generation
    - Wave 7 (sequential): Safety guardrails
    - Wave 8 (fire-and-forget): Audit logging

    Returns:
        Complete AI analysis dict ready for MongoDB storage.
    """
    start_time = time.time()
    stage_timings = {}  # per-stage timing breakdown
    zero_shot_used = False
    hybrid_override_used = False  # Track hybrid classifier usage
    # Security pipeline result defaults (populated later in pipeline)
    threat_level = "normal"
    threat_type_new = "none"
    threat_confidence = 0.0
    triggered_rules = []
    detection_reason = ""
    if now is None:
        now = utcnow()

    combined_text = f"{subject}. {description}"

    # ═══════════════════════════════════════════════════════════════════
    # WAVE 0: Input Validation (gibberish detection)
    # ═══════════════════════════════════════════════════════════════════
    is_valid, validation_error = text_validation_service.validate(
        combined_text, min_words=3
    )
    if not is_valid:
        logger.warning(
            f"Ticket {ticket_id} failed validation: {validation_error}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_error
        )

    # ═══════════════════════════════════════════════════════════════════
    # WAVE 1: NLP + Sentiment in parallel (both only need combined_text)
    # ═══════════════════════════════════════════════════════════════════
    t_wave1 = time.time()

    async def _run_nlp():
        t0 = time.time()
        result = await nlp_cache.get(combined_text)
        if result is None:
            result = await nlp_service.preprocess_async(combined_text)
            await nlp_cache.set(combined_text, result)
        else:
            logger.debug(f"NLP cache hit for {ticket_id} — skipped spaCy processing")
        stage_timings["preprocessing_ms"] = int((time.time() - t0) * 1000)
        return result

    async def _run_sentiment():
        t0 = time.time()
        try:
            result = await asyncio.wait_for(
                sentiment_service.analyze_async(combined_text), timeout=8.0
            )
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Sentiment service timeout/error: {e}. Using neutral fallback.")
            result = {
                "sentiment_label": "NEUTRAL",
                "sentiment_score": 0.5,
                "is_frustrated": False,
            }
        stage_timings["sentiment_ms"] = int((time.time() - t0) * 1000)
        return result

    nlp_result, sentiment_result = await asyncio.gather(
        _run_nlp(),
        _run_sentiment(),
        return_exceptions=True,
    )

    # Handle exceptions from gather
    if isinstance(nlp_result, Exception):
        logger.warning(f"NLP failed: {nlp_result}. Using fallback.")
        nlp_result = {
            "cleaned_text": combined_text.lower(),
            "language": "en",
            "is_english": True,
            "features": {
                "word_count": len(combined_text.split()),
                "urgency_keyword_count": 0,
            },
            "original_cleaned": combined_text,
        }
        stage_timings["preprocessing_ms"] = 0

    if isinstance(sentiment_result, Exception):
        logger.warning(f"Sentiment failed: {sentiment_result}. Using neutral fallback.")
        sentiment_result = {
            "sentiment_label": "NEUTRAL",
            "sentiment_score": 0.5,
            "is_frustrated": False,
        }
        stage_timings["sentiment_ms"] = 0

    stage_timings["wave1_ms"] = int((time.time() - t_wave1) * 1000)

    # Unpack NLP
    cleaned_text = nlp_result["cleaned_text"]
    features = nlp_result["features"]
    word_count = features["word_count"]
    urgency_count = features["urgency_keyword_count"]

    # Unpack sentiment
    sentiment_label = sentiment_result["sentiment_label"]
    sentiment_score = sentiment_result["sentiment_score"]
    is_frustrated = sentiment_result["is_frustrated"]

    # ═══════════════════════════════════════════════════════════════════
    # WAVE 2: Classification (depends on cleaned_text + sentiment_score)
    # ═══════════════════════════════════════════════════════════════════
    t_wave2 = time.time()
    classify_result = await enhanced_hybrid_classifier.classify(
        cleaned_text=cleaned_text,
        user_tier=user_tier,
        submission_hour=now.hour,
        word_count=word_count,
        urgency_keyword_count=urgency_count,
        sentiment_score=sentiment_score,
    )

    category = classify_result["category"]
    model_confidence = classify_result["model_confidence"]
    category_probs = classify_result["category_probabilities"]
    priority = classify_result["priority"]
    priority_confidence = classify_result["priority_confidence"]
    hybrid_override_used = classify_result.get("hybrid_override", False)

    stage_timings["classification_ms"] = int((time.time() - t_wave2) * 1000)
    stage_timings["wave2_ms"] = stage_timings["classification_ms"]

    # ─── Zero-shot fallback for low confidence (<0.55) ────────────────
    if model_confidence < 0.55:
        logger.info(
            f"Low ML confidence ({model_confidence:.2f}) — attempting Ollama zero-shot fallback"
        )
        try:
            zs_result = await asyncio.wait_for(
                ollama_provider.classify_zero_shot(combined_text, ALL_CATEGORIES),
                timeout=15.0,
            )
            # Only override if zero-shot is SIGNIFICANTLY better
            if zs_result and zs_result.get("confidence", 0) > model_confidence + 0.15:
                category = zs_result["category"]
                model_confidence = zs_result["confidence"]
                zero_shot_used = True
                logger.info(
                    f"Zero-shot override: category={category}, confidence={model_confidence:.2f}"
                )
        except Exception as e:
            logger.warning(f"Zero-shot fallback failed (non-fatal): {e}")

    # record zero-shot time separately if it ran
    stage_timings["zero_shot_ms"] = int((time.time() - t_wave2) * 1000) - stage_timings["wave2_ms"]

    # ═══════════════════════════════════════════════════════════════════
    # WAVE 3: Retrieval + Security + LIME + Duplicate + Legacy threat
    #         (all independent, run concurrently)
    # ═══════════════════════════════════════════════════════════════════
    t_wave3 = time.time()

    async def _run_retrieval():
        t0 = time.time()
        try:
            result = await asyncio.wait_for(
                retrieval_service.find_similar_tickets(
                    text=cleaned_text, category=category, top_k=3,
                ),
                timeout=15.0,
            )
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Retrieval service timeout/error: {e}. Using empty fallback.")
            result = {
                "similar_tickets": [],
                "top_similarity_score": 0.0,
                "embedding": None,
                "knowledge_base_size": 0,
            }
        stage_timings["retrieval_ms"] = int((time.time() - t0) * 1000)
        return result

    async def _run_security():
        t0 = time.time()
        result = await security_pipeline.run(
            ticket_id=ticket_id,
            subject=subject,
            description=description,
            ml_category=category,
            ml_confidence=model_confidence,
            precomputed_nlp=nlp_result,
            precomputed_sentiment=sentiment_result,
        )
        stage_timings["security_pipeline_ms"] = int((time.time() - t0) * 1000)
        return result

    async def _run_lime():
        t0 = time.time()
        try:
            result = await explainability_service.explain_async(
                cleaned_text=cleaned_text,
                classifier_service=classifier_service,
                num_features=8,
                num_samples=200,
            )
        except Exception as e:
            logger.debug(f"LIME explanation skipped: {e}")
            result = None
        stage_timings["lime_explainability_ms"] = int((time.time() - t0) * 1000)
        return result

    async def _run_duplicate():
        t0 = time.time()
        result = await duplicate_service.check_duplicate(
            text=cleaned_text,
            new_ticket_id=ticket_id,
            category=category,
        )
        stage_timings["duplicate_detection_ms"] = int((time.time() - t0) * 1000)
        return result

    async def _run_legacy_threat():
        t0 = time.time()
        result = await security_threat_service.analyze_threat(
            text=combined_text,
            category=category,
        )
        stage_timings["legacy_threat_ms"] = int((time.time() - t0) * 1000)
        return result

    (
        retrieval_result,
        sec_pipeline_result,
        lime_result,
        duplicate_result,
        threat_result,
    ) = await asyncio.gather(
        _run_retrieval(),
        _run_security(),
        _run_lime(),
        _run_duplicate(),
        _run_legacy_threat(),
        return_exceptions=True,
    )

    # Handle exceptions from wave 3
    if isinstance(retrieval_result, Exception):
        logger.warning(f"Retrieval failed: {retrieval_result}")
        retrieval_result = {
            "similar_tickets": [],
            "top_similarity_score": 0.0,
            "embedding": None,
            "knowledge_base_size": 0,
        }

    if isinstance(sec_pipeline_result, Exception):
        logger.warning(f"Security pipeline failed: {sec_pipeline_result}")
        sec_pipeline_result = {
            "threat_level": "normal",
            "threat_type": "none",
            "confidence_score": 0.0,
            "triggered_rules": [],
            "detection_reason": "",
            "disable_auto_resolve": False,
            "safe_response": None,
            "auto_escalate": False,
        }

    if isinstance(lime_result, Exception):
        logger.debug(f"LIME failed in gather: {lime_result}")
        lime_result = None

    if isinstance(duplicate_result, Exception):
        logger.warning(f"Duplicate check failed: {duplicate_result}")
        duplicate_result = {
            "is_duplicate": False,
            "is_possible_duplicate": False,
            "parent_ticket_id": None,
            "similarity_score": 0.0,
        }

    if isinstance(threat_result, Exception):
        logger.warning(f"Legacy threat analysis failed: {threat_result}")
        threat_result = {
            "threat_detected": False,
            "severity": "none",
        }

    stage_timings["wave3_ms"] = int((time.time() - t_wave3) * 1000)
    # backward compat: combined threat timing
    stage_timings["threat_analysis_ms"] = (
        stage_timings.get("security_pipeline_ms", 0)
        + stage_timings.get("legacy_threat_ms", 0)
    )

    # Unpack retrieval
    similar_tickets = retrieval_result["similar_tickets"]
    top_similarity = retrieval_result["top_similarity_score"]
    ticket_embedding = retrieval_result.get("embedding")

    # Merge security: new pipeline takes precedence for threat_level/type
    threat_level = sec_pipeline_result["threat_level"]
    threat_type_new = sec_pipeline_result["threat_type"]
    threat_confidence = sec_pipeline_result["confidence_score"]
    triggered_rules = sec_pipeline_result["triggered_rules"]
    detection_reason = sec_pipeline_result["detection_reason"]

    # ═══════════════════════════════════════════════════════════════════
    # WAVE 4: SLA prediction (needs similar_tickets from wave 3)
    # ═══════════════════════════════════════════════════════════════════
    t_wave4 = time.time()
    similar_avg_resolution = (
        sum(t.get("resolution_time_hours", 2.0) for t in similar_tickets)
        / len(similar_tickets)
        if similar_tickets
        else 2.0
    )
    sla_breach_prob = sla_service.predict_breach_probability(
        category=category,
        priority=priority,
        user_tier=user_tier,
        submission_hour=now.hour,
        submission_day=now.weekday(),
        word_count=word_count,
        urgency_keyword_count=urgency_count,
        sentiment_score=sentiment_score,
        current_queue_length=10,  # would be real-time queue in production
        similar_ticket_avg_hours=similar_avg_resolution,
    )
    stage_timings["sla_prediction_ms"] = int((time.time() - t_wave4) * 1000)
    stage_timings["wave4_ms"] = stage_timings["sla_prediction_ms"]

    # ═══════════════════════════════════════════════════════════════════
    # WAVE 5: Time sensitivity + HITL routing (needs sla_breach_prob)
    # ═══════════════════════════════════════════════════════════════════
    t_wave5 = time.time()

    # Time sensitivity classification
    time_sensitivity = time_sensitivity_service.classify(
        category=category,
        priority=priority,
        text=combined_text,
        sla_breach_probability=sla_breach_prob,
    )

    # Department mapping
    department = settings.CATEGORY_TO_DEPARTMENT.get(category, "SOFTWARE")

    # HITL routing decision
    hitl_result = hitl_service.route(
        category=category,
        model_confidence=model_confidence,
        priority=priority,
        priority_confidence=priority_confidence,
        top_similarity_score=top_similarity,
        sentiment_label=sentiment_label,
        sentiment_score=sentiment_score,
        is_frustrated=is_frustrated,
        sla_breach_probability=sla_breach_prob,
        ticket_text=combined_text,
        user_tier=user_tier,
    )
    routing_decision = hitl_result["routing_decision"]
    confidence_score = hitl_result["confidence_score"]
    final_priority = hitl_result["priority"]
    stage_timings["hitl_routing_ms"] = int((time.time() - t_wave5) * 1000)
    stage_timings["wave5_ms"] = stage_timings["hitl_routing_ms"]

    # ── Apply security overrides to routing (must run after wave 3 + wave 5) ──
    if sec_pipeline_result.get("disable_auto_resolve"):
        if routing_decision == "AUTO_RESOLVE":
            routing_decision = "ESCALATE_TO_HUMAN"

    if threat_level == "attack":
        final_priority = "Critical"

    # ═══════════════════════════════════════════════════════════════════
    # WAVE 6: LLM generation (needs routing_decision + similar_tickets)
    # ═══════════════════════════════════════════════════════════════════
    t_wave6 = time.time()
    top_solution = (
        similar_tickets[0]["solution"]
        if similar_tickets
        else "Please contact support for assistance."
    )
    try:
        llm_result = await asyncio.wait_for(
            llm_service.generate_response(
                ticket_text=combined_text,
                category=category,
                retrieved_solution=top_solution,
                routing_decision=routing_decision,
            ),
            timeout=35.0,
        )
    except (asyncio.TimeoutError, Exception) as e:
        logger.warning(f"LLM service timeout/error: {e}. Using fallback response.")
        llm_result = {
            "generated_response": top_solution,
            "hallucination_detected": False,
            "fallback_used": True,
            "model_used": "fallback",
            "generation_time_ms": 0,
        }
    stage_timings["llm_generation_ms"] = int((time.time() - t_wave6) * 1000)
    stage_timings["wave6_ms"] = stage_timings["llm_generation_ms"]

    # ═══════════════════════════════════════════════════════════════════
    # WAVE 7: Safety guardrails (needs generated_response + routing_decision)
    # ═══════════════════════════════════════════════════════════════════
    t_wave7 = time.time()
    safety_result = {
        "is_safe": True,
        "violations": [],
        "response_hash": "",
        "sanitized_response": "",
    }
    generated_response = llm_result.get("generated_response", "")
    if generated_response and routing_decision == "AUTO_RESOLVE":
        safety_result = safety_guardrails_service.validate_response(generated_response)
        if safety_guardrails_service.should_escalate(safety_result):
            routing_decision = "SUGGEST_TO_AGENT"
            logger.warning(
                f"Safety guardrails escalation for {ticket_id}: "
                f"{[v['type'] for v in safety_result['violations']]}"
            )
        elif not safety_result["is_safe"]:
            # Use sanitized response instead
            llm_result["generated_response"] = safety_result["sanitized_response"]
            logger.info(
                f"Response sanitized for {ticket_id}: minor violations redacted"
            )
    stage_timings["safety_check_ms"] = int((time.time() - t_wave7) * 1000)
    stage_timings["wave7_ms"] = stage_timings["safety_check_ms"]

    # Override generated response with safe response for security threats
    if sec_pipeline_result.get("safe_response") and sec_pipeline_result.get(
        "disable_auto_resolve"
    ):
        llm_result["generated_response"] = sec_pipeline_result["safe_response"]

    # Legacy escalation for critical/high threats (post-routing)
    if threat_result.get("threat_detected") and threat_result.get("severity") in (
        "critical",
        "high",
    ):
        if routing_decision == "AUTO_RESOLVE":
            routing_decision = "ESCALATE_TO_HUMAN"
        await escalation_service.create_escalation(
            ticket_id=ticket_id,
            threat_analysis=threat_result,
        )
    elif threat_level == "attack" and not threat_result.get("threat_detected"):
        # New pipeline detected attack but legacy didn't — still escalate
        await escalation_service.create_escalation(
            ticket_id=ticket_id,
            threat_analysis={
                "threat_detected": True,
                "threat_type": threat_type_new,
                "severity": "high",
                "confidence": threat_confidence,
                "recommended_action": detection_reason,
                "indicators": triggered_rules,
            },
        )

    # ─── SLA estimation ───────────────────────────────────────────────
    sla_info = sla_service.get_sla_info(category, final_priority, now)
    estimated_hours = sla_info.get("sla_minutes", 120) / 60 * 0.6
    stage_timings["sla_estimation_ms"] = 0  # sync, instant

    # ─── Build AI analysis doc ─────────────────────────────────────────
    processing_time_ms = int((time.time() - start_time) * 1000)
    stage_timings["total_ms"] = processing_time_ms

    # Load current model version
    from pathlib import Path

    version_file = (
        Path(__file__).parent.parent / "ml" / "artifacts" / "current_version.txt"
    )
    model_version = version_file.read_text().strip() if version_file.exists() else "v1"

    ai_analysis = {
        "category": category,
        "category_probabilities": category_probs,
        "model_confidence": model_confidence,
        "priority": final_priority,
        "priority_confidence": priority_confidence,
        "sentiment_label": sentiment_label,
        "sentiment_score": sentiment_score,
        "is_frustrated": is_frustrated,
        "confidence_score": confidence_score,
        "confidence_breakdown": hitl_result.get("confidence_breakdown"),
        "routing_decision": routing_decision,
        "sla_override": hitl_result.get("sla_override", False),
        "security_override": hitl_result.get("security_override", False),
        "sla_breach_probability": sla_breach_prob,
        "estimated_resolution_hours": estimated_hours,
        "duplicate_of": duplicate_result.get("parent_ticket_id"),
        "is_possible_duplicate": duplicate_result.get("is_possible_duplicate", False),
        "similar_tickets": similar_tickets,
        "top_similarity_score": top_similarity,
        "generated_response": llm_result.get("generated_response"),
        "hallucination_detected": llm_result.get("hallucination_detected", False),
        "fallback_used": llm_result.get("fallback_used", False),
        "model_used": llm_result.get("model_used"),
        "generation_time_ms": llm_result.get("generation_time_ms"),
        "lime_explanation": lime_result,
        "processing_time_ms": processing_time_ms,
        "model_version": model_version,
        # ── HITL Enhancement fields ─────────────────────────────────
        "time_sensitivity": time_sensitivity,
        "department": department,
        "safety_validation": {
            "is_safe": safety_result["is_safe"],
            "violations": safety_result["violations"],
            "response_hash": safety_result.get("response_hash", ""),
            "was_sanitized": not safety_result["is_safe"],
        },
        "stage_timings": stage_timings,
        "zero_shot_used": zero_shot_used,
        "hybrid_override_used": hybrid_override_used,
        # ── Security pipeline fields ────────────────────────────────
        "threat_level": threat_level,
        "threat_type": threat_type_new,
        "threat_confidence": threat_confidence,
        "triggered_rules": triggered_rules,
        "detection_reason": detection_reason,
    }

    # ═══════════════════════════════════════════════════════════════════
    # WAVE 8: Audit logging (fire-and-forget — does not affect response)
    # ═══════════════════════════════════════════════════════════════════
    retrieved_ids = [t["ticket_id"] for t in similar_tickets]

    async def _audit_log():
        try:
            await audit_service.log_pipeline_run(
                ticket_id=ticket_id,
                model_version=model_version,
                predicted_category=category,
                category_probabilities=category_probs,
                model_confidence=model_confidence,
                predicted_priority=final_priority,
                priority_confidence=priority_confidence,
                top_similarity_score=top_similarity,
                retrieved_ticket_ids=retrieved_ids,
                composite_confidence=confidence_score,
                confidence_breakdown=hitl_result.get("confidence_breakdown"),
                routing_decision=routing_decision,
                sla_override=hitl_result.get("sla_override", False),
                security_override=hitl_result.get("security_override", False),
                sla_breach_probability=sla_breach_prob,
                sentiment_label=sentiment_label,
                sentiment_score=sentiment_score,
                generated_response_preview=llm_result.get("generated_response"),
                hallucination_detected=llm_result.get("hallucination_detected", False),
                fallback_used=llm_result.get("fallback_used", False),
                generation_time_ms=llm_result.get("generation_time_ms"),
                lime_top_features=(
                    lime_result.get("top_positive_features") if lime_result else None
                ),
                duplicate_check_performed=True,
                is_duplicate=duplicate_result.get("is_duplicate", False),
                duplicate_of=duplicate_result.get("parent_ticket_id"),
                processing_time_ms=processing_time_ms,
            )
        except Exception as e:
            logger.warning(f"Audit logging failed (non-fatal): {e}")

    asyncio.create_task(_audit_log())

    logger.info(
        f"AI pipeline complete for {ticket_id}: "
        f"category={category}, routing={routing_decision}, "
        f"confidence={confidence_score:.3f}, "
        f"hybrid_override={hybrid_override_used}, "
        f"time={processing_time_ms}ms, "
        f"waves=[w1:{stage_timings.get('wave1_ms', 0)}ms, "
        f"w2:{stage_timings.get('wave2_ms', 0)}ms, "
        f"w3:{stage_timings.get('wave3_ms', 0)}ms, "
        f"w6:{stage_timings.get('wave6_ms', 0)}ms]"
    )

    return ai_analysis


@router.post(
    "/", response_model=TicketSubmitResponse, status_code=status.HTTP_201_CREATED
)
async def submit_ticket(
    body: TicketCreate,
    current_user: Optional[dict] = Depends(get_current_user_optional),
):
    """
    Submit a new support ticket.
    Runs the complete 5-agent AI pipeline and returns result.
    Accessible to anonymous users (no auth required for submission).
    """
    now = utcnow()
    ticket_id = generate_ticket_id()

    user_id = current_user["user_id"] if current_user else "anonymous"
    user_tier = current_user.get("tier", "Standard") if current_user else "Standard"

    # Run AI pipeline
    ai_analysis = await run_ai_pipeline(
        ticket_id=ticket_id,
        subject=body.subject,
        description=body.description,
        user_tier=user_tier,
        now=now,
    )

    # Build ticket document
    ticket_doc = {
        "ticket_id": ticket_id,
        "user_id": user_id,
        "subject": body.subject,
        "description": body.description,
        "cleaned_text": ai_analysis.get("cleaned_text"),
        "attachment_text": body.attachment_text,
        "language": "en",
        "created_at": now,
        "updated_at": now,
        "status": "open",
        "ai_analysis": ai_analysis,
        "resolution": None,
        "metadata": {
            "user_tier": user_tier,
            "submission_hour": now.hour,
            "submission_day": now.weekday(),
            "word_count": len(body.description.split()),
            "urgency_keyword_count": count_urgency_keywords(body.description),
            "duplicate_count": 0,
            "root_cause_group_id": None,
        },
    }

    # Store ticket
    collection = get_tickets_collection()
    await collection.insert_one(ticket_doc)

    # Create journey tracking
    await journey_service.create_journey(ticket_id=ticket_id, initial_phase="submitted")

    # Add AI processing step
    await journey_service.add_journey_step(
        ticket_id=ticket_id,
        phase="ai_processing",
        status="completed",
        notes=f"AI analyzed ticket: {ai_analysis.get('category')} - {ai_analysis.get('priority')}",
        metadata={
            "confidence": ai_analysis.get("confidence_score"),
            "routing": ai_analysis.get("routing_decision"),
        },
    )

    # Handle routing decision
    routing_decision = ai_analysis.get("routing_decision")

    if routing_decision == "AUTO_RESOLVE":
        # Mark as AI resolved
        await journey_service.add_journey_step(
            ticket_id=ticket_id,
            phase="ai_resolved",
            status="completed",
            notes="Ticket automatically resolved by AI",
        )
    elif routing_decision in ["SUGGEST_TO_AGENT", "ESCALATE_TO_HUMAN"]:
        # Assign to human agent
        department = ai_analysis.get("department", "SOFTWARE")
        agent = await journey_service.find_available_agent(department)

        if agent:
            await journey_service.assign_to_agent(
                ticket_id=ticket_id,
                agent_email=agent["email"],
                agent_name=agent["full_name"],
                department=agent["department"],
            )
            logger.info(
                f"Ticket {ticket_id} assigned to {agent['full_name']} ({department})"
            )
        else:
            logger.warning(f"No available agent found for department {department}")
            # Add to queue
            await journey_service.add_journey_step(
                ticket_id=ticket_id,
                phase="queued",
                status="current",
                notes=f"Waiting for available agent in {department} department",
            )

    # Notify connected agent dashboards
    await notification_service.notify_new_ticket(
        {
            "ticket_id": ticket_id,
            "subject": body.subject,
            "category": ai_analysis.get("category"),
            "priority": ai_analysis.get("priority"),
            "routing_decision": ai_analysis.get("routing_decision"),
            "confidence_score": ai_analysis.get("confidence_score"),
        }
    )

    return TicketSubmitResponse(
        ticket_id=ticket_id,
        message=(
            "Your ticket has been automatically resolved!"
            if ai_analysis.get("routing_decision") == "AUTO_RESOLVE"
            else "Your ticket is being reviewed by our team."
        ),
        status="open",
        ai_analysis=ai_analysis,
        estimated_resolution_hours=ai_analysis.get("estimated_resolution_hours"),
    )


@router.get("/", response_model=TicketListResponse)
async def list_tickets(
    status: Optional[str] = None,
    category: Optional[str] = None,
    routing_decision: Optional[str] = None,
    priority: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """
    List tickets with optional filters. Agents see all; users see their own.
    """
    collection = get_tickets_collection()

    # Build filter
    query = {}
    if current_user["role"] == "user":
        query["user_id"] = current_user["user_id"]
    if status:
        query["status"] = status
    if category:
        query["ai_analysis.category"] = category
    if routing_decision:
        query["ai_analysis.routing_decision"] = routing_decision
    if priority:
        query["ai_analysis.priority"] = priority

    total = await collection.count_documents(query)
    paging = paginate(total, page, page_size)

    cursor = (
        collection.find(query)
        .sort("created_at", -1)
        .skip(paging["skip"])
        .limit(paging["limit"])
    )
    docs = await cursor.to_list(length=page_size)

    tickets = []
    for doc in docs:
        ai = doc.get("ai_analysis") or {}
        tickets.append(
            TicketListItem(
                ticket_id=doc["ticket_id"],
                subject=doc["subject"],
                status=doc["status"],
                created_at=doc["created_at"],
                category=ai.get("category"),
                priority=ai.get("priority"),
                confidence_score=ai.get("confidence_score"),
                routing_decision=ai.get("routing_decision"),
                sentiment_label=ai.get("sentiment_label"),
                sla_breach_probability=ai.get("sla_breach_probability"),
                is_frustrated=ai.get("is_frustrated"),
            )
        )

    return TicketListResponse(
        tickets=tickets,
        total=paging["total"],
        page=paging["page"],
        page_size=paging["page_size"],
        total_pages=paging["total_pages"],
    )


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get full ticket details including AI analysis."""
    collection = get_tickets_collection()
    doc = await collection.find_one({"ticket_id": ticket_id})

    if not doc:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Users can only see their own tickets
    if current_user["role"] == "user" and doc["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    doc.pop("_id", None)
    return TicketResponse(**doc)


@router.get("/{ticket_id}/explain")
async def get_ticket_explanation(
    ticket_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get LIME explanation for a ticket's classification."""
    collection = get_tickets_collection()
    doc = await collection.find_one({"ticket_id": ticket_id})

    if not doc:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ai = doc.get("ai_analysis", {}) or {}
    lime = ai.get("lime_explanation")

    if not lime:
        # Re-generate LIME explanation if not stored
        cleaned = doc.get("cleaned_text") or doc.get("description", "")
        lime = await explainability_service.explain_async(
            cleaned_text=cleaned,
            classifier_service=classifier_service,
        )

    return {"ticket_id": ticket_id, "lime_explanation": lime}


@router.get("/{ticket_id}/similar")
async def get_similar_tickets(
    ticket_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get similar resolved tickets from ChromaDB for a given ticket."""
    collection = get_tickets_collection()
    doc = await collection.find_one({"ticket_id": ticket_id})

    if not doc:
        raise HTTPException(status_code=404, detail="Ticket not found")

    cleaned = doc.get("cleaned_text") or doc.get("description", "")
    category = (doc.get("ai_analysis") or {}).get("category")

    similar = await retrieval_service.find_similar_tickets(
        text=cleaned,
        category=category,
    )

    return {
        "ticket_id": ticket_id,
        "similar_tickets": similar["similar_tickets"],
        "knowledge_base_size": similar["knowledge_base_size"],
    }


@router.patch("/{ticket_id}/status")
async def update_ticket_status(
    ticket_id: str,
    body: TicketStatusUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update ticket status (agent/admin only)."""
    if current_user["role"] == "user":
        raise HTTPException(status_code=403, detail="Agents only")

    collection = get_tickets_collection()
    result = await collection.update_one(
        {"ticket_id": ticket_id},
        {
            "$set": {
                "status": body.status,
                "updated_at": utcnow(),
                "resolution.notes": body.notes,
            }
        },
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return {"ticket_id": ticket_id, "status": body.status}


@router.get("/user/{user_id}")
async def get_tickets_by_user(
    user_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get all tickets submitted by a specific user."""
    # Users can only see their own; agents/admins can see any
    if current_user["role"] == "user" and current_user["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    collection = get_tickets_collection()
    cursor = collection.find({"user_id": user_id}).sort("created_at", -1)
    docs = await cursor.to_list(length=50)
    for doc in docs:
        doc.pop("_id", None)

    return {"user_id": user_id, "tickets": docs, "total": len(docs)}