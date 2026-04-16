# backend/diagnose_issue.py (CREATE THIS)

import pandas as pd
from pathlib import Path
import joblib
import os

print("\n" + "=" * 70)
print("DIAGNOSTIC REPORT")
print("=" * 70)

# 1. Check what files exist
print("\n1. CHECKING FILES:")
data_dir = Path("ml/data")
csv_files = list(data_dir.glob("*.csv"))
print(f"   CSV files in ml/data:")
for f in csv_files:
    size_kb = f.stat().st_size / 1024
    print(f"     - {f.name} ({size_kb:.1f} KB)")

# 2. Check models
print("\n2. CHECKING MODELS:")
artifacts_dir = Path("ml/artifacts")
pkl_files = list(artifacts_dir.glob("*.pkl"))
print(f"   PKL files in ml/artifacts:")
for f in pkl_files:
    size_kb = f.stat().st_size / 1024
    print(f"     - {f.name} ({size_kb:.1f} KB)")

# 3. Load and test model
print("\n3. TESTING MODEL:")
model_path = artifacts_dir / "category_model.pkl"
vectorizer_path = artifacts_dir / "tfidf_vectorizer.pkl"

if model_path.exists() and vectorizer_path.exists():
    model = joblib.load(model_path)
    vectorizer = joblib.load(vectorizer_path)

    print(f"   ✓ Model loaded")
    print(f"   Classes: {list(model.classes_)}")
    print(f"   Features: {model.n_features_in_}")

    # Test VPN ticket
    vpn_ticket = "I cannot connect to the company VPN. I get a timeout error after entering my credentials."
    X = vectorizer.transform([vpn_ticket])
    pred = model.predict(X)[0]
    proba = model.predict_proba(X)[0]

    class_probs = dict(zip(model.classes_, proba))
    sorted_probs = sorted(class_probs.items(), key=lambda x: x[1], reverse=True)

    print(f"\n   VPN Test:")
    print(f"   Text: {vpn_ticket[:50]}...")
    print(f"   Prediction: {pred} (confidence: {sorted_probs[0][1]:.2f})")
    print(f"   Top 3:")
    for i, (cls, prob) in enumerate(sorted_probs[:3], 1):
        print(f"     {i}. {cls}: {prob:.2f}")
else:
    print(f"   ❌ Models not found!")

# 4. Check prepared dataset
print("\n4. CHECKING PREPARED DATA:")
prepared_file = data_dir / "prepared_tickets.csv"
if prepared_file.exists():
    df = pd.read_csv(prepared_file)
    print(f"   ✓ {prepared_file.name} loaded")
    print(f"   Rows: {len(df)}")
    print(f"   Categories:")
    for cat in df["category"].value_counts().head(10).items():
        print(f"     - {cat[0]}: {cat[1]}")
else:
    print(f"   ❌ {prepared_file.name} not found")

print("\n" + "=" * 70)
