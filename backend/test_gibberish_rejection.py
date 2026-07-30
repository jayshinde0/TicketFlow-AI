"""
test_gibberish_rejection.py — Integration test for gibberish rejection.
Tests the Pydantic validator to ensure gibberish is rejected at the API level.
"""

from models.ticket import TicketCreate
from pydantic import ValidationError


def test_gibberish_rejection():
    """Test that gibberish input is rejected by the Pydantic validator"""
    
    print("="*80)
    print("GIBBERISH REJECTION INTEGRATION TEST")
    print("="*80)
    
    test_cases = [
        {
            "subject": "Valid subject",
            "description": "12345tygfdzxcdzfdffcsdfszdfcsz",
            "should_pass": False,
            "name": "Random gibberish"
        },
        {
            "subject": "Valid subject",
            "description": "qwertyuiopasdfghjkl",
            "should_pass": False,
            "name": "Keyboard mashing"
        },
        {
            "subject": "Need VPN access",
            "description": "I cannot connect to the VPN from home. Can you help me fix this issue?",
            "should_pass": True,
            "name": "Valid VPN issue"
        },
        {
            "subject": "1234567890",
            "description": "1234567890123456789012345",
            "should_pass": False,
            "name": "Only numbers"
        },
        {
            "subject": "Database timeout",
            "description": "The database connection keeps timing out after 30 seconds. Error code 1045.",
            "should_pass": True,
            "name": "Valid database issue"
        },
        {
            "subject": "test test test",
            "description": "test test test test test test test test",
            "should_pass": False,
            "name": "Excessive repetition"
        },
    ]
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        try:
            ticket = TicketCreate(
                subject=test_case["subject"],
                description=test_case["description"]
            )
            # If we get here, validation passed
            validation_passed = True
            error_msg = None
        except ValidationError as e:
            # Validation failed (caught an error)
            validation_passed = False
            error_msg = str(e.errors()[0]['msg'])
        
        expected_pass = test_case["should_pass"]
        test_passed = (validation_passed == expected_pass)
        
        if test_passed:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
        
        print(f"\n{status}: {test_case['name']}")
        print(f"  Subject: {test_case['subject']}")
        print(f"  Description: {test_case['description'][:60]}...")
        print(f"  Expected: {'ACCEPT' if expected_pass else 'REJECT'}")
        print(f"  Got: {'ACCEPT' if validation_passed else 'REJECT'}")
        if error_msg:
            print(f"  Error: {error_msg}")
    
    print("\n" + "="*80)
    print(f"SUMMARY: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("="*80)
    
    return failed == 0


if __name__ == "__main__":
    success = test_gibberish_rejection()
    
    if success:
        print("\n✅ All integration tests passed!")
        print("The Pydantic validator successfully rejects gibberish input.")
    else:
        print("\n❌ Some tests failed. Review the output above.")
    
    exit(0 if success else 1)
