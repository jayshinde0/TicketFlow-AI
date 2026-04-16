"""
Test LLM service exactly as the backend uses it
"""
import asyncio
import sys
from loguru import logger

# Configure logger to see all messages
logger.remove()
logger.add(sys.stderr, level="DEBUG")

async def test_llm_service():
    print("=" * 60)
    print("Testing LLM Service (as used by backend)")
    print("=" * 60)
    
    # Import after logger config
    from services.llm_service import llm_service
    from core.config import settings
    
    print(f"\nConfiguration:")
    print(f"   Provider: {settings.LLM_PROVIDER}")
    print(f"   Model: {settings.OLLAMA_MODEL}")
    print(f"   URL: {settings.OLLAMA_URL}")
    print(f"   Timeout: 60s")
    print(f"   Max Retries: 2")
    
    # Test 1: Simple generation
    print(f"\n" + "=" * 60)
    print("Test 1: Generate Response (RAG)")
    print("=" * 60)
    
    ticket_text = "I can't login to my account. It says password incorrect."
    category = "Auth"
    retrieved_solution = "Reset password via the password reset link. Check if account is locked after 3 failed attempts."
    routing_decision = "AUTO_RESOLVE"
    
    print(f"\nInput:")
    print(f"   Ticket: {ticket_text}")
    print(f"   Category: {category}")
    print(f"   Routing: {routing_decision}")
    
    print(f"\nCalling llm_service.generate_response()...")
    
    try:
        result = await llm_service.generate_response(
            ticket_text=ticket_text,
            category=category,
            retrieved_solution=retrieved_solution,
            routing_decision=routing_decision
        )
        
        print(f"\nResult:")
        print(f"   Generated: {bool(result['generated_response'])}")
        print(f"   Time: {result['generation_time_ms']}ms")
        print(f"   Hallucination: {result['hallucination_detected']}")
        print(f"   Fallback: {result['fallback_used']}")
        print(f"   Model: {result['model_used']}")
        
        if result['generated_response']:
            print(f"\nResponse:")
            print(f"   {result['generated_response'][:300]}...")
            
            if result['fallback_used']:
                print(f"\nWARNING: Fallback was used!")
                print(f"   This means LLM generation failed or hallucination detected")
                return False
            else:
                print(f"\nSUCCESS: LLM generated response correctly!")
                return True
        else:
            print(f"\nERROR: No response generated!")
            return False
            
    except Exception as e:
        print(f"\nEXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_llm_service())
    print(f"\n" + "=" * 60)
    if result:
        print("SUCCESS: LLM SERVICE IS WORKING CORRECTLY")
    else:
        print("FAILED: LLM SERVICE FAILED")
    print("=" * 60)
    sys.exit(0 if result else 1)
