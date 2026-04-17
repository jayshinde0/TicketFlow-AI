"""
Simple migration script to create journey records for existing tickets
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

MONGODB_URL = "mongodb+srv://jayshinde4554_db_user:b8GF9ENNhu51iUxX@cluster0.i96uoim.mongodb.net/?appName=Cluster0"
DATABASE_NAME = "ticketflow_ai"


async def migrate_existing_tickets():
    """Create journey records for existing tickets that don't have one"""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    tickets_collection = db["tickets"]
    journeys_collection = db["ticket_journeys"]
    users_collection = db["users"]
    
    print("🔄 Migrating existing tickets to journey tracking...")
    
    # Get all tickets
    tickets = await tickets_collection.find({}).to_list(length=None)
    print(f"📊 Found {len(tickets)} total tickets")
    
    created_count = 0
    skipped_count = 0
    
    for ticket in tickets:
        ticket_id = ticket.get("ticket_id")
        
        # Check if journey already exists
        existing_journey = await journeys_collection.find_one({"ticket_id": ticket_id})
        if existing_journey:
            skipped_count += 1
            continue
        
        # Get ticket details
        status = ticket.get("status", "open")
        ai_analysis = ticket.get("ai_analysis", {})
        routing_decision = ai_analysis.get("routing_decision", "SUGGEST_TO_AGENT")
        category = ai_analysis.get("category", "GENERAL")
        
        # Determine current phase
        if status in ["resolved", "closed"]:
            current_phase = "resolved"
            current_status = status
        elif routing_decision == "AUTO_RESOLVE":
            current_phase = "ai_resolved"
            current_status = "resolved"
        else:
            current_phase = "assigned_to_agent"
            current_status = "in_progress"
        
        # Find an agent for this department
        department_map = {
            "NETWORK": "NETWORK",
            "SOFTWARE": "SOFTWARE",
            "DATABASE": "DATABASE",
            "SECURITY": "SECURITY",
            "BILLING": "BILLING",
            "HR_FACILITIES": "HR_FACILITIES",
            "HARDWARE": "HR_FACILITIES",
        }
        department = department_map.get(category, "NETWORK")
        
        agent = await users_collection.find_one({
            "role": "agent",
            "department": department,
            "is_active": True
        })
        
        # Build journey steps
        journey_steps = [
            {
                "step_id": "1",
                "phase": "submitted",
                "status": "completed",
                "timestamp": ticket.get("created_at", datetime.now(timezone.utc)),
                "duration_seconds": 1,
                "notes": "Ticket submitted by user",
            },
            {
                "step_id": "2",
                "phase": "ai_processing",
                "status": "completed",
                "timestamp": ticket.get("created_at", datetime.now(timezone.utc)),
                "duration_seconds": 15,
                "notes": "AI analysis completed",
            }
        ]
        
        # Add phase-specific steps
        if routing_decision == "AUTO_RESOLVE":
            journey_steps.append({
                "step_id": "3",
                "phase": "ai_resolved",
                "status": "completed" if status in ["resolved", "closed"] else "current",
                "timestamp": ticket.get("created_at", datetime.now(timezone.utc)),
                "duration_seconds": None if status not in ["resolved", "closed"] else 0,
                "notes": "AI successfully resolved the ticket",
            })
        else:
            journey_steps.append({
                "step_id": "3",
                "phase": "assigned_to_agent",
                "status": "completed" if status in ["resolved", "closed"] else "current",
                "timestamp": ticket.get("created_at", datetime.now(timezone.utc)),
                "duration_seconds": None if status not in ["resolved", "closed"] else 0,
                "assigned_agent": agent["email"] if agent else None,
                "assigned_agent_name": agent["full_name"] if agent else None,
                "department": department,
                "notes": f"Ticket assigned to {agent['full_name'] if agent else 'agent'} ({department})",
            })
        
        # Add resolved step if ticket is resolved
        if status in ["resolved", "closed"]:
            journey_steps.append({
                "step_id": str(len(journey_steps) + 1),
                "phase": "resolved",
                "status": "completed",
                "timestamp": ticket.get("updated_at", datetime.now(timezone.utc)),
                "duration_seconds": 0,
                "notes": "Ticket resolved",
            })
        
        # Create journey document
        journey = {
            "ticket_id": ticket_id,
            "current_phase": current_phase,
            "current_status": current_status,
            "assigned_agent_email": agent["email"] if agent else None,
            "assigned_agent_name": agent["full_name"] if agent else None,
            "assigned_department": department,
            "journey_steps": journey_steps,
            "created_at": ticket.get("created_at", datetime.now(timezone.utc)),
            "updated_at": ticket.get("updated_at", datetime.now(timezone.utc)),
        }
        
        try:
            await journeys_collection.insert_one(journey)
            created_count += 1
            print(f"  ✓ Created journey for {ticket_id} (phase: {current_phase})")
        except Exception as e:
            print(f"  ✗ Failed to create journey for {ticket_id}: {e}")
    
    print(f"\n✅ Migration complete!")
    print(f"   Created: {created_count} journeys")
    print(f"   Skipped: {skipped_count} (already exist)")
    print(f"   Total: {len(tickets)} tickets")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(migrate_existing_tickets())
