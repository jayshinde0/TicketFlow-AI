# backend/test_routing_decision.py (CREATE THIS)

import asyncio
from datetime import datetime
from services.classifier_service import classifier_service
from services.nlp_service import nlp_service
from services.hitl_service import hitl_service
from utils.helpers import utcnow


async def test_routing():
    ticket = "I cannot connect to the company VPN. I get a timeout error after entering my credentials. This is blocking my work completely."

    print("\n" + "=" * 70)
    print("TESTING FULL ROUTING LOGIC")
    print("=" * 70)

    # Step 1: NLP
    print("\n1. NLP PREPROCESSING:")
    nlp_result = await nlp_service.preprocess_async(ticket)
    cleaned = nlp_result["cleaned_text"]
    print(f"   ✓ Cleaned text ready")

    # Step 2: Classification
    print("\n2. CLASSIFICATION:")
    classify_result = classifier_service.classify(
        cleaned_text=cleaned,
        user_tier="Standard",
        submission_hour=9,
        word_count=nlp_result["features"]["word_count"],
        urgency_keyword_count=nlp_result["features"]["urgency_keyword_count"],
        sentiment_score=0.5,
    )

    print(f"   Category: {classify_result['category']}")
    print(f"   Model confidence: {classify_result['model_confidence']:.2f}")
    print(f"   Priority: {classify_result['priority']}")

    # Step 3: HITL Routing
    print("\n3. HITL ROUTING DECISION:")
    hitl_result = hitl_service.route(
        category=classify_result["category"],
        model_confidence=classify_result["model_confidence"],
        priority=classify_result["priority"],
        priority_confidence=classify_result.get("priority_confidence", 0.7),
        top_similarity_score=0.85,  # Assume we found similar ticket
        sentiment_label="NEUTRAL",
        sentiment_score=0.5,
        is_frustrated=False,
        sla_breach_probability=0.3,
        ticket_text=ticket,
        user_tier="Standard",
    )

    print(f"   Routing Decision: {hitl_result['routing_decision']}")
    print(f"   Composite Confidence: {hitl_result['confidence_score']:.2f}")
    print(f"   Final Priority: {hitl_result['priority']}")
    print(f"   Confidence Breakdown:")
    for key, val in hitl_result.get("confidence_breakdown", {}).items():
        print(f"     - {key}: {val:.2f}")

    print("\n" + "=" * 70)


asyncio.run(test_routing())
