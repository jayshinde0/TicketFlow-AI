"""
tests/test_nlp_cache.py — Test NLP preprocessing cache functionality
Run with: python tests/test_nlp_cache.py
"""

import asyncio
import sys
from pathlib import Path
import time
import uuid

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.nlp_cache import nlp_cache
from services.nlp_service import nlp_service


async def test_nlp_cache():
    """Test NLP cache with first miss, then hit"""
    
    print("\n" + "="*60)
    print("NLP CACHE TEST")
    print("="*60)
    
    # Use unique text each run to avoid cache pollution
    unique_id = str(uuid.uuid4())[:8]
    test_text = f"VPN timeout error 800. Cannot connect to network. {unique_id}"
    
    print(f"\nTest Text: {test_text}")
    print("\n--- First Call (Cache Miss) ---")
    
    # First call - should be cache miss (unique text)
    t0 = time.time()
    result1 = await nlp_cache.get(test_text)
    first_check_time = time.time() - t0
    
    print(f"Cache lookup time: {first_check_time*1000:.2f}ms")
    
    nlp_result = None  # Initialize variable
    
    if result1 is None:
        print("✅ Cache miss (expected - first time)")
        
        # Now actually process it
        print("\nProcessing NLP...")
        t0 = time.time()
        nlp_result = await nlp_service.preprocess_async(test_text)
        process_time = time.time() - t0
        print(f"NLP processing time: {process_time*1000:.2f}ms")
        
        # Store in cache
        print("\nStoring in cache...")
        await nlp_cache.set(test_text, nlp_result)
        print("✅ Stored in cache")
        
        print(f"\nCleaned text: {nlp_result['cleaned_text']}")
        print(f"Word count: {nlp_result['features']['word_count']}")
        print(f"Urgency keywords: {nlp_result['features']['urgency_keyword_count']}")
    else:
        print("⚠️ Cache hit on first call (data already cached)")
        nlp_result = result1
    
    print("\n--- Second Call (Cache Hit) ---")
    
    # Second call - should be cache hit
    t0 = time.time()
    result2 = await nlp_cache.get(test_text)
    second_check_time = time.time() - t0
    
    print(f"Cache lookup time: {second_check_time*1000:.2f}ms")
    
    if result2 is not None:
        print("✅ Cache hit (expected - second time)")
        
        # Check if content is the same
        if nlp_result and result2:
            content_match = (
                result2.get('cleaned_text') == nlp_result.get('cleaned_text') and
                result2.get('features') == nlp_result.get('features')
            )
            print(f"Content match: {content_match}")
        
        if first_check_time > 0 and second_check_time > 0:
            speedup = first_check_time / second_check_time
            print(f"Speedup: {speedup:.1f}x")
    else:
        print("⚠️ Cache miss (might be Upstash not configured)")
    
    print("\n" + "="*60)
    print("NLP CACHE TEST COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(test_nlp_cache())