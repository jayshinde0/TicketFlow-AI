"""
Test Ollama connection and generation
"""
import asyncio
import sys
from services.ollama_provider import ollama_provider
from core.config import settings

async def test_ollama():
    print(f"Testing Ollama connection...")
    print(f"URL: {settings.OLLAMA_URL}")
    print(f"Model: {settings.OLLAMA_MODEL}")
    print("-" * 50)
    
    # Test 1: Check availability
    print("\n1. Checking if Ollama is available...")
    is_available = await ollama_provider.is_available()
    print(f"   Result: {'✅ Available' if is_available else '❌ Not available'}")
    
    if not is_available:
        print("\n❌ Ollama is not running or not accessible!")
        print(f"   Make sure Ollama is running on {settings.OLLAMA_URL}")
        return False
    
    # Test 2: Simple generation
    print("\n2. Testing simple generation...")
    prompt = "Say 'Hello, I am working!' and nothing else."
    response = await ollama_provider.generate(prompt, temperature=0.1, max_tokens=50)
    
    if response:
        print(f"   ✅ Response received: {response[:100]}")
    else:
        print(f"   ❌ No response received (empty string)")
        return False
    
    # Test 3: RAG-style generation
    print("\n3. Testing RAG-style generation...")
    rag_prompt = """You are a professional IT support specialist.

User ticket: I can't login to my account. It says password incorrect.
Category: Auth

Similar resolved ticket solution: Reset password via the password reset link. Check if account is locked after 3 failed attempts.

Write a professional support response in 3-4 sentences.
Be specific and actionable. Use numbered steps if needed.
"""
    
    rag_response = await ollama_provider.generate(rag_prompt, temperature=0.3, max_tokens=250)
    
    if rag_response:
        print(f"   ✅ RAG Response received ({len(rag_response)} chars):")
        print(f"   {rag_response[:200]}...")
    else:
        print(f"   ❌ No RAG response received")
        return False
    
    print("\n" + "=" * 50)
    print("✅ All tests passed! Ollama is working correctly.")
    return True

if __name__ == "__main__":
    result = asyncio.run(test_ollama())
    sys.exit(0 if result else 1)
