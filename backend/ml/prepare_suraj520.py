# backend/ml/prepare_suraj520.py (FIXED VERSION)

import pandas as pd
import os
from loguru import logger
from pathlib import Path

# Configure logger
logger.remove()
logger.add(lambda msg: print(msg), format="{time:HH:mm:ss} | {level} | {message}")

def prepare_suraj520_dataset():
    """
    Convert suraj520 customer support dataset to TicketFlow-AI format.
    """
    
    print("\n" + "="*70)
    print("PREPARING SURAJ520 DATASET FOR TICKETFLOW-AI")
    print("="*70)
    
    # Get the correct path (relative to this script)
    script_dir = Path(__file__).parent  # backend/ml/
    data_dir = script_dir / "data"
    
    # Try different possible filenames
    possible_files = [
        data_dir / "customer_support_tickets.csv",
        data_dir / "customer-support-tickets.csv",
        data_dir / "customer_support_tickets_processed.csv",
    ]
    
    input_file = None
    for possible_path in possible_files:
        if possible_path.exists():
            input_file = possible_path
            break
    
    if input_file is None:
        logger.error(f"Input file not found in {data_dir}")
        logger.info(f"Looking for CSV files...")
        csv_files = list(data_dir.glob("*.csv"))
        if csv_files:
            logger.info(f"Found these CSV files:")
            for f in csv_files:
                logger.info(f"  - {f.name} ({f.stat().st_size / 1024:.2f} KB)")
        return False
    
    output_file = script_dir / "data" / "prepared_tickets.csv"
    
    logger.info(f"Input file: {input_file}")
    logger.info(f"Output file: {output_file}")
    
    # Load dataset
    logger.info(f"\nLoading dataset...")
    try:
        df = pd.read_csv(input_file)
        logger.info(f"✓ Loaded {len(df)} tickets")
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        return False
    
    # Step 1: Extract and combine text
    logger.info(f"\nStep 1: Extracting text fields...")
    
    # Check which columns exist
    available_cols = df.columns.tolist()
    logger.info(f"Available columns: {available_cols}")
    
    # Find text columns (flexible matching)
    subject_col = None
    desc_col = None
    
    for col in available_cols:
        if 'subject' in col.lower():
            subject_col = col
        if any(x in col.lower() for x in ['description', 'body', 'detail', 'message']):
            desc_col = col
    
    logger.info(f"Subject column: {subject_col}")
    logger.info(f"Description column: {desc_col}")
    
    # Combine text
    if subject_col and desc_col:
        df['combined_text'] = (
            df[subject_col].fillna('') + ' ' + 
            df[desc_col].fillna('')
        ).str.strip()
    elif desc_col:
        df['combined_text'] = df[desc_col].fillna('')
    else:
        logger.error("Could not find description column!")
        return False
    
    initial_count = len(df)
    logger.info(f"✓ Combined text fields")
    
    # Step 2: Clean text
    logger.info(f"\nStep 2: Cleaning text...")
    
    # Remove nulls
    df = df[df['combined_text'].notna() & (df['combined_text'].str.len() > 0)]
    logger.info(f"✓ After removing nulls: {len(df)} rows")
    
    # Remove short texts
    df = df[df['combined_text'].str.len() >= 20]
    logger.info(f"✓ After removing short texts: {len(df)} rows")
    
    # Remove duplicates
    before_dedup = len(df)
    df = df.drop_duplicates(subset=['combined_text'])
    logger.info(f"✓ After removing duplicates: {len(df)} rows (removed {before_dedup - len(df)})")
    
    # Step 3: Map Ticket Type to TicketFlow Categories
    logger.info(f"\nStep 3: Mapping categories...")
    
    # Find the ticket type column
    type_col = None
    for col in available_cols:
        if any(x in col.lower() for x in ['type', 'category', 'topic', 'class']):
            type_col = col
            break
    
    if not type_col:
        logger.warning(f"Could not find type/category column, using default")
        df['category'] = 'Software'
    else:
        logger.info(f"Using column '{type_col}' for categories")
        
        category_mapping = {
            "technical issue": "Software",
            "billing inquiry": "Billing",
            "refund request": "Billing",
            "cancellation request": "ServiceRequest",
            "product inquiry": "ServiceRequest",
            "account access": "Auth",
            "account": "Auth",
            "login": "Auth",
            "password": "Auth",
            "authentication": "Auth",
            "email": "Email",
            "mail": "Email",
            "network": "Network",
            "connectivity": "Network",
            "vpn": "Network",
            "hardware": "Hardware",
            "device": "Hardware",
            "laptop": "Hardware",
            "security": "Security",
            "phishing": "Security",
            "access": "Access",
            "permission": "Access",
        }
        
        def map_category(val):
            val_lower = str(val).lower().strip()
            # Exact match
            if val_lower in category_mapping:
                return category_mapping[val_lower]
            # Partial match
            for key, mapped_cat in category_mapping.items():
                if key in val_lower:
                    return mapped_cat
            return "Software"
        
        df['category'] = df[type_col].apply(map_category)
    
    logger.info(f"✓ Category distribution:")
    for cat, count in df['category'].value_counts().items():
        pct = 100 * count / len(df)
        logger.info(f"  {cat}: {count} ({pct:.1f}%)")
    
    # Step 4: Map Priority
    logger.info(f"\nStep 4: Mapping priorities...")
    
    # Find priority column
    priority_col = None
    for col in available_cols:
        if 'priority' in col.lower() or 'severity' in col.lower():
            priority_col = col
            break
    
    if priority_col:
        logger.info(f"Using column '{priority_col}' for priorities")
        
        priority_mapping = {
            "critical": "Critical",
            "high": "High",
            "medium": "Medium",
            "low": "Low",
            "urgent": "High",
            "normal": "Medium",
        }
        
        def map_priority(val):
            val_lower = str(val).lower().strip()
            return priority_mapping.get(val_lower, "Medium")
        
        df['priority'] = df[priority_col].apply(map_priority)
    else:
        logger.warning(f"Could not find priority column, using default")
        df['priority'] = 'Medium'
    
    logger.info(f"✓ Priority distribution:")
    for pri, count in df['priority'].value_counts().items():
        pct = 100 * count / len(df)
        logger.info(f"  {pri}: {count} ({pct:.1f}%)")
    
    # Step 5: Create final dataset
    logger.info(f"\nStep 5: Creating final dataset...")
    
    df_final = pd.DataFrame({
        'text': df['combined_text'],
        'category': df['category'],
        'priority': df['priority'],
    })
    
    df_final = df_final.reset_index(drop=True)
    
    # Step 6: Save
    logger.info(f"\nStep 6: Saving processed dataset...")
    df_final.to_csv(output_file, index=False)
    logger.info(f"✓ Saved to {output_file}")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Original rows:     {initial_count}")
    print(f"After cleaning:    {len(df_final)}")
    print(f"Removed:           {initial_count - len(df_final)} ({100*(initial_count-len(df_final))/initial_count:.1f}%)")
    print(f"\nOutput file:       {output_file}")
    print(f"File size:         {output_file.stat().st_size / 1024:.2f} KB")
    print("\nData ready for training!")
    print("="*70)
    
    return True

if __name__ == "__main__":
    success = prepare_suraj520_dataset()
    if success:
        print("\n✅ Preparation successful!")
    else:
        print("\n❌ Preparation failed!")
        exit(1)