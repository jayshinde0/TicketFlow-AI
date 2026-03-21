"""
backend/main.py — FastAPI application entry point.

Starts the TicketFlow AI backend:
- Registers all 7 routers
- Sets up MongoDB connections on startup
- Configures APScheduler for background tasks (SLA monitoring, root cause)
- Configures CORS for React frontend
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from core.config import settings
from core.database import db_manager as database_manager, create_indexes


# ─── Application lifespan ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    logger.info("═══ TicketFlow AI Backend Starting ═══")

    # 1. Connect MongoDB
    await database_manager.connect()
    await create_indexes()
    logger.info("MongoDB connected and indexes created.")

    # 2. Start APScheduler for background jobs
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.interval import IntervalTrigger

        scheduler = AsyncIOScheduler()

        # Root cause detection — every 5 minutes
        from services.root_cause_service import root_cause_service
        scheduler.add_job(
            root_cause_service.run_detection,
            trigger=IntervalTrigger(minutes=5),
            id="root_cause_detection",
            replace_existing=True,
        )

        # SLA warning check — every 2 minutes
        scheduler.add_job(
            check_sla_warnings,
            trigger=IntervalTrigger(minutes=2),
            id="sla_warning_check",
            replace_existing=True,
        )

        scheduler.start()
        app.state.scheduler = scheduler
        logger.info("APScheduler started: root_cause(5min), sla_check(2min)")
    except ImportError:
        logger.warning("apscheduler not installed. Background jobs disabled.")

    logger.info("TicketFlow AI is ready!")

    yield   # --- Application running ---

    logger.info("Shutting down TicketFlow AI...")
    if hasattr(app.state, "scheduler"):
        app.state.scheduler.shutdown(wait=False)
    await database_manager.disconnect()
    logger.info("MongoDB disconnected. Goodbye.")


async def check_sla_warnings():
    """
    Scheduled job: check all open tickets for SLA risk and notify agents.
    """
    from core.database import get_tickets_collection
    from services.sla_service import sla_service
    from services.notification_service import notification_service
    from datetime import datetime, timezone

    try:
        collection = get_tickets_collection()
        cursor = collection.find(
            {"status": "open"},
            {"ticket_id": 1, "ai_analysis.category": 1, "ai_analysis.priority": 1,
             "created_at": 1}
        )
        tickets = await cursor.to_list(length=500)

        now = datetime.now(timezone.utc)
        for t in tickets:
            ai = t.get("ai_analysis") or {}
            category = ai.get("category", "Software")
            priority = ai.get("priority", "Medium")
            created_at = t.get("created_at")
            if not created_at:
                continue

            sla_info = sla_service.get_sla_info(category, priority, created_at)
            mins_left = sla_info["minutes_remaining"]

            # Warn when < 20% SLA time remaining
            sla_mins = sla_info["sla_minutes"]
            if 0 < mins_left < sla_mins * 0.20:
                await notification_service.notify_sla_warning(
                    ticket_id=t["ticket_id"],
                    minutes_left=mins_left,
                    category=category,
                    priority=priority,
                )
    except Exception as e:
        logger.error(f"SLA warning check failed: {e}")


# ─── FastAPI application ──────────────────────────────────────────────
app = FastAPI(
    title="TicketFlow AI",
    description="Intelligent Auto-Handling of Support Tickets with Confidence-Based HITL",
    version="1.0.0",
    lifespan=lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Register all routers ─────────────────────────────────────────────
from routers.auth import router as auth_router
from routers.tickets import router as tickets_router
from routers.feedback import router as feedback_router
from routers.agents import router as agents_router
from routers.analytics import router as analytics_router
from routers.admin import router as admin_router
from routers.websocket import router as ws_router

app.include_router(auth_router)
app.include_router(tickets_router)
app.include_router(feedback_router)
app.include_router(agents_router)
app.include_router(analytics_router)
app.include_router(admin_router)
app.include_router(ws_router)


# ─── Health endpoints ─────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "TicketFlow AI"}


@app.get("/")
async def root():
    return {
        "name": "TicketFlow AI",
        "version": "1.0.0",
        "docs": "/docs",
    }
