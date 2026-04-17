# Ticket Journey Tracking Feature

## Overview

The Journey Tracking feature allows users to see the complete lifecycle of their support tickets, including which phase the ticket is in and which agent is working on it.

## Features

### 1. **Ticket Journey Timeline**
Track every phase a ticket goes through:
- ✅ **Submitted** - User submits ticket
- ✅ **AI Processing** - AI analyzes the ticket
- ✅ **AI Resolved** - Ticket auto-resolved by AI (if confidence is high)
- ✅ **Assigned to Agent** - Ticket assigned to human agent (if escalated)
- ✅ **In Progress** - Agent is actively working on it
- ✅ **Resolved** - Ticket has been resolved
- ✅ **Closed** - Ticket is closed

### 2. **Agent Assignment**
- Automatic assignment to available agents based on department
- Load balancing across agents
- Shows agent name and department

### 3. **Sample Agents**
Pre-configured agents for each department:
- **NETWORK**: John Network, Sarah Network
- **SOFTWARE**: Mike Software, Lisa Software
- **DATABASE**: David Database, Emma Database
- **SECURITY**: Alex Security, Rachel Security
- **BILLING**: Tom Billing, Nina Billing
- **HR_FACILITIES**: Chris HR, Amy Facilities

## Setup

### 1. Seed Sample Agents

```bash
cd backend
python seed_agents.py
```

**Output:**
```
🔧 Seeding support agents...
  ✓ Created: John Network (NETWORK)
  ✓ Created: Sarah Network (NETWORK)
  ...
✅ Seeding complete!
   Created: 12 agents
   
📝 Default password for all agents: Agent@123
   Example login: john.network@ticketflow.ai / Agent@123
```

### 2. Restart Backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Get Ticket Journey

```http
GET /api/journey/{ticket_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "ticket_id": "TKT-ABC123",
  "ticket_title": "Application Crash on PDF Upload",
  "ticket_status": "in_progress",
  "journey": {
    "ticket_id": "TKT-ABC123",
    "current_phase": "in_progress",
    "current_status": "in_progress",
    "assigned_agent_email": "mike.software@ticketflow.ai",
    "assigned_agent_name": "Mike Software",
    "assigned_department": "SOFTWARE",
    "journey_steps": [
      {
        "step_id": "1",
        "phase": "submitted",
        "status": "completed",
        "timestamp": "2024-01-01T10:00:00Z",
        "duration_seconds": 5,
        "notes": "Ticket submitted by user"
      },
      {
        "step_id": "2",
        "phase": "ai_processing",
        "status": "completed",
        "timestamp": "2024-01-01T10:00:05Z",
        "duration_seconds": 15,
        "notes": "AI analyzed ticket: Software - High",
        "metadata": {
          "confidence": 0.85,
          "routing": "ESCALATE_TO_HUMAN"
        }
      },
      {
        "step_id": "3",
        "phase": "assigned_to_agent",
        "status": "completed",
        "timestamp": "2024-01-01T10:00:20Z",
        "duration_seconds": 300,
        "assigned_agent": "mike.software@ticketflow.ai",
        "assigned_agent_name": "Mike Software",
        "department": "SOFTWARE",
        "notes": "Ticket assigned to Mike Software (SOFTWARE)"
      },
      {
        "step_id": "4",
        "phase": "in_progress",
        "status": "current",
        "timestamp": "2024-01-01T10:05:20Z",
        "duration_seconds": null,
        "notes": "Mike Software started working on this ticket"
      }
    ],
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:05:20Z"
  }
}
```

### Assign Ticket to Agent

```http
POST /api/journey/{ticket_id}/assign
Authorization: Bearer <token>
Content-Type: application/json

{
  "agent_email": "mike.software@ticketflow.ai"
}
```

**Response:**
```json
{
  "message": "Ticket assigned successfully",
  "ticket_id": "TKT-ABC123",
  "assigned_to": "Mike Software",
  "department": "SOFTWARE"
}
```

### Start Working on Ticket

```http
POST /api/journey/{ticket_id}/start-work
Authorization: Bearer <token>
```

**Response:**
```json
{
  "message": "Ticket marked as in progress",
  "ticket_id": "TKT-ABC123"
}
```

### Get Agent Workload

```http
GET /api/journey/agent/{agent_email}/workload
Authorization: Bearer <token>
```

**Response:**
```json
{
  "agent_email": "mike.software@ticketflow.ai",
  "current_workload": 5
}
```

### Get Department Agents

```http
GET /api/journey/department/{department}/agents
Authorization: Bearer <token>
```

**Response:**
```json
{
  "department": "SOFTWARE",
  "agents": [
    {
      "email": "mike.software@ticketflow.ai",
      "full_name": "Mike Software",
      "role": "agent",
      "department": "SOFTWARE",
      "specialization": "Application Support",
      "is_active": true,
      "max_concurrent_tickets": 15,
      "current_workload": 5
    },
    {
      "email": "lisa.software@ticketflow.ai",
      "full_name": "Lisa Software",
      "role": "agent",
      "department": "SOFTWARE",
      "specialization": "Software Development",
      "is_active": true,
      "max_concurrent_tickets": 15,
      "current_workload": 3
    }
  ],
  "total_agents": 2
}
```

## How It Works

### 1. Ticket Submission
When a user submits a ticket:
1. Journey is created with "submitted" phase
2. AI processes the ticket
3. Journey updated with "ai_processing" phase

### 2. Routing Decision

**If AUTO_RESOLVE (confidence >= 0.70):**
- Journey updated with "ai_resolved" phase
- Ticket marked as resolved
- No agent assignment needed

**If SUGGEST_TO_AGENT or ESCALATE_TO_HUMAN:**
- System finds available agent in the appropriate department
- Agent with lowest workload is selected
- Ticket assigned to agent
- Journey updated with "assigned_to_agent" phase

### 3. Agent Work
When agent starts working:
- Agent calls `/api/journey/{ticket_id}/start-work`
- Journey updated with "in_progress" phase
- Ticket status changed to "in_progress"

### 4. Resolution
When ticket is resolved:
- Journey updated with "resolved" phase
- Duration calculated for each phase
- Complete timeline available to user

## Frontend Integration

### User Dashboard Component

```typescript
// Example React component
import { useEffect, useState } from 'react';

function TicketJourneyDashboard({ ticketId }) {
  const [journey, setJourney] = useState(null);

  useEffect(() => {
    fetch(`/api/journey/${ticketId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => setJourney(data.journey));
  }, [ticketId]);

  if (!journey) return <div>Loading...</div>;

  return (
    <div className="journey-timeline">
      <h2>Ticket Journey: {journey.ticket_id}</h2>
      
      {/* Current Status */}
      <div className="current-status">
        <h3>Current Phase: {journey.current_phase}</h3>
        {journey.assigned_agent_name && (
          <p>Assigned to: {journey.assigned_agent_name} ({journey.assigned_department})</p>
        )}
      </div>

      {/* Timeline */}
      <div className="timeline">
        {journey.journey_steps.map(step => (
          <div key={step.step_id} className={`step ${step.status}`}>
            <div className="step-icon">
              {step.status === 'completed' ? '✓' : '○'}
            </div>
            <div className="step-content">
              <h4>{step.phase}</h4>
              <p>{step.notes}</p>
              <small>{new Date(step.timestamp).toLocaleString()}</small>
              {step.duration_seconds && (
                <small> ({step.duration_seconds}s)</small>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

## Database Schema

### ticket_journeys Collection

```javascript
{
  "_id": ObjectId("..."),
  "ticket_id": "TKT-ABC123",
  "current_phase": "in_progress",
  "current_status": "in_progress",
  "assigned_agent_email": "mike.software@ticketflow.ai",
  "assigned_agent_name": "Mike Software",
  "assigned_department": "SOFTWARE",
  "journey_steps": [
    {
      "step_id": "1",
      "phase": "submitted",
      "status": "completed",
      "timestamp": ISODate("2024-01-01T10:00:00Z"),
      "duration_seconds": 5,
      "notes": "Ticket submitted by user"
    }
  ],
  "created_at": ISODate("2024-01-01T10:00:00Z"),
  "updated_at": ISODate("2024-01-01T10:05:20Z")
}
```

## Testing

### 1. Seed Agents
```bash
python seed_agents.py
```

### 2. Create Test Ticket
```bash
curl -X POST http://localhost:8000/api/tickets/ \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Test Ticket",
    "description": "Application crashes with OutOfMemoryException"
  }'
```

### 3. Get Journey
```bash
curl http://localhost:8000/api/journey/TKT-ABC123 \
  -H "Authorization: Bearer <token>"
```

### 4. Login as Agent
```
Email: mike.software@ticketflow.ai
Password: Agent@123
```

### 5. Start Working
```bash
curl -X POST http://localhost:8000/api/journey/TKT-ABC123/start-work \
  -H "Authorization: Bearer <agent_token>"
```

## Files Created

1. ✅ `backend/seed_agents.py` - Seed sample agents
2. ✅ `backend/models/ticket_journey.py` - Journey data models
3. ✅ `backend/services/journey_service.py` - Journey tracking logic
4. ✅ `backend/routers/journey.py` - Journey API endpoints
5. ✅ `backend/JOURNEY_TRACKING_FEATURE.md` - This documentation

## Files Modified

1. ✅ `backend/routers/tickets.py` - Added journey tracking on ticket creation
2. ✅ `backend/main.py` - Registered journey router

## Next Steps

1. **Frontend Dashboard**: Create React component to display journey timeline
2. **Real-time Updates**: Use WebSocket to push journey updates to users
3. **Agent Dashboard**: Show assigned tickets and workload
4. **Notifications**: Email/SMS when ticket is assigned or status changes
5. **Analytics**: Track average time per phase, agent performance

## Summary

✅ **Journey tracking implemented**
✅ **12 sample agents created across 6 departments**
✅ **Automatic agent assignment based on workload**
✅ **Complete API for journey management**
✅ **Ready for frontend integration**

Users can now track their ticket's progress from submission to resolution, including which agent is working on it!
