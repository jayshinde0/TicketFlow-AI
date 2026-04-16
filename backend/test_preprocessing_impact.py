# backend/test_preprocessing_impact.py (CREATE THIS)

import asyncio
from services.nlp_service import nlp_service
import joblib


async def test_preprocessing():
    ticket = "I cannot connect to the company VPN. I get a timeout error after entering my credentials."

    # Load classifier
    model = joblib.load("ml/artifacts/category_model.pkl")
    vectorizer = joblib.load("ml/artifacts/tfidf_vectorizer.pkl")

    print("\n" + "=" * 70)
    print("TESTING PREPROCESSING IMPACT")
    print("=" * 70)

    # Test 1: Original text
    print("\n1. ORIGINAL TEXT:")
    print(f"   Text: {ticket}")
    X = vectorizer.transform([ticket])
    pred = model.predict(X)[0]
    conf = model.predict_proba(X)[0].max()
    print(f"   Classification: {pred} ({conf:.2f})")

    # Test 2: After NLP preprocessing
    print("\n2. AFTER NLP PREPROCESSING:")
    nlp_result = await nlp_service.preprocess_async(ticket)
    cleaned = nlp_result["cleaned_text"]
    print(f"   Text: {cleaned}")
    X = vectorizer.transform([cleaned])
    pred = model.predict(X)[0]
    conf = model.predict_proba(X)[0].max()
    print(f"   Classification: {pred} ({conf:.2f})")

    # Test 3: Show difference
    print("\n3. DIFFERENCE:")
    if ticket == cleaned:
        print(f"   ✓ No change - text is the same")
    else:
        print(f"   ❌ Text was modified by NLP preprocessing")
        print(f"   Original length: {len(ticket)}")
        print(f"   Cleaned length: {len(cleaned)}")

    print("\n" + "=" * 70)


asyncio.run(test_preprocessing())
