"""
Seed the knowledge base with sample articles
Run with: python seed_knowledge_base.py
"""

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
from services.retrieval_service import retrieval_service

# Sample knowledge base articles
SAMPLE_ARTICLES = [
    {
        "article_id": "KB-AUTH001",
        "title": "Password Reset Email Not Received",
        "category": "Auth",
        "problem_description": "User cannot receive password reset email after requesting it through the forgot password link.",
        "likely_cause": "Email is in spam/junk folder, incorrect email address entered, or email server delay.",
        "solution_steps": [
            "Check your spam/junk folder for emails from noreply@company.com",
            "Verify that you entered the correct email address",
            "Wait 5-10 minutes for email delivery (server delays can occur)",
            "Whitelist noreply@company.com in your email settings",
            "Request a new reset link if not received within 10 minutes",
            "Contact IT support at ext. 5555 if issue persists",
        ],
        "prevention": "Add noreply@company.com to your email whitelist to prevent future delivery issues.",
        "tags": ["password", "reset", "email", "authentication", "forgot"],
        "difficulty": "Easy",
        "estimated_resolution_time": "15 minutes",
        "source_ticket_id": "TKT-SAMPLE01",
        "usage_count": 15,
    },
    {
        "article_id": "KB-NET001",
        "title": "VPN Connection Timeout Error 800",
        "category": "Network",
        "problem_description": "VPN client shows 'Connecting...' for 30 seconds then times out with error code 800.",
        "likely_cause": "Network firewall blocking VPN ports, outdated VPN client version, or VPN server maintenance.",
        "solution_steps": [
            "Check VPN server status at https://status.company.com/vpn",
            "Restart your VPN client application",
            "Temporarily disable Windows Firewall and test connection",
            "Update to latest GlobalProtect version from IT portal",
            "Try connecting to alternate VPN server (vpn2.company.com)",
            "Restart your computer if issue persists",
            "Contact network team if multiple users affected",
        ],
        "prevention": "Keep VPN client updated and ensure firewall allows VPN traffic on ports 443 and 4501.",
        "tags": ["vpn", "connection", "timeout", "error800", "network"],
        "difficulty": "Medium",
        "estimated_resolution_time": "30 minutes",
        "source_ticket_id": "TKT-SAMPLE02",
        "usage_count": 23,
    },
    {
        "article_id": "KB-SOFT001",
        "title": "Microsoft Teams Installation",
        "category": "Software",
        "problem_description": "New employee needs Microsoft Teams installed on their laptop for remote meetings.",
        "likely_cause": "Software not included in initial laptop setup or user doesn't have admin rights.",
        "solution_steps": [
            "Open Company Software Portal (portal.company.com/software)",
            "Login with your company credentials",
            "Search for 'Microsoft Teams' in the catalog",
            "Click 'Install' button (requires admin approval for first-time users)",
            "Wait 5-10 minutes for automatic installation",
            "Restart your computer after installation completes",
            "Launch Teams and sign in with your company email",
        ],
        "prevention": "Request software access during onboarding process to avoid delays.",
        "tags": ["teams", "microsoft", "installation", "software", "onboarding"],
        "difficulty": "Easy",
        "estimated_resolution_time": "20 minutes",
        "source_ticket_id": "TKT-SAMPLE03",
        "usage_count": 18,
    },
    {
        "article_id": "KB-HARD001",
        "title": "Office Printer Not Responding",
        "category": "Hardware",
        "problem_description": "Network printer shows as offline on computer despite being powered on.",
        "likely_cause": "Printer network cable disconnected, printer IP changed, or print spooler service stopped.",
        "solution_steps": [
            "Check that printer is powered on and displays 'Ready' status",
            "Verify network cable is securely connected to printer",
            "Print a test page directly from printer control panel",
            "On your computer, go to Settings > Devices > Printers",
            "Remove the printer and add it again using IP address",
            "Restart Print Spooler service (services.msc > Print Spooler > Restart)",
            "Contact facilities if printer still shows offline",
        ],
        "prevention": "Use static IP addresses for network printers to prevent connection issues.",
        "tags": ["printer", "offline", "hardware", "network", "printing"],
        "difficulty": "Medium",
        "estimated_resolution_time": "25 minutes",
        "source_ticket_id": "TKT-SAMPLE04",
        "usage_count": 12,
    },
    {
        "article_id": "KB-EMAIL001",
        "title": "Outlook Not Syncing New Emails",
        "category": "Email",
        "problem_description": "Outlook can send emails but not receive new messages. Other apps work normally.",
        "likely_cause": "Outlook offline mode enabled, mailbox quota exceeded, or sync settings misconfigured.",
        "solution_steps": [
            "Check if Outlook is in Offline Mode (bottom status bar)",
            "Click 'Send/Receive' tab and click 'Work Offline' to disable",
            "Go to File > Account Settings > Account Settings",
            "Select your email account and click 'Change'",
            "Click 'More Settings' > 'Advanced' tab",
            "Ensure 'Leave a copy of messages on server' is checked",
            "Click 'Send/Receive All Folders' to force sync",
            "Restart Outlook if issue persists",
        ],
        "prevention": "Regularly archive old emails to stay under mailbox quota limit.",
        "tags": ["outlook", "email", "sync", "not receiving", "office365"],
        "difficulty": "Easy",
        "estimated_resolution_time": "15 minutes",
        "source_ticket_id": "TKT-SAMPLE05",
        "usage_count": 20,
    },
    {
        "article_id": "KB-ACCESS001",
        "title": "Shared Drive Access Request",
        "category": "Access",
        "problem_description": "User needs access to department shared folder on network drive.",
        "likely_cause": "User not added to appropriate Active Directory security group.",
        "solution_steps": [
            "Identify the shared folder path (e.g., \\\\fileserver\\Marketing)",
            "Get manager approval via email",
            "Submit access request through IT Service Portal",
            "Include: folder path, business justification, manager approval",
            "IT will add you to appropriate security group",
            "Wait 15-30 minutes for Active Directory sync",
            "Restart your computer to refresh group memberships",
            "Test access by navigating to shared folder",
        ],
        "prevention": "Request access during onboarding or role change to avoid delays.",
        "tags": ["access", "shared drive", "permissions", "network", "folder"],
        "difficulty": "Easy",
        "estimated_resolution_time": "45 minutes",
        "source_ticket_id": "TKT-SAMPLE06",
        "usage_count": 16,
    },
    {
        "article_id": "KB-PERF001",
        "title": "Computer Running Slow",
        "category": "Software",
        "problem_description": "Laptop performance degraded significantly. Applications take long to open and system freezes intermittently.",
        "likely_cause": "High disk usage, insufficient RAM, malware, or too many startup programs.",
        "solution_steps": [
            "Open Task Manager (Ctrl+Shift+Esc) and check CPU/Memory/Disk usage",
            "Close unnecessary applications and browser tabs",
            "Disable startup programs: Task Manager > Startup tab",
            "Run Windows Disk Cleanup (search 'Disk Cleanup' in Start menu)",
            "Run antivirus full scan (Windows Security or company antivirus)",
            "Check for Windows updates and install pending updates",
            "Restart computer after cleanup and updates",
            "Contact IT if issue persists for hardware upgrade assessment",
        ],
        "prevention": "Regularly close unused applications, run disk cleanup monthly, and keep system updated.",
        "tags": ["slow", "performance", "lag", "freeze", "computer"],
        "difficulty": "Medium",
        "estimated_resolution_time": "1 hour",
        "source_ticket_id": "TKT-SAMPLE07",
        "usage_count": 25,
    },
    {
        "article_id": "KB-WIFI001",
        "title": "WiFi Keeps Disconnecting",
        "category": "Network",
        "problem_description": "Laptop WiFi connection drops every 10-15 minutes requiring manual reconnection.",
        "likely_cause": "Power saving mode disabling WiFi adapter, driver issues, or weak signal strength.",
        "solution_steps": [
            "Right-click WiFi icon in system tray > Open Network Settings",
            "Click 'Change adapter options'",
            "Right-click WiFi adapter > Properties",
            "Click 'Configure' > 'Power Management' tab",
            "Uncheck 'Allow computer to turn off this device to save power'",
            "Update WiFi driver: Device Manager > Network adapters > Update driver",
            "Forget WiFi network and reconnect with password",
            "Move closer to WiFi access point if signal is weak",
            "Contact IT if issue affects multiple users in same area",
        ],
        "prevention": "Disable power saving for network adapters and keep WiFi drivers updated.",
        "tags": ["wifi", "disconnect", "wireless", "network", "connection"],
        "difficulty": "Medium",
        "estimated_resolution_time": "30 minutes",
        "source_ticket_id": "TKT-SAMPLE08",
        "usage_count": 19,
    },
    {
        "article_id": "KB-EXCEL001",
        "title": "Excel Crashing When Opening Large Files",
        "category": "Software",
        "problem_description": "Microsoft Excel crashes or freezes when attempting to open spreadsheets larger than 10MB.",
        "likely_cause": "Insufficient memory, Excel add-ins causing conflicts, or corrupted Office installation.",
        "solution_steps": [
            "Close all other applications to free up memory",
            "Open Excel in Safe Mode: Hold Ctrl while launching Excel",
            "Disable Excel add-ins: File > Options > Add-ins > Manage COM Add-ins",
            "Increase Excel memory limit: File > Options > Advanced > Display",
            "Repair Office installation: Control Panel > Programs > Microsoft Office > Change > Repair",
            "Split large file into smaller workbooks if possible",
            "Save file as .xlsx instead of .xls format",
            "Contact IT for RAM upgrade if issue persists with large files",
        ],
        "prevention": "Keep Excel files under 5MB when possible, use external data connections for large datasets.",
        "tags": ["excel", "crash", "freeze", "large file", "office"],
        "difficulty": "Medium",
        "estimated_resolution_time": "40 minutes",
        "source_ticket_id": "TKT-SAMPLE09",
        "usage_count": 14,
    },
    {
        "article_id": "KB-LOGIN001",
        "title": "Account Locked After Multiple Failed Login Attempts",
        "category": "Auth",
        "problem_description": "User account locked due to entering incorrect password multiple times.",
        "likely_cause": "Password changed recently and old password cached, or caps lock enabled during login.",
        "solution_steps": [
            "Wait 30 minutes for automatic account unlock (security policy)",
            "Verify Caps Lock is OFF before entering password",
            "Try password reset if you don't remember current password",
            "Clear saved passwords in browser if auto-fill is using old password",
            "Contact IT Help Desk at ext. 5555 for immediate unlock if urgent",
            "Provide employee ID and verify identity for manual unlock",
            "Update password in all devices after unlock to prevent re-lock",
        ],
        "prevention": "Use password manager to avoid typos, and update passwords on all devices simultaneously.",
        "tags": ["locked", "account", "login", "password", "authentication"],
        "difficulty": "Easy",
        "estimated_resolution_time": "35 minutes",
        "source_ticket_id": "TKT-SAMPLE10",
        "usage_count": 22,
    },
]


async def seed_knowledge_base():
    """Seed MongoDB with sample knowledge base articles"""
    print("🌱 Seeding Knowledge Base...")
    print(f"Connecting to MongoDB: {settings.MONGODB_URL}")

    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    collection = db["knowledge_articles"]

    try:
        # Clear existing articles (optional)
        print("\n🗑️  Clearing existing articles...")
        result = await collection.delete_many({})
        print(f"   Deleted {result.deleted_count} existing articles")

        # Insert sample articles
        print("\n📝 Creating sample articles...")
        created_count = 0

        for article in SAMPLE_ARTICLES:
            # Add timestamps
            article["created_at"] = datetime.now(timezone.utc)
            article["last_used_at"] = datetime.now(timezone.utc)
            article["embedding_id"] = article["article_id"]

            await collection.insert_one(article.copy())
            created_count += 1
            print(f"   ✅ Created: {article['article_id']} - {article['title']}")

            # Also add to ChromaDB for semantic search
            article_content = (
                f"{article['title']} {article['problem_description']} "
                f"{' '.join(article['solution_steps'])}"
            )
            await retrieval_service.add_knowledge_article(
                article_id=article["article_id"],
                content=article_content,
                metadata={
                    "article_id": article["article_id"],
                    "category": article["category"],
                    "difficulty": article["difficulty"],
                    "tags": ",".join(article["tags"]),
                },
            )

        print(f"\n✨ Successfully created {created_count} knowledge base articles!")
        print("\n📊 Articles by Category:")

        # Count by category
        pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        async for doc in collection.aggregate(pipeline):
            print(f"   • {doc['_id']}: {doc['count']} articles")

        print("\n🎯 Knowledge Base is ready!")
        print("   Navigate to http://localhost:3000/knowledge-base to view articles")

    except Exception as e:
        print(f"\n❌ Error seeding knowledge base: {e}")
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    print("=" * 60)
    print("  TicketFlow AI - Knowledge Base Seeder")
    print("=" * 60)
    asyncio.run(seed_knowledge_base())
