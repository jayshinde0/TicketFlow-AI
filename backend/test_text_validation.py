"""
test_text_validation.py — Test the gibberish detection and text validation.
"""

from services.text_validation_service import text_validation_service


def test_validation():
    """Test various inputs for validation"""
    
    test_cases = [
        # (text, should_pass, description)
        ("My laptop won't connect to the VPN", True, "Valid technical issue"),
        ("I can't access my email account", True, "Valid access issue"),
        ("The database connection keeps timing out", True, "Valid database issue"),
        ("12345tygfdzxcdzfdffcsdfszdfcsz", False, "Random gibberish"),
        ("1234567890", False, "Only numbers"),
        ("asdfghjkl", False, "Keyboard mashing"),
        ("qwertyuiop", False, "Keyboard pattern"),
        ("aaaaaaaaaaaaaaaa", False, "Repeated characters"),
        ("test test test test test", False, "Excessive repetition"),
        ("xyz abc def ghi jkl mno pqr", False, "Random letters with spaces"),
        ("zxcvbnmasdfghjkl", False, "Impossible consonant clusters"),
        ("hi", False, "Too short"),
        ("help me please urgent asap", True, "Valid short request"),
        ("123 456 789 password reset needed", True, "Valid with some numbers"),
        ("my computer is broken please fix it", True, "Valid simple issue"),
        ("fghdjkslghfjdksghfkjdshgfjkds", False, "Consonant-heavy gibberish"),
        ("The printer won't print and shows error 404", True, "Valid hardware issue"),
        ("abc def ghi jkl mno", False, "No meaningful words"),
        ("I need access to the shared folder", True, "Valid permission request"),
        ("12345678901234567890123456789012345", False, "Excessive digits"),
    ]
    
    print("="*80)
    print("TEXT VALIDATION TEST RESULTS")
    print("="*80)
    
    passed = 0
    failed = 0
    
    for text, expected_valid, description in test_cases:
        is_valid, error_msg = text_validation_service.validate(text, min_words=3)
        
        # Check if result matches expectation
        test_passed = (is_valid == expected_valid)
        
        if test_passed:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
        
        print(f"\n{status}")
        print(f"  Input: '{text[:60]}{'...' if len(text) > 60 else ''}'")
        print(f"  Expected: {'VALID' if expected_valid else 'INVALID'}")
        print(f"  Got: {'VALID' if is_valid else 'INVALID'}")
        if not is_valid:
            print(f"  Error: {error_msg}")
        print(f"  Description: {description}")
    
    print("\n" + "="*80)
    print(f"SUMMARY: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("="*80)
    
    return failed == 0


if __name__ == "__main__":
    success = test_validation()
    exit(0 if success else 1)
