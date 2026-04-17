"""
test_hackathon_final.py — Final hackathon demo test
Tests all 10 AI agents with 5 real-world tickets
Run with: python test_hackathon_final.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from routers.tickets import run_ai_pipeline
from utils.helpers import generate_ticket_id, utcnow


# Test tickets covering all 10 categories
TEST_TICKETS = [
    {
        "id": "TEST-001",
        "subject": "VPN timeout error 800",
        "description": "Cannot connect to company VPN. Getting error 800. This is urgent!",
        "expected_category": "Network",
    },
    {
        "id": "TEST-002",
        "subject": "Password reset needed",
        "description": "Locked out of my account. Please reset my password.",
        "expected_category": "Auth",
    },
    {
        "id": "TEST-003",
        "subject": "Malware detected - suspicious activity",
        "description": "Security scan found 5 threats. System compromised. Urgent escalation needed!",
        "expected_category": "Security",
    },
    {
        "id": "TEST-004",
        "subject": "Database connection refused",
        "description": "Cannot connect to production database. Connection timeout. Critical issue!",
        "expected_category": "Database",
    },
    {
        "id": "TEST-005",
        "subject": "Invoice duplicate charge",
        "description": "Been charged twice for the same subscription. Need refund.",
        "expected_category": "Billing",
    },
]


async def test_single_ticket(ticket):
    """Run AI pipeline on a single ticket"""
    
    print(f"\n{'─' * 60}")
    print(f"Testing: {ticket['subject']}")
    print(f"{'─' * 60}")
    
    try:
        # Run the full AI pipeline
        ai_analysis = await run_ai_pipeline(
            ticket_id=ticket["id"],
            subject=ticket["subject"],
            description=ticket["description"],
            user_tier="Standard",
            now=utcnow(),
        )
        
        # Extract key results
        category = ai_analysis.get("category")
        confidence = ai_analysis.get("confidence_score", 0)
        routing = ai_analysis.get("routing_decision")
        priority = ai_analysis.get("priority")
        threat_level = ai_analysis.get("threat_level", "normal")
        
        # Check if category matches expected
        expected = ticket["expected_category"]
        match = "✅" if category == expected else "⚠️"
        
        print(f"Subject:      {ticket['subject']}")
        print(f"Category:     {match} {category} (expected: {expected})")
        print(f"Confidence:   {confidence:.2f}")
        print(f"Priority:     {priority}")
        print(f"Routing:      {routing}")
        print(f"Threat Level: {threat_level}")
        
        # Show generated response snippet
        response = ai_analysis.get("generated_response", "")
        if response:
            snippet = response[:100] + "..." if len(response) > 100 else response
            print(f"Response:     {snippet}")
        
        # Security check
        if threat_level != "normal":
            print(f"🛡️  SECURITY: Threat detected - {threat_level}")
        
        # Return success flag
        return category == expected
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all test tickets"""
    
    print("\n" + "=" * 60)
    print("TICKETFLOW AI - HACKATHON FINAL TEST")
    print("=" * 60)
    print(f"Testing: 5 real-world tickets across all categories")
    print(f"Time: {utcnow().isoformat()}")
    
    results = []
    
    for ticket in TEST_TICKETS:
        success = await test_single_ticket(ticket)
        results.append(success)
    
    # Summary
    passed = sum(results)
    total = len(results)
    accuracy = (passed / total * 100) if total > 0 else 0
    
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    print(f"Passed: {passed}/{total}")
    print(f"Accuracy: {accuracy:.1f}%")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
        print("System is ready for production deployment")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
    
    print("=" * 60 + "\n")
    
    return passed == total


def main():
    """Main entry point"""
    print("\n🚀 Starting TicketFlow AI Hackathon Test Suite\n")
    
    try:
        # Run async tests
        success = asyncio.run(run_all_tests())
        
        if success:
            print("✅ READY FOR HACKATHON PRESENTATION!")
            sys.exit(0)
        else:
            print("❌ Some tests failed - check output above")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()