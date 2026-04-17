"""
Seed sample support agents for each department
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime, timezone

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

MONGODB_URL = "mongodb+srv://jayshinde4554_db_user:b8GF9ENNhu51iUxX@cluster0.i96uoim.mongodb.net/?appName=Cluster0"
DATABASE_NAME = "ticketflow_ai"

# Sample agents for each department
SAMPLE_AGENTS = [
    # Network Department
    {
        "email": "john.network@ticketflow.ai",
        "full_name": "John Network",
        "role": "agent",
        "department": "NETWORK",
        "specialization": "Network Infrastructure",
        "is_active": True,
        "current_workload": 0,
        "max_concurrent_tickets": 10,
    },
    {
        "email": "sarah.network@ticketflow.ai",
        "full_name": "Sarah Network",
        "role": "agent",
        "department": "NETWORK",
        "specialization": "Network Security",
        "is_active": True,
        "current_workload": 0,
        "max_concurrent_tickets": 10,
    },
    # Software Department
    {
        "email": "mike.software@ticketflow.ai",
        "full_name": "Mike Software",
        "role": "agent",
        "department": "SOFTWARE",
        "specialization": "Application Support",
        "is_active": True,
        "current_workload": 0,
        "max_concurrent_tickets": 15,
    },
    {
        "email": "lisa.software@ticketflow.ai",
        "full_name": "Lisa Software",
        "role": "agent",
        "department": "SOFTWARE",
        "specialization": "Software Development",
        "is_active": True,
        "current_workload": 0,
        "max_concurrent_tickets": 15,
    },
    # Database Department
    {
        "email": "david.database@ticketflow.ai",
        "full_name": "David Database",
        "role": "agent",
        "department": "DATABASE",
        "specialization": "Database Administration",
        "is_active": True,
        "current_workload": 0,
        "max_concurrent_tickets": 8,
    },
    {
        "email": "emma.database@ticketflow.ai",
        "full_name": "Emma Database",
        "role": "agent",
        "department": "DATABASE",
        "specialization": "Database Performance",
        "is_active": True,
        "current_workload": 0,
        "max_concurrent_tickets": 8,
    },
    # Security Department
    {
        "email": "alex.security@ticketflow.ai",
        "full_name": "Alex Security",
        "role": "agent",
        "department": "SECURITY",
        "specialization": "Security Analysis",
        "is_active": True,
        "current_workload": 0,
        "max_concurrent_tickets": 5,
    },
    {
        "email": "rachel.security@ticketflow.ai",
        "full_name": "Rachel Security",
        "role": "agent",
        "department": "SECURITY",
        "specialization": "Incident Response",
        "is_active": True,
        "current_workload": 0,
        "max_concurrent_tickets": 5,
    },
    # Billing Department
    {
        "email": "tom.billing@ticketflow.ai",
        "full_name": "Tom Billing",
        "role": "agent",
        "department": "BILLING",
        "specialization": "Billing Support",
        "is_active": True,
        "current_workload": 0,
        "max_concurrent_tickets": 12,
    },
    {
        "email": "nina.billing@ticketflow.ai",
        "full_name": "Nina Billing",
        "role": "agent",
        "department": "BILLING",
        "specialization": "Payment Processing",
        "is_active": True,
        "current_workload": 0,
        "max_concurrent_tickets": 12,
    },
    # HR & Facilities Department
    {
        "email": "chris.hrfacilities@ticketflow.ai",
        "full_name": "Chris HR",
        "role": "agent",
        "department": "HR_FACILITIES",
        "specialization": "HR & Facilities",
        "is_active": True,
        "current_workload": 0,
        "max_concurrent_tickets": 10,
    },
    {
        "email": "amy.hrfacilities@ticketflow.ai",
        "full_name": "Amy Facilities",
        "role": "agent",
        "department": "HR_FACILITIES",
        "specialization": "Hardware & Facilities",
        "is_active": True,
        "current_workload": 0,
        "max_concurrent_tickets": 10,
    },
]


async def seed_agents():
    """Seed sample support agents"""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    users_collection = db["users"]

    print("🔧 Seeding support agents...")

    # Clean up any documents with null user_id first
    print("  🧹 Cleaning up invalid documents...")
    cleanup_result = await users_collection.delete_many({"user_id": None})
    if cleanup_result.deleted_count > 0:
        print(f"  ✓ Removed {cleanup_result.deleted_count} invalid documents")

    # Default password for all agents
    default_password = "Agent@123"
    hashed_password = pwd_context.hash(default_password)

    created_count = 0
    updated_count = 0

    for agent_data in SAMPLE_AGENTS:
        # Check if agent already exists by email OR user_id
        existing = await users_collection.find_one({
            "$or": [
                {"email": agent_data["email"]},
                {"user_id": agent_data["email"]}
            ]
        })

        agent_doc = {
            **agent_data,
            "user_id": agent_data["email"],  # Use email as user_id
            "password_hash": hashed_password,
            "updated_at": datetime.now(timezone.utc),
        }

        if existing:
            # Update existing agent (preserve created_at)
            await users_collection.update_one(
                {"_id": existing["_id"]}, 
                {"$set": agent_doc}
            )
            updated_count += 1
            print(f"  ✓ Updated: {agent_data['full_name']} ({agent_data['department']})")
        else:
            # Create new agent
            agent_doc["created_at"] = datetime.now(timezone.utc)
            await users_collection.insert_one(agent_doc)
            created_count += 1
            print(f"  ✓ Created: {agent_data['full_name']} ({agent_data['department']})")

    print(f"\n✅ Seeding complete!")
    print(f"   Created: {created_count} agents")
    print(f"   Updated: {updated_count} agents")
    print(f"   Total: {len(SAMPLE_AGENTS)} agents")
    print(f"\n📝 Default password for all agents: {default_password}")
    print(f"   Example login: john.network@ticketflow.ai / {default_password}")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed_agents())
