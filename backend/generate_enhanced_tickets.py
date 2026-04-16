"""
Enhanced Demo Ticket Generator - High Confidence Tickets for All 10 Domains
Creates 30+ tickets with domain-specific keywords for better confidence scores
"""

import asyncio
import sys
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
from models.ticket import TicketStatus
import random

# High-confidence tickets for each domain (3 per domain = 30 tickets)
ENHANCED_TICKETS = [
    # ═══════════════════════════════════════════════════════════════
    # NETWORK DOMAIN (3 tickets)
    # ═══════════════════════════════════════════════════════════════
    {
        "title": "VPN connection timeout error",
        "description": "Cannot connect to company VPN. Getting connection timeout error after 30 seconds. VPN client shows 'Connecting...' then fails. Tried restarting VPN service and router. Network connectivity is fine for other applications. Using Cisco AnyConnect VPN client version 4.10. Need VPN access for remote work urgently.",
        "category": "Network",
        "priority": "High",
        "keywords": [
            "vpn",
            "connection",
            "timeout",
            "network",
            "connectivity",
            "cisco",
            "remote",
        ],
    },
    {
        "title": "WiFi keeps disconnecting every 10 minutes",
        "description": "Office WiFi network keeps disconnecting every 10-15 minutes. Have to manually reconnect each time. Signal strength shows full bars. Other devices on same network work fine. Laptop is Dell Latitude 5520. WiFi adapter driver is up to date. This started happening after Windows update yesterday.",
        "category": "Network",
        "priority": "Medium",
        "keywords": [
            "wifi",
            "disconnecting",
            "network",
            "wireless",
            "connectivity",
            "internet",
        ],
    },
    {
        "title": "Cannot access company intranet portal",
        "description": "Unable to access company intranet portal at portal.company.com. Browser shows 'Connection timed out' error. Tried different browsers (Chrome, Edge, Firefox). Can access other websites fine. Cleared browser cache and cookies. Firewall settings unchanged. Need access to submit timesheet before deadline.",
        "category": "Network",
        "priority": "High",
        "keywords": [
            "intranet",
            "portal",
            "network",
            "connection",
            "timeout",
            "firewall",
            "access",
        ],
    },
    # ═══════════════════════════════════════════════════════════════
    # AUTH DOMAIN (3 tickets)
    # ═══════════════════════════════════════════════════════════════
    {
        "title": "Forgot password - cannot login",
        "description": "Forgot my account password and cannot login. Tried password reset link but not receiving reset email. Checked spam folder - nothing there. My email is john.doe@company.com. Account username is jdoe. Need urgent access to complete project deliverables today.",
        "category": "Auth",
        "priority": "High",
        "keywords": [
            "password",
            "forgot",
            "reset",
            "login",
            "authentication",
            "account",
            "access",
        ],
    },
    {
        "title": "Account locked after failed login attempts",
        "description": "My account got locked after 3 failed login attempts. I was using wrong password by mistake. Now getting 'Account locked' message. Username is sarah.smith. Need account unlocked immediately. Have important client meeting in 30 minutes and need access to presentation files.",
        "category": "Auth",
        "priority": "Critical",
        "keywords": [
            "account",
            "locked",
            "login",
            "authentication",
            "password",
            "access",
            "unlock",
        ],
    },
    {
        "title": "Two-factor authentication not working",
        "description": "2FA authentication code not working. Entering correct 6-digit code from authenticator app but getting 'Invalid code' error. Tried multiple times. Authenticator app is Microsoft Authenticator. Phone time is synced correctly. Cannot login without 2FA. Need alternative authentication method or 2FA reset.",
        "category": "Auth",
        "priority": "High",
        "keywords": [
            "2fa",
            "two-factor",
            "authentication",
            "mfa",
            "login",
            "code",
            "authenticator",
        ],
    },
    # ═══════════════════════════════════════════════════════════════
    # SOFTWARE DOMAIN (3 tickets)
    # ═══════════════════════════════════════════════════════════════
    {
        "title": "Microsoft Excel crashing when opening large files",
        "description": "Excel 2021 crashes immediately when opening spreadsheets larger than 50MB. Error message: 'Excel has stopped working'. Tried repairing Office installation through Control Panel. Issue persists. Need to work on quarterly financial reports. Files open fine on colleague's computer. Windows 11 Pro, 16GB RAM.",
        "category": "Software",
        "priority": "High",
        "keywords": [
            "excel",
            "crash",
            "software",
            "application",
            "office",
            "spreadsheet",
            "error",
        ],
    },
    {
        "title": "Need Adobe Acrobat Pro installed",
        "description": "Need Adobe Acrobat Pro DC installed on my workstation for PDF editing. I'm in Marketing department and need to edit client proposals. Manager approved this software request. My computer is HP EliteDesk 800 G6. Windows 10 Pro. Have license key ready.",
        "category": "Software",
        "priority": "Medium",
        "keywords": [
            "adobe",
            "acrobat",
            "software",
            "install",
            "application",
            "pdf",
            "license",
        ],
    },
    {
        "title": "Zoom application not launching",
        "description": "Zoom desktop application won't launch. Double-clicking icon does nothing. Tried uninstalling and reinstalling - same issue. Zoom web version works but need desktop app for screen sharing features. Have important client presentation in 2 hours. Windows 10, Zoom version 5.16.5.",
        "category": "Software",
        "priority": "Critical",
        "keywords": [
            "zoom",
            "application",
            "software",
            "launch",
            "install",
            "meeting",
            "crash",
        ],
    },
    # ═══════════════════════════════════════════════════════════════
    # HARDWARE DOMAIN (3 tickets)
    # ═══════════════════════════════════════════════════════════════
    {
        "title": "Laptop keyboard keys not working",
        "description": "Several keys on laptop keyboard stopped working (E, R, T, Y keys). Tried external USB keyboard - works fine. Laptop is Dell Latitude 7420. Keyboard was working fine until yesterday. No liquid spills. Need keyboard replacement or repair. Laptop is under warranty.",
        "category": "Hardware",
        "priority": "High",
        "keywords": [
            "keyboard",
            "laptop",
            "hardware",
            "keys",
            "device",
            "repair",
            "replacement",
        ],
    },
    {
        "title": "Office printer not printing - paper jam error",
        "description": "HP LaserJet Pro printer on 3rd floor showing 'Paper Jam in Tray 2' error. Checked all trays - no paper stuck. Turned printer off and on. Error persists. Printer model: HP LaserJet Pro M404dn. Multiple people need to print urgent documents. Printer was working fine this morning.",
        "category": "Hardware",
        "priority": "High",
        "keywords": [
            "printer",
            "hardware",
            "paper jam",
            "device",
            "printing",
            "error",
            "laserjet",
        ],
    },
    {
        "title": "Monitor screen flickering constantly",
        "description": "External monitor screen flickering constantly. Tried different HDMI cable - same issue. Monitor is Dell UltraSharp 27 inch. Flickering started after power outage yesterday. Laptop screen works fine. Monitor power LED is on. Very distracting during work. Need monitor replacement if cannot be fixed.",
        "category": "Hardware",
        "priority": "Medium",
        "keywords": [
            "monitor",
            "screen",
            "flickering",
            "hardware",
            "display",
            "device",
            "hdmi",
        ],
    },
    # ═══════════════════════════════════════════════════════════════
    # ACCESS DOMAIN (3 tickets)
    # ═══════════════════════════════════════════════════════════════
    {
        "title": "Need access to shared Marketing folder",
        "description": "Need read/write access to Marketing shared folder on network drive (\\\\fileserver\\marketing). My manager Sarah Johnson approved this access request. I'm working on Q1 campaign materials. My username is mjones. Department: Marketing. Start date: 2024-01-15.",
        "category": "Access",
        "priority": "Medium",
        "keywords": [
            "access",
            "permission",
            "shared folder",
            "network drive",
            "authorization",
            "grant",
        ],
    },
    {
        "title": "Cannot access Salesforce CRM",
        "description": "Getting 'Access Denied' error when trying to login to Salesforce CRM. Was able to access yesterday. No password changes. Other team members can access fine. Need access urgently for client follow-ups. Username: robert.chen@company.com. Sales department.",
        "category": "Access",
        "priority": "High",
        "keywords": [
            "access",
            "salesforce",
            "crm",
            "permission",
            "denied",
            "authorization",
            "login",
        ],
    },
    {
        "title": "Need admin rights to install software",
        "description": "Need temporary admin rights to install development tools (Visual Studio Code, Git, Node.js). I'm a new developer in Engineering team. Manager David Lee approved. My username is asmith. Computer: LAPTOP-DEV-042. Windows 11 Pro.",
        "category": "Access",
        "priority": "Medium",
        "keywords": [
            "admin",
            "rights",
            "access",
            "permission",
            "install",
            "authorization",
            "privileges",
        ],
    },
    # ═══════════════════════════════════════════════════════════════
    # BILLING DOMAIN (3 tickets)
    # ═══════════════════════════════════════════════════════════════
    {
        "title": "Duplicate charge on company credit card",
        "description": "Noticed duplicate charge of $299.99 on company credit card statement for Microsoft 365 subscription. Transaction appears twice on same date (March 15). Invoice number: INV-2024-0315. Need refund for duplicate charge. Card ending in 4532. Finance department needs this resolved for month-end closing.",
        "category": "Billing",
        "priority": "High",
        "keywords": [
            "billing",
            "charge",
            "duplicate",
            "refund",
            "payment",
            "invoice",
            "subscription",
        ],
    },
    {
        "title": "Cannot download invoice for expense report",
        "description": "Need to download invoice for software purchase but getting error on billing portal. Transaction ID: TXN-20240320-1234. Amount: $149.99. Need invoice PDF for expense reimbursement. Tried different browsers. Portal shows 'Invoice not found' error. Purchase was made last week.",
        "category": "Billing",
        "priority": "Medium",
        "keywords": [
            "invoice",
            "billing",
            "download",
            "payment",
            "expense",
            "transaction",
            "receipt",
        ],
    },
    {
        "title": "Subscription renewal failed - payment declined",
        "description": "Received email that subscription renewal payment was declined. Card on file is valid and has sufficient funds. Subscription: Adobe Creative Cloud Team. Need to update payment method or retry charge. Service will be suspended in 3 days. Account ID: ACC-2024-5678.",
        "category": "Billing",
        "priority": "High",
        "keywords": [
            "billing",
            "payment",
            "subscription",
            "renewal",
            "declined",
            "charge",
            "card",
        ],
    },
    # ═══════════════════════════════════════════════════════════════
    # EMAIL DOMAIN (3 tickets)
    # ═══════════════════════════════════════════════════════════════
    {
        "title": "Outlook not syncing new emails",
        "description": "Outlook 2021 stopped syncing new emails since yesterday evening. Can send emails but not receiving new ones. Checked webmail - emails are there. Tried Send/Receive button multiple times. Restarted Outlook and computer. Internet connection is fine. Using Exchange server. Need email sync working for client communications.",
        "category": "Email",
        "priority": "High",
        "keywords": [
            "outlook",
            "email",
            "sync",
            "mail",
            "exchange",
            "inbox",
            "receiving",
        ],
    },
    {
        "title": "Email attachment size limit error",
        "description": "Cannot send email with 30MB PDF attachment. Getting error: 'Attachment size exceeds limit'. Need to send proposal document to client urgently. File is too large to compress further. Is there way to increase attachment limit or alternative method to share large files? Using Outlook 2021.",
        "category": "Email",
        "priority": "Medium",
        "keywords": [
            "email",
            "attachment",
            "size limit",
            "outlook",
            "mail",
            "send",
            "file",
        ],
    },
    {
        "title": "Emails going to spam folder automatically",
        "description": "Important emails from clients going to spam folder automatically. Marked as 'Not Spam' multiple times but keeps happening. Missing important client communications. Email addresses are from legitimate domains. Need spam filter adjusted. Using Outlook with Exchange Online. This started 3 days ago.",
        "category": "Email",
        "priority": "High",
        "keywords": ["email", "spam", "filter", "inbox", "mail", "outlook", "junk"],
    },
    # ═══════════════════════════════════════════════════════════════
    # SECURITY DOMAIN (3 tickets)
    # ═══════════════════════════════════════════════════════════════
    {
        "title": "Suspicious phishing email received",
        "description": "Received suspicious email claiming to be from IT department asking to verify account credentials by clicking link. Email has spelling errors and sender address looks fake (it-support@company-verify.com). Did not click any links. Reporting for security team investigation. Other employees may have received same email. Forwarding email to security@company.com.",
        "category": "Security",
        "priority": "Critical",
        "keywords": [
            "security",
            "phishing",
            "suspicious",
            "email",
            "threat",
            "malware",
            "credentials",
        ],
    },
    {
        "title": "Antivirus detected malware on laptop",
        "description": "Windows Defender detected and quarantined malware: Trojan:Win32/Wacatac.B!ml. Scan found threat in downloaded file. Laptop seems to be running normally. Ran full system scan - no additional threats found. Need security team to verify laptop is clean and safe to use. Laptop: LAPTOP-SEC-089. User: jsmith.",
        "category": "Security",
        "priority": "Critical",
        "keywords": [
            "security",
            "malware",
            "virus",
            "antivirus",
            "threat",
            "trojan",
            "infected",
        ],
    },
    {
        "title": "Multiple failed login attempts on my account",
        "description": "Received 10 security alerts about failed login attempts on my account from IP address in China (IP: 123.45.67.89). I'm currently in US and haven't traveled. Attempts happened between 2 AM - 3 AM last night. Changed password immediately. Need security team to investigate and block suspicious IP. Account: mjohnson@company.com.",
        "category": "Security",
        "priority": "Critical",
        "keywords": [
            "security",
            "login",
            "failed attempts",
            "breach",
            "suspicious",
            "account",
            "threat",
        ],
    },
    # ═══════════════════════════════════════════════════════════════
    # SERVICE REQUEST DOMAIN (3 tickets)
    # ═══════════════════════════════════════════════════════════════
    {
        "title": "New employee laptop setup request",
        "description": "Need laptop setup for new employee starting Monday March 25. Employee: Jennifer Williams, Department: Sales, Manager: Robert Chen. Required software: Microsoft Office 365, Salesforce, Zoom, Slack. Laptop model: Dell Latitude 5520 preferred. Need setup completed by Friday EOD. Employee ID: EMP-2024-0156.",
        "category": "ServiceRequest",
        "priority": "High",
        "keywords": [
            "service request",
            "new employee",
            "setup",
            "laptop",
            "onboarding",
            "provisioning",
        ],
    },
    {
        "title": "Request for additional monitor",
        "description": "Request additional monitor for workstation to improve productivity. Current setup has single 24-inch monitor. Need second monitor for multitasking (coding on one screen, documentation on other). Manager approved. Department: Engineering. Desk location: 4th floor, Desk 4B-12. Preferred: Dell UltraSharp 27-inch.",
        "category": "ServiceRequest",
        "priority": "Low",
        "keywords": [
            "service request",
            "monitor",
            "equipment",
            "request",
            "hardware",
            "setup",
        ],
    },
    {
        "title": "Conference room AV equipment setup",
        "description": "Need AV equipment setup for client presentation in Conference Room B on March 28 at 2 PM. Requirements: projector, wireless presentation adapter, conference phone, HDMI cables. Expecting 15 attendees. Important client meeting. Need equipment tested before meeting. Contact: Sarah Johnson, ext. 5678.",
        "category": "ServiceRequest",
        "priority": "Medium",
        "keywords": [
            "service request",
            "conference room",
            "av equipment",
            "setup",
            "meeting",
            "projector",
        ],
    },
    # ═══════════════════════════════════════════════════════════════
    # DATABASE DOMAIN (3 tickets)
    # ═══════════════════════════════════════════════════════════════
    {
        "title": "Cannot connect to production database",
        "description": "Getting 'Connection timeout' error when trying to connect to production database server (db-prod-01.company.com). Connection was working fine yesterday. Using SQL Server Management Studio. Error code: 08001. Other team members having same issue. Need urgent fix as this blocks deployment. Database: CustomerDB. Port: 1433.",
        "category": "Database",
        "priority": "Critical",
        "keywords": [
            "database",
            "connection",
            "sql",
            "server",
            "timeout",
            "production",
            "access",
        ],
    },
    {
        "title": "Database query running extremely slow",
        "description": "Customer report query taking 5+ minutes to execute. Usually completes in 10-15 seconds. Query: SELECT * FROM orders WHERE date > '2024-01-01'. Database: SalesDB. Checked query execution plan - full table scan happening. Need database performance optimization. Affecting customer service response times. 50,000+ records in table.",
        "category": "Database",
        "priority": "High",
        "keywords": [
            "database",
            "performance",
            "slow",
            "query",
            "sql",
            "optimization",
            "server",
        ],
    },
    {
        "title": "Need read access to analytics database",
        "description": "Need read-only access to analytics database for generating monthly reports. Database: AnalyticsDB, Server: db-analytics-01. Manager Lisa Chen approved access request. My username: rjones. Department: Business Intelligence. Need access to tables: sales_data, customer_metrics, revenue_summary.",
        "category": "Database",
        "priority": "Medium",
        "keywords": [
            "database",
            "access",
            "permission",
            "sql",
            "read-only",
            "analytics",
            "grant",
        ],
    },
]


async def generate_enhanced_tickets():
    """Generate enhanced demo tickets with high confidence scores"""

    print("🎬 Generating Enhanced Demo Tickets...")
    print(f"📊 Total tickets to create: {len(ENHANCED_TICKETS)}")
    print(f"🎯 Coverage: All 10 domains (3 tickets each)")
    print(f"💪 Optimized for high confidence scores\n")

    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    tickets_collection = db["tickets"]

    try:
        # Optional: Clear existing tickets
        print("🗑️  Clear existing tickets? (y/n): ", end="")
        # Auto-yes for script execution
        clear_existing = True

        if clear_existing:
            result = await tickets_collection.delete_many({})
            print(f"   Deleted {result.deleted_count} existing tickets\n")

        # Generate tickets
        print("📝 Creating enhanced tickets...\n")
        created_count = 0
        domain_counts = {}

        for idx, ticket_data in enumerate(ENHANCED_TICKETS, 1):
            # Track domain counts
            domain = ticket_data["category"]
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

            ticket = {
                "ticket_id": f"TKT-{idx:04d}",
                "title": ticket_data["title"],
                "description": ticket_data["description"],
                "user_email": "demo.user@company.com",
                "status": TicketStatus.OPEN,
                "created_at": datetime.utcnow()
                - timedelta(minutes=random.randint(5, 120)),
                "updated_at": datetime.utcnow(),
                "metadata": {
                    "expected_category": ticket_data["category"],
                    "expected_priority": ticket_data["priority"],
                    "demo_ticket": True,
                    "enhanced": True,
                    "keywords": ticket_data["keywords"],
                },
            }

            await tickets_collection.insert_one(ticket)
            created_count += 1

            # Progress indicator
            if created_count % 3 == 0:
                print(f"   ✅ {domain}: {created_count//3} domains completed")

        print(f"\n✨ Successfully created {created_count} enhanced tickets!\n")
        print("=" * 60)
        print("📊 TICKET DISTRIBUTION BY DOMAIN")
        print("=" * 60)
        for domain, count in sorted(domain_counts.items()):
            print(f"   {domain:20s}: {count} tickets")

        print("\n" + "=" * 60)
        print("🎯 CONFIDENCE OPTIMIZATION FEATURES")
        print("=" * 60)
        print("   ✅ Domain-specific keywords included")
        print("   ✅ Clear problem descriptions")
        print("   ✅ Technical details provided")
        print("   ✅ Context and urgency specified")
        print("   ✅ Expected confidence: 70-85%")

        print("\n" + "=" * 60)
        print("🚀 READY FOR DEMO!")
        print("=" * 60)
        print("   1. Login to http://localhost:3000")
        print("   2. Navigate to ticket queue")
        print("   3. Process tickets and see high confidence scores")
        print("   4. All 10 domains represented equally")

    except Exception as e:
        print(f"\n❌ Error generating tickets: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    print("=" * 60)
    print("  TicketFlow AI - Enhanced Ticket Generator")
    print("  High Confidence Tickets for All 10 Domains")
    print("=" * 60)
    print()
    asyncio.run(generate_enhanced_tickets())
