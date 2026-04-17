# Migrate Existing Tickets to Journey Tracking

## Purpose
This script creates journey records for all existing tickets in your database that were created before the journey tracking feature was implemented.

## What It Does
1. Finds all tickets in the database
2. Checks if each ticket already has a journey record
3. Creates journey records for tickets without one
4. Sets appropriate phases based on ticket status:
   - `resolved` tickets → `resolved` phase
   - `closed` tickets → `closed` phase
   - `AUTO_RESOLVE` tickets → `ai_resolved` phase
   - `SUGGEST_TO_AGENT` tickets → `assigned_to_agent` phase
   - Other tickets → `submitted` phase

## How to Run

### Step 1: Make sure backend dependencies are installed
```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Run the migration script
```bash
cd backend
python migrate_existing_tickets.py
```

### Expected Output
```
🔄 Migrating existing tickets to journey tracking...
📊 Found 25 total tickets
  ✓ Created journey for NETWORK-001 (phase: resolved)
  ✓ Created journey for SOFTWARE-002 (phase: ai_resolved)
  ✓ Created journey for DATABASE-003 (phase: assigned_to_agent)
  ...

✅ Migration complete!
   Created: 25 journeys
   Skipped: 0 (already exist)
   Total: 25 tickets
```

## Safety
- The script is **idempotent** - you can run it multiple times safely
- It will skip tickets that already have journey records
- It does not modify existing tickets or journeys
- It only creates new journey records

## After Migration
Once the migration is complete:
1. Restart your backend (if running)
2. Navigate to `/journey` in the frontend
3. You should see all your existing tickets with journey tracking

## Auto-Refresh Features
The journey dashboard now includes:
- **Auto-refresh every 10 seconds** - Automatically shows new tickets
- **Manual refresh button** - Click to refresh immediately
- **Last updated timestamp** - Shows when data was last loaded
- **Real-time phase updates** - Journey timeline updates every 5 seconds

## Troubleshooting

### No journeys showing after migration
1. Check the migration script output for errors
2. Verify MongoDB connection string in the script
3. Check that tickets exist in the database
4. Restart the backend server

### Migration script fails
1. Ensure MongoDB is accessible
2. Check that the database name is correct
3. Verify you have write permissions to the database
4. Check backend logs for detailed error messages

### Journeys not updating in real-time
1. Check browser console for API errors
2. Verify backend is running
3. Check that journey API endpoints are working
4. Try manual refresh button

## Manual Journey Creation (Alternative)
If you prefer to create journeys manually for specific tickets:

```python
from services.journey_service import JourneyService

# Create journey for a specific ticket
journey = await journey_service.create_journey(
    ticket_id="NETWORK-001",
    user_id="user@example.com",
    category="NETWORK"
)
```

## Database Query (Check Existing Journeys)
To check how many journeys exist:

```javascript
// In MongoDB shell or Compass
db.ticket_journeys.countDocuments()

// To see all journeys
db.ticket_journeys.find().pretty()
```

## Next Steps
After migration:
1. ✅ All existing tickets now have journey tracking
2. ✅ New tickets automatically get journeys on submission
3. ✅ Dashboard auto-refreshes to show new tickets
4. ✅ Users can track all their tickets in one place

---

**Note**: This is a one-time migration. Once run successfully, all future tickets will automatically have journey tracking enabled.
