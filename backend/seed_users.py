"""
seed_users.py — Create 3 test users in MongoDB for local testing.
Run once: python seed_users.py

Users created:
  user@test.com    / test1234  (role: user)
  agent@test.com   / test1234  (role: agent)
  admin@test.com   / test1234  (role: admin)
"""

import asyncio
import uuid
from datetime import datetime, timezone
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorClient

# ── Config ────────────────────────────────────────────────────────────
MONGODB_URL = "mongodb+srv://jayshinde4554_db_user:b8GF9ENNhu51iUxX@cluster0.i96uoim.mongodb.net/?appName=Cluster0"
DATABASE_NAME = "ticketflow_ai"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SEED_USERS = [
    {
        "name": "Test User",
        "email": "user@test.com",
        "password": "test1234",
        "role": "user",
        "tier": "Standard",
    },
    {
        "name": "Test Agent",
        "email": "agent@test.com",
        "password": "test1234",
        "role": "agent",
        "tier": "Premium",
    },
    {
        "name": "Test Admin",
        "email": "admin@test.com",
        "password": "test1234",
        "role": "admin",
        "tier": "Enterprise",
    },
]


async def seed():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    users_col = db["users"]

    created = 0
    skipped = 0

    for u in SEED_USERS:
        existing = await users_col.find_one({"email": u["email"]})
        if existing:
            print(f"  ⚠  Already exists: {u['email']}")
            skipped += 1
            continue

        doc = {
            "user_id": str(uuid.uuid4()),
            "name": u["name"],
            "email": u["email"],
            "password_hash": pwd_context.hash(u["password"]),
            "role": u["role"],
            "tier": u["tier"],
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        }
        await users_col.insert_one(doc)
        print(f"  ✅ Created: {u['email']}  (role={u['role']})")
        created += 1

    print(f"\n Done — {created} created, {skipped} skipped.")
    client.close()


if __name__ == "__main__":
    print("Seeding test users into MongoDB Atlas...\n")
    asyncio.run(seed())
