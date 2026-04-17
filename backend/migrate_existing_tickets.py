"""
Migrate existing tickets to create journey records
Run this once to create journeys for all existing tickets
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from services.journey_service import JourneyService

MONGODB_URL = "mongodb+srv://jayshinde4554_db_user:b8GF9ENNhu51iUxX@cluster0.i96uoim.mongodb.net/?appName=Cluster0"
DATABASE_NAME = "ticketflow_ai"


async def migrate_existing_tickets():
    """Create journey records for existing tickets that don't have one"""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    tickets_collection = db["tickets"]
    journeys_collection = db["ticket_journeys"]
    users_collection = db["users"]
    
    journey_service = JourneyService()
    
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
        
        # Determine current phase based on ticket status
        status = ticket.get("status", "open")
        routing_decision = ticket.get("ai_analysis", {}).get("routing_decision", "SUGGEST_TO_AGENT")
        category = ticket.get("ai_analysis", {}).get("category", "GENERAL")
        
        # Create journey with initial phase
        try:
            journey = await journey_service.create_journey(
                ticket_id=ticket_id,
                initial_phase="submitted"
            )
            
            # Add AI processing step
            await journey_service.add_journey_step(
                ticket_id=ticket_id,
                phase="ai_processing",
                status="completed",
                notes="AI analysis completed"
            )
            
            # Determine next phase based on routing decision
            if routing_decision == "AUTO_RESOLVE":
                await journey_service.add_journey_step(
                    ticket_id=ticket_id,
                    phase="ai_resolved",
                    status="completed" if status in ["resolved", "closed"] else "current",
                    notes="AI successfully resolved the ticket"
                )
            else:
                # Assign to agent
                await journey_service.add_journey_step(
                    ticket_id=ticket_id,
                    phase="assigned_to_agent",
                    status="completed" if status in ["resolved", "closed"] else "current",
                    notes="Ticket assigned to agent"
                )
                
                # Try to find and assign an agent
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
                
                # Find available agent
                agent = await users_collection.find_one({
                    "role": "agent",
                    "department": department,
                    "is_active": True
                })
                
                if agent:
                    await journey_service.assign_agent(
                        ticket_id=ticket_id,
                        agent_email=agent["email"],
                        agent_name=agent["full_name"],
                        department=department
                    )
            
            # If ticket is resolved, add resolved step
            if status in ["resolved", "closed"]:
                await journey_service.add_journey_step(
                    ticket_id=ticket_id,
                    phase="resolved",
                    status="completed",
                    notes="Ticket resolved"
                )
            
            created_count += 1
            current_phase = "resolved" if status in ["resolved", "closed"] else (
                "ai_resolved" if routing_decision == "AUTO_RESOLVE" else "assigned_to_agent"
            )
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
