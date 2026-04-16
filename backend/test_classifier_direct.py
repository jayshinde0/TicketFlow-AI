# backend/test_classifier_direct.py (CREATE THIS)

import joblib
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer

# Load model and vectorizer
model = joblib.load("ml/artifacts/category_model.pkl")
vectorizer = joblib.load("ml/artifacts/tfidf_vectorizer.pkl")

tickets = [
    ("I cannot connect to the company VPN. I get a timeout error.", "Network"),
    ("I was charged twice for my subscription.", "Billing"),
    ("Cannot login to my account.", "Auth"),
    ("Laptop screen is flickering.", "Hardware"),
    ("Application crashes on startup.", "Software"),
]

print("\n" + "=" * 70)
print("DIRECT CLASSIFIER TEST")
print("=" * 70)

for text, expected in tickets:
    X = vectorizer.transform([text])
    pred = model.predict(X)[0]
    conf = model.predict_proba(X)[0].max()

    status = "✓" if pred == expected else "❌"
    print(f"\n{status} Text: {text[:50]}...")
    print(f"   Expected: {expected}")
    print(f"   Predicted: {pred} (confidence: {conf:.2f})")

print("\n" + "=" * 70)
