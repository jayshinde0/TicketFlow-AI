"""
Generate sample tickets for demo purposes
Run this script to populate the database with realistic demo data
"""

import asyncio
import sys
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
from models.ticket import TicketStatus, TicketPriority, TicketCategory
import random

# Sample tickets for different scenarios
DEMO_TICKETS = [
    # AUTO-RESOLVE TICKETS (High Confidence)
    {
        "title": "Forgot my password",
        "description": "I forgot my password and need to reset it. I tried the forgot password link but I'm not receiving the reset email. My email is john.doe@company.com. Please help me access my account.",
        "user_email": "user@company.com",
        "expected_category": "Authentication",
        "expected_priority": "Medium"
    },
    {
        "title": "Office printer not responding",
        "description": "The printer on the 3rd floor (HP LaserJet 4050) is not responding. I've tried turning it off and on, but it still shows offline on my computer. I need to print urgent documents for a meeting in 1 hour.",
        "user_email": "user@company.com",
        "expected_category": "Hardware",
        "expected_priority": "High"
    },
    {
        "title": "Need Microsoft Teams installed",
        "description": "I need Microsoft Teams installed on my laptop for remote meetings. I'm a new employee and it wasn't included in my initial setup. My laptop is a Dell Latitude 5520 running Windows 11.",
        "user_email": "user@company.com",
        "expected_category": "Software",
        "expected_priority": "Medium"
    },
    
    # AGENT REVIEW TICKETS (Medium Confidence)
    {
        "title": "VPN connection timeout",
        "description": "I'm unable to connect to the company VPN since this morning at 9 AM. The VPN client shows 'Connecting...' for about 30 seconds then times out with error code 800. I've tried restarting the VPN client and my laptop. Other team members on the same floor seem to be affected too. I'm on Windows 11, using GlobalProtect v6.2.",
        "user_email": "user@company.com",
        "expected_category": "Network",
        "expected_priority": "High"
    },
    {
        "title": "Outlook not syncing emails",
        "description": "My Outlook is not syncing new emails since yesterday evening. I can send emails but not receive them. I've checked my internet connection and it's working fine. Other applications like Teams and browser work normally. I'm using Outlook 2021 on Windows 10.",
        "user_email": "user@company.com",
        "expected_category": "Email",
        "expected_priority": "Medium"
    },
    {
        "title": "Computer running very slow",
        "description": "My computer has been running extremely slow for the past week. Applications take forever to open, and sometimes the screen freezes for 10-15 seconds. I've tried restarting multiple times but the issue persists. I have important deadlines coming up and this is affecting my productivity.",
        "user_email": "user@company.com",
        "expected_category": "Performance",
        "expected_priority": "Medium"
    },
    
    # ESCALATION TICKETS (Overrides)
    {
        "title": "Database access denied - URGENT",
        "description": "I'm getting 'Access Denied' errors when trying to connect to the production database. This is blocking our entire development team from deploying the critical hotfix. We need immediate access restored. This has been happening for the last 30 minutes and we're losing money every minute!",
        "user_email": "user@company.com",
        "expected_category": "Database",
        "expected_priority": "Critical"
    },
    {
        "title": "Suspicious login attempts on my account",
        "description": "I received 15 security alerts about failed login attempts on my account from an IP address in Russia. I haven't traveled recently and I'm currently in the US. I'm worried my account has been compromised. Please investigate immediately and secure my account.",
        "user_email": "user@company.com",
        "expected_category": "Security",
        "expected_priority": "Critical"
    },
    {
        "title": "STILL can't access shared drive - 3rd time reporting!",
        "description": "This is the THIRD time I'm reporting this issue and NOBODY has fixed it! I can't access the shared drive and I'm missing deadlines because of this. This is completely unacceptable! I've been waiting for 2 days and I'm extremely frustrated. I need this fixed NOW or I'm escalating to management!",
        "user_email": "user@company.com",
        "expected_category": "Access",
        "expected_priority": "High"
    }
]

# Additional realistic tickets for variety
ADDITIONAL_TICKETS = [
    {
        "title": "Cannot login to email",
        "description": "I'm getting an 'Invalid credentials' error when trying to login to my email. I'm sure I'm using the correct password. Can you please reset it?",
        "user_email": "user@company.com"
    },
    {
        "title": "Laptop screen flickering",
        "description": "My laptop screen has been flickering intermittently. It happens randomly and lasts for a few seconds. It's very distracting during video calls.",
        "user_email": "user@company.com"
    },
    {
        "title": "Need access to shared folder",
        "description": "I need access to the Marketing shared folder on the network drive. My manager approved this request. My username is jdoe.",
        "user_email": "user@company.com"
    },
    {
        "title": "Excel keeps crashing",
        "description": "Microsoft Excel crashes every time I try to open large spreadsheets (>10MB). I've tried restarting but the issue persists. I need this for my quarterly report.",
        "user_email": "user@company.com"
    },
    {
        "title": "WiFi keeps disconnecting",
        "description": "My laptop WiFi keeps disconnecting every 10-15 minutes. I have to manually reconnect each time. This is affecting my work productivity.",
        "user_email": "user@company.com"
    }
]


async def generate_demo_tickets():
    """Generate demo tickets in the database"""
    
    print("🎬 Generating demo tickets...")
    print(f"Connecting to MongoDB: {settings.MONGODB_URI}")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.DATABASE_NAME]
    tickets_collection = db["tickets"]
    
    try:
        # Clear existing demo tickets (optional)
        print("\n🗑️  Clearing existing tickets...")
        result = await tickets_collection.delete_many({})
        print(f"   Deleted {result.deleted_count} existing tickets")
        
        # Generate main demo tickets
        print("\n📝 Creating demo tickets...")
        created_count = 0
        
        for idx, ticket_data in enumerate(DEMO_TICKETS, 1):
            ticket = {
                "ticket_id": f"TKT-DEMO{idx:02d}",
                "title": ticket_data["title"],
                "description": ticket_data["description"],
                "user_email": ticket_data["user_email"],
                "status": TicketStatus.OPEN,
                "created_at": datetime.utcnow() - timedelta(minutes=random.randint(5, 60)),
                "updated_at": datetime.utcnow(),
                "metadata": {
                    "expected_category": ticket_data.get("expected_category"),
                    "expected_priority": ticket_data.get("expected_priority"),
                    "demo_ticket": True
                }
            }
            
            await tickets_collection.insert_one(ticket)
            created_count += 1
            print(f"   ✅ Created: {ticket['ticket_id']} - {ticket['title']}")
        
        # Generate additional tickets for variety
        print("\n📝 Creating additional tickets...")
        for idx, ticket_data in enumerate(ADDITIONAL_TICKETS, 10):
            ticket = {
                "ticket_id": f"TKT-DEMO{idx:02d}",
                "title": ticket_data["title"],
                "description": ticket_data["description"],
                "user_email": ticket_data["user_email"],
                "status": random.choice([TicketStatus.OPEN, TicketStatus.RESOLVED]),
                "created_at": datetime.utcnow() - timedelta(hours=random.randint(1, 48)),
                "updated_at": datetime.utcnow(),
                "metadata": {
                    "demo_ticket": True
                }
            }
            
            # Add resolution data for resolved tickets
            if ticket["status"] == TicketStatus.RESOLVED:
                ticket["resolved_at"] = datetime.utcnow() - timedelta(hours=random.randint(1, 24))
                ticket["resolution"] = "Issue has been resolved. Please let us know if you need further assistance."
            
            await tickets_collection.insert_one(ticket)
            created_count += 1
            print(f"   ✅ Created: {ticket['ticket_id']} - {ticket['title']}")
        
        print(f"\n✨ Successfully created {created_count} demo tickets!")
        print("\n📋 Demo Ticket Summary:")
        print("   • Auto-Resolve Candidates: 3 tickets (DEMO01-DEMO03)")
        print("   • Agent Review Candidates: 3 tickets (DEMO04-DEMO06)")
        print("   • Escalation Candidates: 3 tickets (DEMO07-DEMO09)")
        print("   • Additional Variety: 5 tickets (DEMO10-DEMO14)")
        print("\n🎯 Ready for demo! Login and start processing tickets.")
        
    except Exception as e:
        print(f"\n❌ Error generating demo tickets: {e}")
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    print("=" * 60)
    print("  TicketFlow AI - Demo Ticket Generator")
    print("=" * 60)
    asyncio.run(generate_demo_tickets())
