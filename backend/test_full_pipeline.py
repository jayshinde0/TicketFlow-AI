# backend/test_full_pipeline.py (FIXED)

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from services.classifier_service import classifier_service
from services.nlp_service import nlp_service


async def test_pipeline():
    test_ticket = "I cannot connect to the company VPN. I get a timeout error after entering my credentials. This is blocking my work completely."

    print("\n" + "=" * 70)
    print("TESTING FULL CLASSIFICATION PIPELINE")
    print("=" * 70)

    # Step 1: NLP preprocessing (async)
    print("\n1. NLP PREPROCESSING:")
    nlp_result = await nlp_service.preprocess_async(test_ticket)
    print(f"   Original text: {test_ticket[:60]}...")
    print(f"   Cleaned text: {nlp_result['cleaned_text'][:60]}...")
    print(f"   Features:")
    print(f"     - word_count: {nlp_result['features']['word_count']}")
    print(f"     - urgency_keywords: {nlp_result['features']['urgency_keyword_count']}")

    # Step 2: Classification (sync)
    print("\n2. CLASSIFICATION:")
    result = classifier_service.classify(
        cleaned_text=nlp_result["cleaned_text"],
        user_tier="Standard",
        submission_hour=9,
        word_count=nlp_result["features"]["word_count"],
        urgency_keyword_count=nlp_result["features"]["urgency_keyword_count"],
        sentiment_score=0.5,
    )

    print(
        f"   Category: {result['category']} (confidence: {result['model_confidence']:.2f})"
    )
    print(f"   Priority: {result['priority']}")
    print(f"   Top 5 categories with probabilities:")
    sorted_probs = sorted(
        result["category_probabilities"].items(), key=lambda x: x[1], reverse=True
    )
    for cat, prob in sorted_probs[:5]:
        print(f"     - {cat}: {prob:.3f}")

    print("\n" + "=" * 70)

    # Compare direct vs pipeline
    print("\n3. COMPARISON:")
    print(f"   Direct classifier: Network (0.88)")
    print(
        f"   Pipeline result: {result['category']} ({result['model_confidence']:.2f})"
    )

    if result["category"] == "Network":
        print(f"   ✓ MATCH - Pipeline works correctly!")
    else:
        print(f"   ❌ MISMATCH - Issue in pipeline preprocessing")


if __name__ == "__main__":
    asyncio.run(test_pipeline())
