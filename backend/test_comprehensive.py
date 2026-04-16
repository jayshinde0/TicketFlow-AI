"""
Comprehensive test suite for TicketFlow AI pipeline.
Tests all categories, edge cases, and scenarios.
"""

import asyncio
from services.nlp_service import nlp_service
from services.classifier_service import classifier_service
from services.confidence_service import confidence_service
from services.sentiment_service import sentiment_service
from services.sla_service import sla_service
from services.hitl_service import hitl_service
from utils.helpers import utcnow

# Test data: (ticket_text, expected_category, description)
TEST_CASES = [
    # ═══════════════════════════════════════════════════════════════
    # NETWORK (10 cases)
    # ═══════════════════════════════════════════════════════════════
    (
        "I cannot connect to the company VPN. I get a timeout error after entering my credentials. This is blocking my work completely.",
        "Network",
        "VPN Connection Timeout - High Priority"
    ),
    (
        "WiFi keeps disconnecting on the 5th floor. Signal is very weak. Multiple people affected.",
        "Network",
        "WiFi Connectivity Issue - Multiple Users"
    ),
    (
        "DNS resolution failing. Cannot reach external websites. Internal sites work fine.",
        "Network",
        "DNS Resolution Failure"
    ),
    (
        "Firewall blocking access to GitHub. Need port 443 opened. Development blocked.",
        "Network",
        "Firewall Blocking Port - Dev Impact"
    ),
    (
        "Internet down since 10am. Phone line also affected. Need urgent fix.",
        "Network",
        "Complete Internet Outage - Critical"
    ),

    # ═══════════════════════════════════════════════════════════════
    # AUTH / Authentication (10 cases)
    # ═══════════════════════════════════════════════════════════════
    (
        "I forgot my password. Cannot login to the system. Getting 'invalid credentials' error.",
        "Auth",
        "Password Reset Request"
    ),
    (
        "My account is locked. I've tried 5 times to login. Need unlock immediately.",
        "Auth",
        "Account Locked - Multiple Failed Attempts"
    ),
    (
        "2FA token not working. App not generating codes. Cannot access account.",
        "Auth",
        "2FA Token Generation Failure"
    ),
    (
        "SSO integration broken. Cannot login with company credentials. Auth service down?",
        "Auth",
        "SSO Integration Failure"
    ),
    (
        "OTP not arriving via SMS. Tried 3 times. Need alternative verification.",
        "Auth",
        "OTP Delivery Failure"
    ),

    # ═══════════════════════════════════════════════════════════════
    # SECURITY (10 cases)
    # ═══════════════════════════════════════════════════════════════
    (
        "URGENT: Received suspicious email with phishing link asking for password. Looks legitimate but sender domain is wrong.",
        "Security",
        "Phishing Email Detection - Urgent"
    ),
    (
        "My laptop has malware. Kaspersky detected 5 threats. System running slow.",
        "Security",
        "Malware Infection - Desktop"
    ),
    (
        "CRITICAL: Data breach notification. 500 user records may be exposed. Database compromised.",
        "Security",
        "Data Breach - Critical Incident"
    ),
    (
        "SQL injection vulnerability found in login form. Attacker can bypass authentication.",
        "Security",
        "SQL Injection Vulnerability"
    ),
    (
        "Ransomware detected on server. Files encrypted. Bitcoin ransom demanded. HELP!",
        "Security",
        "Ransomware Attack - Critical"
    ),

    # ═══════════════════════════════════════════════════════════════
    # DATABASE (10 cases)
    # ═══════════════════════════════════════════════════════════════
    (
        "Database query taking 45 seconds. Usually 2 seconds. SELECT * FROM users WHERE status = 'active'.",
        "Database",
        "Slow Query Performance"
    ),
    (
        "MySQL server crashed. Service not responding. Cannot restart. Disk space issue?",
        "Database",
        "Database Server Down - Disk Full"
    ),
    (
        "Replication lag detected. Master 100GB ahead of slave. Replication thread stopped.",
        "Database",
        "Database Replication Failure"
    ),
    (
        "Backup failed last night. Error: disk full. No recent backup available.",
        "Database",
        "Backup Failure - Critical"
    ),
    (
        "Data corruption in transactions table. Rows showing NULL values. Checksum mismatch.",
        "Database",
        "Data Corruption Detected"
    ),

    # ═══════════════════════════════════════════════════════════════
    # BILLING (10 cases)
    # ═══════════════════════════════════════════════════════════════
    (
        "I was charged twice for last month's subscription. Invoice shows duplicate entries. Total $200 instead of $100.",
        "Billing",
        "Duplicate Charges"
    ),
    (
        "Refund requested 2 weeks ago but status shows pending. When will it process?",
        "Billing",
        "Pending Refund"
    ),
    (
        "Payment method expired. System won't accept new credit card. Getting payment failed error.",
        "Billing",
        "Payment Method Issue"
    ),
    (
        "Invoice for March 2026 has wrong amount. Should be $500, showing $750. Audit needed.",
        "Billing",
        "Invoice Amount Discrepancy"
    ),
    (
        "Subscription upgrade not applied. Still on Basic plan but charged Enterprise rate.",
        "Billing",
        "Subscription Tier Mismatch"
    ),

    # ═══════════════════════════════════════════════════════════════
    # SOFTWARE (10 cases)
    # ═══════════════════════════════════════════════════════════════
    (
        "Application crashes when opening large PDF files. Error: memory exception. Happens 100% of the time.",
        "Software",
        "Application Crash - Memory Issue"
    ),
    (
        "Software update failed. Installation stuck at 45%. Need to rollback.",
        "Software",
        "Update Installation Failure"
    ),
    (
        "System freezes for 10 seconds every 5 minutes. High CPU usage. Process viewer shows unknown.exe.",
        "Software",
        "System Performance Issues"
    ),
    (
        "Bug in report generation. Charts not displaying. Data is there but visualization broken.",
        "Software",
        "UI Rendering Bug"
    ),
    (
        "Console shows 50+ JavaScript errors. Application very slow. Need debugging.",
        "Software",
        "JavaScript Errors - Performance Degradation"
    ),

    # ═══════════════════════════════════════════════════════════════
    # HARDWARE (10 cases)
    # ═══════════════════════════════════════════════════════════════
    (
        "Laptop screen flickering constantly. Sometimes goes black. Still under warranty.",
        "Hardware",
        "Monitor Display Failure"
    ),
    (
        "Keyboard keys not responding. Q, W, E keys stuck. Need replacement.",
        "Hardware",
        "Keyboard Malfunction"
    ),
    (
        "Battery not charging. Plugged in but showing 5% battery. Been like this for hours.",
        "Hardware",
        "Battery Charging Issue"
    ),
    (
        "USB ports not working. Cannot connect external drive. All ports same issue.",
        "Hardware",
        "USB Port Failure"
    ),
    (
        "Hard drive making clicking sounds. System running very slow. Backup needed immediately.",
        "Hardware",
        "Hard Drive Failure - Urgent Backup"
    ),

    # ═══════════════════════════════════════════════════════════════
    # EMAIL (10 cases)
    # ═══════════════════════════════════════════════════════════════
    (
        "Email not sending. Getting timeout error. SMTP server not responding.",
        "Email",
        "SMTP Delivery Failure"
    ),
    (
        "Inbox not syncing with mobile. Desktop shows 100 new emails, phone shows 0.",
        "Email",
        "Email Synchronization Failure"
    ),
    (
        "Attachments not downloading. Getting corrupted file errors. File size shows 0 bytes.",
        "Email",
        "Email Attachment Download Issue"
    ),
    (
        "Spam filter too aggressive. Legitimate emails marked as spam. Whelist not working.",
        "Email",
        "Spam Filter Configuration Issue"
    ),
    (
        "Calendar not accepting meeting invites. Sync broken with Outlook.",
        "Email",
        "Calendar Integration Failure"
    ),

    # ═══════════════════════════════════════════════════════════════
    # ACCESS / Permissions (10 cases)
    # ═══════════════════════════════════════════════════════════════
    (
        "Cannot access the Finance folder. Getting 'access denied' error. Need permission from manager.",
        "Access",
        "Folder Permission Denied"
    ),
    (
        "User removed from admin group but still has access. Permission revocation not working.",
        "Access",
        "Permission Revocation Failure"
    ),
    (
        "New employee cannot access any shared drives. AD group membership issue?",
        "Access",
        "New User Access Provisioning"
    ),
    (
        "Cannot write to shared folder. Read-only permission issue. Need write access.",
        "Access",
        "Write Permission Issue"
    ),
    (
        "Group policy not applying. Restricted software still accessible. Need GPO update.",
        "Access",
        "Group Policy Not Enforced"
    ),

    # ═══════════════════════════════════════════════════════════════
    # SERVICE REQUEST (10 cases)
    # ═══════════════════════════════════════════════════════════════
    (
        "Please set up a new email account for the new hire. Name: John Doe. Department: Engineering.",
        "ServiceRequest",
        "New User Email Setup"
    ),
    (
        "Need new laptop provisioned. Windows 11, 16GB RAM, 512GB SSD. For Developer role.",
        "ServiceRequest",
        "New Hardware Request"
    ),
    (
        "Can you please enable MFA for my account? I want to use authenticator app.",
        "ServiceRequest",
        "MFA Enablement Request"
    ),
    (
        "New conference room needs projector installed. Room 401. Please schedule installation.",
        "ServiceRequest",
        "Equipment Installation Request"
    ),
    (
        "Request to upgrade my Office 365 license to include Teams premium features.",
        "ServiceRequest",
        "License Upgrade Request"
    ),

    # ═══════════════════════════════════════════════════════════════
    # EDGE CASES & MIXED SIGNALS
    # ═══════════════════════════════════════════════════════════════
    (
        "VPN timeout and billing issue. Cannot connect and I was charged twice.",
        "Network",
        "Mixed Issue - Primary: Network"
    ),
    (
        "URGENT: Cannot access system. Email not working. Phone down. Everything broken!",
        "Network",
        "Multiple Outages - Escalation Needed"
    ),
    (
        "okay so like the thing is not working you know? can you help me fix it?",
        "Software",
        "Vague Description - Low Quality"
    ),
    (
        "Everything is perfect! Just wanted to say great job on the new update!",
        "ServiceRequest",
        "Positive Feedback - Not a Real Issue"
    ),
]


async def run_comprehensive_tests():
    """Run all test cases through the pipeline."""
    
    print("\n" + "="*80)
    print("COMPREHENSIVE TICKETFLOW AI TEST SUITE")
    print("="*80)
    
    results = {
        "passed": 0,
        "failed": 0,
        "by_category": {},
        "failures": [],
    }
    
    for i, (ticket_text, expected_category, description) in enumerate(TEST_CASES, 1):
        print(f"\n[TEST {i}/{len(TEST_CASES)}] {description}")
        print(f"  Expected: {expected_category}")
        
        try:
            # NLP Preprocessing
            nlp_result = await nlp_service.preprocess_async(ticket_text)
            cleaned_text = nlp_result["cleaned_text"]
            features = nlp_result["features"]
            
            # Classification
            classify_result = classifier_service.classify(
                cleaned_text=cleaned_text,
                user_tier="Standard",
                submission_hour=10,
                word_count=features["word_count"],
                urgency_keyword_count=features["urgency_keyword_count"],
                sentiment_score=0.5,
            )
            
            predicted_category = classify_result["category"]
            model_confidence = classify_result["model_confidence"]
            priority = classify_result["priority"]
            
            # Sentiment analysis
            sentiment_result = await sentiment_service.analyze_async(ticket_text)
            sentiment_label = sentiment_result["sentiment_label"]
            sentiment_score = sentiment_result["sentiment_score"]
            
            # SLA prediction
            sla_breach_prob = sla_service.predict_breach_probability(
                category=predicted_category,
                priority=priority,
                user_tier="Standard",
                submission_hour=10,
                submission_day=0,
                word_count=features["word_count"],
                urgency_keyword_count=features["urgency_keyword_count"],
                sentiment_score=sentiment_score,
                current_queue_length=5,
                similar_ticket_avg_hours=2.0,
            )
            
            # Confidence & routing
            confidence_result = confidence_service.compute(
                model_confidence=model_confidence,
                similarity_score=0.75,  # Assume good similarity for now
                ticket_text=ticket_text,
                category=predicted_category,
                sentiment_label=sentiment_label,
                sentiment_score=sentiment_score,
                sla_breach_probability=sla_breach_prob,
                user_tier="Standard",
            )
            
            routing_decision = confidence_result["routing_decision"]
            confidence_score = confidence_result["confidence_score"]
            
            # Check result
            match = "✓" if predicted_category == expected_category else "✗"
            status = "PASS" if predicted_category == expected_category else "FAIL"
            
            print(f"  Predicted: {predicted_category} {match}")
            print(f"  Confidence: {model_confidence:.2f} | Composite: {confidence_score:.2f}")
            print(f"  Priority: {priority} | Routing: {routing_decision}")
            print(f"  Sentiment: {sentiment_label} ({sentiment_score:.2f})")
            print(f"  SLA Breach Prob: {sla_breach_prob:.2f}")
            print(f"  Status: {status}")
            
            # Track results
            if predicted_category not in results["by_category"]:
                results["by_category"][predicted_category] = {"pass": 0, "fail": 0}
            
            if status == "PASS":
                results["passed"] += 1
                results["by_category"][predicted_category]["pass"] += 1
            else:
                results["failed"] += 1
                results["by_category"][predicted_category]["fail"] += 1
                results["failures"].append({
                    "test": i,
                    "description": description,
                    "expected": expected_category,
                    "predicted": predicted_category,
                })
        
        except Exception as e:
            print(f"  Status: ERROR - {str(e)}")
            results["failed"] += 1
            results["failures"].append({
                "test": i,
                "description": description,
                "error": str(e),
            })
    
    # Summary Report
    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)
    
    total = results["passed"] + results["failed"]
    pass_rate = (results["passed"] / total * 100) if total > 0 else 0
    
    print(f"\nOverall: {results['passed']}/{total} PASSED ({pass_rate:.1f}%)")
    
    print("\nBy Category:")
    for category in sorted(results["by_category"].keys()):
        stats = results["by_category"][category]
        cat_total = stats["pass"] + stats["fail"]
        cat_pass_rate = (stats["pass"] / cat_total * 100) if cat_total > 0 else 0
        print(f"  {category:15} → {stats['pass']}/{cat_total} ({cat_pass_rate:5.1f}%)")
    
    if results["failures"]:
        print("\nFailed Tests:")
        for failure in results["failures"]:
            if "error" in failure:
                print(f"  Test {failure['test']}: {failure['description']} - ERROR: {failure['error']}")
            else:
                print(f"  Test {failure['test']}: {failure['description']}")
                print(f"    Expected: {failure['expected']}, Got: {failure['predicted']}")
    
    print("\n" + "="*80)
    
    return results


if __name__ == "__main__":
    asyncio.run(run_comprehensive_tests())