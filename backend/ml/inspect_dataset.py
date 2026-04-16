# backend/ml/inspect_dataset.py (UPDATE THIS)

import pandas as pd
import os
from pathlib import Path

print("=" * 70)
print("DATASET INSPECTION")
print("=" * 70)

# Get the correct path (relative to the script location)
script_dir = Path(__file__).parent  # This is backend/ml/
data_dir = script_dir / "data"  # This is backend/ml/data/

print(f"\nLooking for data in: {data_dir}")
print(f"Directory exists: {data_dir.exists()}")

if not data_dir.exists():
    print(f"❌ Data directory not found: {data_dir}")
    print(f"Please download the dataset to: {data_dir}")
    exit(1)

# Find CSV files
csv_files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]
print(f"\nFound CSV files: {csv_files}\n")

if not csv_files:
    print("❌ No CSV files found in data directory!")
    exit(1)

for csv_file in csv_files:
    file_path = data_dir / csv_file
    print(f"\n{'='*70}")
    print(f"FILE: {csv_file}")
    print(f"SIZE: {file_path.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"{'='*70}")

    # Load CSV
    df = pd.read_csv(file_path)

    print(f"\n📊 SHAPE: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"\n📋 COLUMNS:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i}. {col} ({df[col].dtype})")

    print(f"\n📝 FIRST ROW:")
    print(df.iloc[0].to_string())

    print(f"\n🔍 DATA TYPES:")
    print(df.dtypes)

    print(f"\n⚠️  NULL VALUES:")
    null_counts = df.isnull().sum()
    for col, count in null_counts.items():
        if count > 0:
            print(f"  {col}: {count} nulls ({100*count/len(df):.1f}%)")

    print(f"\n📈 UNIQUE VALUES:")
    for col in df.columns:
        unique_count = df[col].nunique()
        if unique_count < 50:
            print(f"  {col}: {unique_count} unique values")
            if unique_count <= 10:
                print(f"    {df[col].unique()}")
        else:
            print(f"  {col}: {unique_count} unique values")

print("\n✅ Inspection complete!")
