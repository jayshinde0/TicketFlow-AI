"""
Test the trained models against realistic real-world ticket examples.
This reveals overfitting by testing on tickets that don't match training templates.

Run with: python test_real_world.py
"""

import sys
from pathlib import Path
from loguru import logger
import joblib

sys.path.insert(0, str(Path(__file__).parent))

from ml.models.category_classifier import CategoryClassifier
from ml.models.priority_classifier import PriorityClassifier
from ml.feature_engineering import FeatureEngineer
from ml.train import preprocess_texts

# ═══ Real-world tickets with messy, ambiguous descriptions ═══════════════

REAL_WORLD_TICKETS = [
    # Vague/ambiguous descriptions
    {
        "text": "hi its not working can u help",
        "expected_category": "Unknown/Ambiguous",
        "notes": "Too vague - could be anything"
    },
    {
        "text": "Hey guys, having some issues with the thing we talked about yesterday. Still broken.",
        "expected_category": "Unknown/Ambiguous", 
        "notes": "No context, unclear issue"
    },
    {
        "text": "everything is slow today",
        "expected_category": "Network or Software",
        "notes": "Could be network latency or app performance"
    },
    
    # Mixed/multiple issues in one ticket
    {
        "text": "Can't login to my email and also my laptop keyboard isn't working properly",
        "expected_category": "Auth + Hardware",
        "notes": "Two separate issues - Auth and Hardware"
    },
    {
        "text": "VPN won't connect, tried resetting password but now account is locked",
        "expected_category": "Network + Auth",
        "notes": "Network issue led to Auth issue"
    },
    {
        "text": "After the software update my printer stopped working and I can't access the shared drive",
        "expected_category": "Software + Hardware + Access",
        "notes": "Multiple cascading issues"
    },
    
    # Typos and informal language
    {
        "text": "cant recieve emails from clients idk y this is hapening plz fix asap!!!",
        "expected_category": "Email",
        "notes": "Typos: recieve->receive, y->why, hapening->happening"
    },
    {
        "text": "the databse is super slow rn and queries r timing out",
        "expected_category": "Database",
        "notes": "Typos: databse->database, rn->right now, r->are"
    },
    {
        "text": "my laptpo keybord has a sticki spacbar key",
        "expected_category": "Hardware",
        "notes": "Multiple typos demonstrating the problem"
    },
    
    # Different wording than training data
    {
        "text": "I forgot my credentials and can't sign into the system",
        "expected_category": "Auth",
        "notes": "Similar to Auth but different vocabulary"
    },
    {
        "text": "Need permissions to view the financial reports folder",
        "expected_category": "Access",
        "notes": "Access request but different phrasing"
    },
    {
        "text": "Getting charged duplicate amounts on my company credit card",
        "expected_category": "Billing",
        "notes": "Billing issue with different wording"
    },
    {
        "text": "Suspicious message asking me to verify my identity by clicking a link",
        "expected_category": "Security",
        "notes": "Phishing but not using exact keywords"
    },
    
    # Context-dependent or domain-specific jargon
    {
        "text": "Jenkins pipeline failing on deploy stage, getting 403 forbidden",
        "expected_category": "Software or Access",
        "notes": "DevOps context, could be permissions or software bug"
    },
    {
        "text": "Kubernetes pod keeps crashing with OOMKilled status",
        "expected_category": "Software or Database",
        "notes": "Technical infrastructure issue"
    },
    {
        "text": "SAML assertion failed when trying to access dashboard",
        "expected_category": "Auth",
        "notes": "Technical SSO issue"
    },
    
    # Borderline cases between categories
    {
        "text": "Server is down, can't access any applications",
        "expected_category": "Database or Network or Software",
        "notes": "Could fit multiple categories"
    },
    {
        "text": "My files disappeared after the system restart",
        "expected_category": "Hardware or Software or Database",
        "notes": "Could be disk issue, software bug, or data loss"
    },
    {
        "text": "Need software installed on new laptop for remote work",
        "expected_category": "ServiceRequest or Software",
        "notes": "Request type, could go either way"
    },
    
    # Customer service tone (less common in IT tickets)
    {
        "text": "Hello, I hope you're having a great day! I was wondering if perhaps someone might be able to assist me with a small matter regarding my account access. No rush at all, whenever you have a moment. Thank you so much!",
        "expected_category": "Access",
        "notes": "Overly polite, buried information"
    },
    
    # Passive aggressive or emotional
    {
        "text": "This is the THIRD TIME I'm reporting this. My email is STILL not working. This is completely unacceptable and affecting my ability to do my job.",
        "expected_category": "Email",
        "notes": "Emotional tone, repeated issue"
    },
    
    # Technical error messages without context
    {
        "text": "Error: Failed to fetch. Status code: 500. Please help?",
        "expected_category": "Software or Network",
        "notes": "Generic error, no context"
    },
    {
        "text": "Getting bluescreens with error DRIVER_IRQL_NOT_LESS_OR_EQUAL",
        "expected_category": "Hardware or Software",
        "notes": "Windows BSOD - could be driver or hardware"
    },
    
    # Non-English or mixed language
    {
        "text": "No puedo iniciar sesión, password reset not working",
        "expected_category": "Auth",
        "notes": "Spanish + English mix"
    },
    
    # Questions instead of problems
    {
        "text": "How do I set up my work email on my personal phone?",
        "expected_category": "Email or ServiceRequest",
        "notes": "How-to question, not a problem report"
    },
    {
        "text": "What's the process for getting access to the production environment?",
        "expected_category": "Access or ServiceRequest",
        "notes": "Process question"
    },
    
    # Edge cases
    {
        "text": "",
        "expected_category": "Invalid",
        "notes": "Empty ticket"
    },
    {
        "text": "test test test 123",
        "expected_category": "Invalid",
        "notes": "Spam/test ticket"
    },
    {
        "text": "asdfghjkl",
        "expected_category": "Invalid",
        "notes": "Random characters"
    },
]


def test_model_on_real_world():
    """Test category classifier on realistic tickets."""
    
    logger.info("Loading trained models...")
    
    try:
        cat_clf = CategoryClassifier.load()
        priority_clf = PriorityClassifier.load()
        
        # Load the TF-IDF vectorizer
        artifact_dir = Path(__file__).parent / "ml" / "artifacts"
        tfidf_path = artifact_dir / "tfidf_vectorizer.pkl"
        fe: FeatureEngineer = joblib.load(tfidf_path)
        
    except FileNotFoundError as e:
        logger.error(f"Model files not found. Run ml/train.py first. Error: {e}")
        return
    
    logger.info("=" * 80)
    logger.info("REAL-WORLD TICKET TEST RESULTS")
    logger.info("=" * 80)
    
    correct_predictions = 0
    total_clear_cases = 0  # Only count tickets with clear expected categories
    
    for i, ticket in enumerate(REAL_WORLD_TICKETS, 1):
        text = ticket["text"]
        expected = ticket["expected_category"]
        notes = ticket["notes"]
        
        # Skip invalid/ambiguous test cases for accuracy calculation
        if expected in ["Invalid", "Unknown/Ambiguous"] or "or" in expected or "+" in expected:
            count_for_accuracy = False
        else:
            count_for_accuracy = True
            total_clear_cases += 1
        
        logger.info(f"\n{'─' * 80}")
        logger.info(f"Test #{i}")
        logger.info(f"Ticket: \"{text[:100]}{'...' if len(text) > 100 else ''}\"")
        logger.info(f"Expected: {expected}")
        logger.info(f"Notes: {notes}")
        
        if not text or len(text.strip()) < 3:
            logger.info("Result: [SKIPPED - Invalid input]")
            continue
        
        try:
            # Preprocess and predict category
            processed_text = preprocess_texts([text])
            X = fe.transform(processed_text)
            
            # Predict category - returns (category, confidence, prob_dict)
            predicted_category, confidence, prob_dict = cat_clf.predict(X)
            
            # Predict priority
            predicted_priority = priority_clf.predict(processed_text[0], predicted_category)
            
            logger.info(f"Predicted Category: {predicted_category} (confidence: {confidence:.2%})")
            logger.info(f"Predicted Priority: {predicted_priority}")
            
            # Check if correct (for single-category expectations)
            if count_for_accuracy:
                if predicted_category == expected:
                    logger.info("✓ CORRECT")
                    correct_predictions += 1
                else:
                    logger.info("✗ INCORRECT")
            else:
                logger.info("⊘ NOT SCORED (ambiguous/multi-category/invalid)")
                
        except Exception as e:
            logger.error(f"Error processing ticket: {e}")
            logger.info("Result: [ERROR]")
    
    logger.info(f"\n{'═' * 80}")
    logger.info("SUMMARY")
    logger.info(f"{'═' * 80}")
    
    if total_clear_cases > 0:
        accuracy = (correct_predictions / total_clear_cases) * 100
        logger.info(f"Clear test cases: {total_clear_cases}")
        logger.info(f"Correct predictions: {correct_predictions}")
        logger.info(f"Real-world accuracy: {accuracy:.1f}%")
        logger.info(f"\nTraining accuracy was: 100%")
        logger.info(f"Real-world accuracy is: {accuracy:.1f}%")
        logger.info(f"Performance gap: {100 - accuracy:.1f}% (indicates overfitting)")
    else:
        logger.info("No clear test cases to calculate accuracy")
    
    logger.info(f"\n{'═' * 80}")


if __name__ == "__main__":
    test_model_on_real_world()
