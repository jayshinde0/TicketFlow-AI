# Ticket Journey Tracking - Setup & Usage Guide

## Overview
The Ticket Journey Tracking feature provides real-time visibility into the lifecycle of support tickets, from submission through resolution. Users can track which phase their ticket is in and which agent is handling it.

## Backend Setup ✅ COMPLETED

### 1. Database Models
- **File**: `backend/models/ticket_journey.py`
- **Collections**: `ticket_journeys` (MongoDB)
- **Fields**:
  - `journey_id`: Unique identifier
  - `ticket_id`: Reference to ticket
  - `user_id`: Ticket submitter
  - `current_phase`: Current journey phase
  - `phases`: Array of phase history with timestamps
  - `assigned_agent_id`: Agent handling the ticket
  - `total_duration_ms`: Total time in journey

### 2. Journey Service
- **File**: `backend/services/journey_service.py`
- **Features**:
  - Automatic journey creation on ticket submission
  - Phase transition tracking with timestamps
  - Automatic agent assignment based on department and workload
  - Duration calculation for each phase

### 3. API Endpoints
- **File**: `backend/routers/journey.py`
- **Endpoints**:
  - `GET /api/journey/ticket/{ticket_id}` - Get journey by ticket ID
  - `GET /api/journey/user/{user_id}` - Get all journeys for a user
  - `PATCH /api/journey/{journey_id}/phase` - Update journey phase (admin/agent only)

### 4. Sample Agents Created ✅
Run the seed script to create 12 sample agents:
```bash
cd backend
python seed_agents.py
```

**Created Agents** (2 per department):
- **NETWORK**: John Network, Sarah Network
- **SOFTWARE**: Mike Software, Lisa Software
- **DATABASE**: David Database, Emma Database
- **SECURITY**: Alex Security, Rachel Security
- **BILLING**: Tom Billing, Nina Billing
- **HR_FACILITIES**: Chris HR, Amy Facilities

**Default Password**: `Agent@123`

**Example Login**: `john.network@ticketflow.ai` / `Agent@123`

## Frontend Setup ✅ COMPLETED

### 1. API Service
- **File**: `frontend/src/services/api.js`
- **Added**: `journeyAPI` with methods for fetching journey data

### 2. Components Created

#### TicketJourney Component
- **File**: `frontend/src/components/ticket/TicketJourney.jsx`
- **Purpose**: Full journey timeline with phase indicators
- **Features**:
  - Visual timeline with icons for each phase
  - Assigned agent information card
  - Duration tracking for each phase
  - Current phase highlighting with animation
  - Total journey duration summary

#### JourneyBadge Component
- **File**: `frontend/src/components/ticket/JourneyBadge.jsx`
- **Purpose**: Compact badge showing current phase
- **Features**:
  - Color-coded phase indicators
  - Icon representation
  - Agent name display (when assigned)

#### TicketJourneyDashboard Page
- **File**: `frontend/src/pages/TicketJourneyDashboard.jsx`
- **Purpose**: User dashboard showing all ticket journeys
- **Features**:
  - Statistics cards (total, active, resolved, avg duration)
  - Journey cards with progress bars
  - Assigned agent information
  - Click to view ticket details

### 3. Integration Points

#### TicketDetail Page
- **File**: `frontend/src/pages/TicketDetail.jsx`
- **Integration**: Journey timeline added to sidebar
- **Location**: Above AI Metrics card

#### App Router
- **File**: `frontend/src/App.jsx`
- **Route**: `/journey` - Journey dashboard page

#### Sidebar Navigation
- **File**: `frontend/src/components/Sidebar.jsx`
- **Link**: "Ticket Journey" in General section

## Journey Phases

### Phase Flow
```
submitted 
  ↓
ai_processing 
  ↓
ai_resolved (if AI can resolve)
  OR
assigned_to_agent (if needs human)
  ↓
in_progress (agent working on it)
  ↓
resolved
  ↓
closed
```

### Phase Descriptions

1. **submitted**: Ticket just created, waiting for AI processing
2. **ai_processing**: AI is analyzing and generating response
3. **ai_resolved**: AI successfully resolved the ticket
4. **assigned_to_agent**: Ticket assigned to human agent
5. **in_progress**: Agent actively working on the ticket
6. **resolved**: Ticket resolved (by AI or agent)
7. **closed**: Ticket closed by user or system

## Automatic Agent Assignment

The system automatically assigns tickets to agents based on:

1. **Department Match**: Agent's department matches ticket category
2. **Workload Balance**: Agent with lowest current workload
3. **Availability**: Only active agents are considered
4. **Capacity**: Agents not exceeding max concurrent tickets

**Assignment Logic** (in `journey_service.py`):
```python
# Find agents in matching department
# Sort by current_workload (ascending)
# Filter by is_active and under max_concurrent_tickets
# Assign to first available agent
```

## Testing the Feature

### 1. Start Backend
```bash
cd backend
python main.py
```

### 2. Start Frontend
```bash
cd frontend
npm start
```

### 3. Test Flow

#### As User:
1. Login as regular user
2. Submit a new ticket
3. Navigate to "Ticket Journey" in sidebar
4. View journey dashboard with all tickets
5. Click on a ticket to see detailed timeline
6. Check assigned agent information

#### As Agent:
1. Login as agent (e.g., `john.network@ticketflow.ai` / `Agent@123`)
2. Go to Agent Queue
3. View tickets assigned to you
4. Update ticket status
5. Journey phases update automatically

### 4. API Testing

#### Get Journey by Ticket ID
```bash
curl -X GET "http://localhost:8000/api/journey/ticket/NETWORK-001" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Get All User Journeys
```bash
curl -X GET "http://localhost:8000/api/journey/user/user@example.com" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Update Journey Phase (Admin/Agent)
```bash
curl -X PATCH "http://localhost:8000/api/journey/JOURNEY_ID/phase" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"phase": "in_progress"}'
```

## UI Features

### Journey Dashboard (`/journey`)
- **Stats Cards**: Total tickets, active, resolved, average duration
- **Journey Cards**: Grid layout with progress bars
- **Agent Info**: Shows assigned agent with department
- **Phase Progress**: Visual progress bar showing completion
- **Click Navigation**: Click any card to view ticket details

### Ticket Detail Page
- **Journey Timeline**: Full vertical timeline in sidebar
- **Phase Icons**: Color-coded icons for each phase
- **Duration Display**: Time spent in each phase
- **Agent Card**: Detailed agent information with workload
- **Current Phase**: Highlighted with animation

### Journey Badge
- **Compact Display**: Small badge for lists
- **Color Coding**: Different colors per phase
- **Agent Name**: Shows agent first name when assigned

## Color Scheme

- **Submitted**: Blue (`text-blue-400`)
- **AI Processing**: Purple (`text-purple-400`)
- **AI Resolved**: Emerald (`text-emerald-400`)
- **Assigned to Agent**: Amber (`text-amber-400`)
- **In Progress**: Cyan (`text-cyan-400`)
- **Resolved**: Emerald (`text-emerald-400`)
- **Closed**: Gray (`text-gray-400`)

## Database Schema

### ticket_journeys Collection
```javascript
{
  journey_id: "JRN-20260417-001",
  ticket_id: "NETWORK-001",
  user_id: "user@example.com",
  current_phase: "assigned_to_agent",
  phases: [
    {
      phase: "submitted",
      entered_at: ISODate("2026-04-17T10:00:00Z"),
      duration_ms: 1500
    },
    {
      phase: "ai_processing",
      entered_at: ISODate("2026-04-17T10:00:01Z"),
      duration_ms: 15000
    },
    {
      phase: "assigned_to_agent",
      entered_at: ISODate("2026-04-17T10:00:16Z"),
      duration_ms: null  // Still in this phase
    }
  ],
  assigned_agent_id: "john.network@ticketflow.ai",
  total_duration_ms: 16500,
  created_at: ISODate("2026-04-17T10:00:00Z"),
  updated_at: ISODate("2026-04-17T10:00:16Z")
}
```

## Troubleshooting

### Journey Not Created
- Check if `journey_service.create_journey()` is called in ticket submission
- Verify MongoDB connection
- Check backend logs for errors

### Agent Not Assigned
- Ensure agents exist in database (run `seed_agents.py`)
- Check agent department matches ticket category
- Verify agents are active and under capacity
- Check backend logs for assignment logic

### Journey Not Loading in UI
- Check browser console for API errors
- Verify JWT token is valid
- Check network tab for API responses
- Ensure journey API endpoints are registered in `main.py`

### Phase Not Updating
- Verify user has permission (admin/agent)
- Check phase transition is valid
- Ensure journey_id is correct
- Check backend logs for validation errors

## Next Steps

### Potential Enhancements
1. **Real-time Updates**: WebSocket integration for live phase updates
2. **SLA Tracking**: Add SLA breach warnings to journey timeline
3. **Agent Notes**: Allow agents to add notes at each phase
4. **Email Notifications**: Notify users on phase transitions
5. **Journey Analytics**: Dashboard showing average times per phase
6. **Agent Performance**: Track agent resolution times
7. **Escalation Path**: Show escalation history in journey
8. **Customer Feedback**: Collect feedback at resolution phase

## Files Modified/Created

### Backend
- ✅ `backend/models/ticket_journey.py` (new)
- ✅ `backend/services/journey_service.py` (new)
- ✅ `backend/routers/journey.py` (new)
- ✅ `backend/routers/tickets.py` (modified - added journey creation)
- ✅ `backend/main.py` (modified - registered journey router)
- ✅ `backend/seed_agents.py` (new)

### Frontend
- ✅ `frontend/src/services/api.js` (modified - added journeyAPI)
- ✅ `frontend/src/components/ticket/TicketJourney.jsx` (new)
- ✅ `frontend/src/components/ticket/JourneyBadge.jsx` (new)
- ✅ `frontend/src/pages/TicketJourneyDashboard.jsx` (new)
- ✅ `frontend/src/pages/TicketDetail.jsx` (modified - added journey component)
- ✅ `frontend/src/App.jsx` (modified - added journey route)
- ✅ `frontend/src/components/Sidebar.jsx` (modified - added journey link)

### Documentation
- ✅ `backend/JOURNEY_TRACKING_FEATURE.md` (API documentation)
- ✅ `JOURNEY_TRACKING_SETUP.md` (this file)

## Support

For issues or questions:
1. Check backend logs: `backend/main.py` console output
2. Check browser console for frontend errors
3. Verify API endpoints are accessible
4. Test with sample agents created by seed script
5. Review journey service logic in `backend/services/journey_service.py`

---

**Status**: ✅ Feature Complete - Ready for Testing
**Last Updated**: April 17, 2026
