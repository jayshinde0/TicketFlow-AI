"""
routers/queue.py — Priority queue monitor endpoints.
GET /api/queue/status — queue depth, rate, wait times
GET /api/queue/performance — latency metrics (p50/p95/p99)
GET /api/queue/stage-breakdown — per-stage average times
"""

from fastapi import APIRouter, Depends
from loguru import logger

from core.security import require_role
from services.performance_service import performance_service
from services.cache_service import cache_service

router = APIRouter(prefix="/api/queue", tags=["Queue Monitor"])


@router.get("/status")
async def queue_status(
    current_user: dict = Depends(require_role("admin", "agent")),
):
    """
    Get current queue status: ticket counts by status, processing rate, etc.
    """
    from core.database import get_db
    from datetime import datetime, timezone, timedelta

    db = get_db()
    if db is None:
        return {"error": "Database unavailable"}

    now = datetime.now(timezone.utc)
    one_hour_ago = (now - timedelta(hours=1)).isoformat()

    # Count tickets by status
    open_count = await db["tickets"].count_documents({"status": "open"})
    in_progress = await db["tickets"].count_documents({"status": "in_progress"})
    resolved_1h = await db["tickets"].count_documents(
        {
            "status": "resolved",
            "updated_at": {"$gte": one_hour_ago},
        }
    )

    # Count by routing decision
    auto_resolved = await db["tickets"].count_documents(
        {
            "ai_analysis.routing_decision": "AUTO_RESOLVE",
        }
    )
    suggest_count = await db["tickets"].count_documents(
        {
            "ai_analysis.routing_decision": "SUGGEST_TO_AGENT",
        }
    )
    escalated = await db["tickets"].count_documents(
        {
            "ai_analysis.routing_decision": "ESCALATE_TO_HUMAN",
        }
    )

    # Count by priority in queue
    priority_breakdown = {}
    for p in ["Critical", "High", "Medium", "Low"]:
        count = await db["tickets"].count_documents(
            {
                "status": {"$in": ["open", "in_progress"]},
                "ai_analysis.priority": p,
            }
        )
        priority_breakdown[p] = count

    return {
        "queue_depth": {
            "open": open_count,
            "in_progress": in_progress,
            "total_waiting": open_count + in_progress,
        },
        "resolved_last_hour": resolved_1h,
        "processing_rate_per_hour": resolved_1h,
        "routing_breakdown": {
            "auto_resolved": auto_resolved,
            "suggest_to_agent": suggest_count,
            "escalated": escalated,
        },
        "priority_in_queue": priority_breakdown,
        "cache_stats": cache_service.get_stats(),
    }


@router.get("/performance")
async def queue_performance(
    hours: int = 24,
    current_user: dict = Depends(require_role("admin")),
):
    """Get p50/p95/p99 latency metrics."""
    metrics = await performance_service.get_latency_metrics(hours)
    return metrics


@router.get("/stage-breakdown")
async def stage_breakdown(
    hours: int = 24,
    current_user: dict = Depends(require_role("admin")),
):
    """Get average latency per pipeline stage."""
    breakdown = await performance_service.get_stage_breakdown(hours)
    return breakdown
