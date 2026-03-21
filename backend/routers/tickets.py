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
    TicketCreate, TicketListResponse, TicketListItem,
    TicketResponse, TicketSubmitResponse, TicketStatusUpdate,
    TicketStatus, TicketMetadata, AIAnalysis, ResolutionData,
)
from services.nlp_service import nlp_service
from services.classifier_service import classifier_service
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
from utils.helpers import generate_ticket_id, utcnow, paginate, tier_to_int
from utils.text_cleaner import count_urgency_keywords

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])


async def run_ai_pipeline(
    ticket_id: str,
    subject: str,
    description: str,
    user_tier: str = "Standard",
    now: Optional[datetime] = None,
) -> dict:
    """
    Orchestrated 5-agent AI pipeline for ticket processing.

    Agents run in sequence:
    1. NLP preprocessing
    2. Sentiment analysis
    3. Classifier (category + priority)
    4. Embeddings + Retrieval (similar tickets)
    5. SLA prediction
    6. HITL routing decision (confidence + overrides)
    7. LLM response generation
    8. LIME explainability
    9. Duplicate detection
    10. Audit logging

    Returns:
        Complete AI analysis dict ready for MongoDB storage.
    """
    start_time = time.time()
    if now is None:
        now = utcnow()

    combined_text = f"{subject}. {description}"

    # ─── Agent 0: NLP preprocessing ──────────────────────────────────
    nlp_result = await nlp_service.preprocess_async(combined_text)
    cleaned_text = nlp_result["cleaned_text"]
    features = nlp_result["features"]
    word_count = features["word_count"]
    urgency_count = features["urgency_keyword_count"]

    # ─── Sentiment service ────────────────────────────────────────────
    try:
        sentiment_result = await asyncio.wait_for(
            sentiment_service.analyze_async(combined_text), timeout=8.0
        )
    except (asyncio.TimeoutError, Exception) as e:
        logger.warning(f"Sentiment service timeout/error: {e}. Using neutral fallback.")
        sentiment_result = {"sentiment_label": "NEUTRAL", "sentiment_score": 0.5, "is_frustrated": False}
    sentiment_label = sentiment_result["sentiment_label"]
    sentiment_score = sentiment_result["sentiment_score"]
    is_frustrated = sentiment_result["is_frustrated"]

    # ─── Agent 1: Classify category + priority ────────────────────────
    classify_result = classifier_service.classify(
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

    # ─── Agent 2: Retrieve similar tickets ────────────────────────────
    try:
        retrieval_result = await asyncio.wait_for(
            retrieval_service.find_similar_tickets(
                text=cleaned_text, category=category, top_k=3,
            ),
            timeout=15.0,   # first run downloads embedding model
        )
    except (asyncio.TimeoutError, Exception) as e:
        logger.warning(f"Retrieval service timeout/error: {e}. Using empty fallback.")
        retrieval_result = {"similar_tickets": [], "top_similarity_score": 0.0, "embedding": None, "knowledge_base_size": 0}
    similar_tickets = retrieval_result["similar_tickets"]
    top_similarity = retrieval_result["top_similarity_score"]
    ticket_embedding = retrieval_result.get("embedding")

    # ─── SLA prediction ───────────────────────────────────────────────
    similar_avg_resolution = (
        sum(t.get("resolution_time_hours", 2.0) for t in similar_tickets) / len(similar_tickets)
        if similar_tickets else 2.0
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

    # ─── Agent 3: HITL routing decision ────────────────────────────────
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

    # ─── Agent 4: LLM response generation ─────────────────────────────
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

    # ─── LIME explainability (async, won't block pipeline) ────────────
    lime_result = None
    try:
        lime_result = await explainability_service.explain_async(
            cleaned_text=cleaned_text,
            classifier_service=classifier_service,
            num_features=8,
            num_samples=200,   # reduced samples for speed
        )
    except Exception as e:
        logger.debug(f"LIME explanation skipped: {e}")

    # ─── Duplicate detection ──────────────────────────────────────────
    duplicate_result = await duplicate_service.check_duplicate(
        text=cleaned_text,
        new_ticket_id=ticket_id,
        category=category,
    )

    # ─── SLA estimation ───────────────────────────────────────────────
    sla_info = sla_service.get_sla_info(category, final_priority, now)
    estimated_hours = sla_service._get_predictor() and sla_service.predict_breach_probability  # use model if available

    # ─── Build AI analysis doc ─────────────────────────────────────────
    processing_time_ms = int((time.time() - start_time) * 1000)

    # Load current model version
    from pathlib import Path
    version_file = Path(__file__).parent.parent / "ml" / "artifacts" / "current_version.txt"
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
        "estimated_resolution_hours": sla_info.get("sla_minutes", 120) / 60 * 0.6,
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
    }

    # ─── Audit logging ────────────────────────────────────────────────
    retrieved_ids = [t["ticket_id"] for t in similar_tickets]
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
        lime_top_features=lime_result.get("top_positive_features") if lime_result else None,
        duplicate_check_performed=True,
        is_duplicate=duplicate_result.get("is_duplicate", False),
        duplicate_of=duplicate_result.get("parent_ticket_id"),
        processing_time_ms=processing_time_ms,
    )

    logger.info(
        f"AI pipeline complete for {ticket_id}: "
        f"category={category}, routing={routing_decision}, "
        f"confidence={confidence_score:.3f}, "
        f"time={processing_time_ms}ms"
    )

    return ai_analysis


@router.post("/", response_model=TicketSubmitResponse, status_code=status.HTTP_201_CREATED)
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

    # Notify connected agent dashboards
    await notification_service.notify_new_ticket({
        "ticket_id": ticket_id,
        "subject": body.subject,
        "category": ai_analysis.get("category"),
        "priority": ai_analysis.get("priority"),
        "routing_decision": ai_analysis.get("routing_decision"),
        "confidence_score": ai_analysis.get("confidence_score"),
    })

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
        tickets.append(TicketListItem(
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
        ))

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
