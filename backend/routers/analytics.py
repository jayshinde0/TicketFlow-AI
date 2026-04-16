"""
routers/analytics.py — Dashboard analytics and model performance endpoints.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from loguru import logger

from core.database import (
    get_tickets_collection,
    get_feedback_collection,
    get_audit_logs_collection,
    get_root_cause_alerts_collection,
)
from core.security import get_current_user, require_role
from services.retrieval_service import retrieval_service

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/overview")
async def get_dashboard_overview(
    current_user: dict = Depends(get_current_user),  # Allow all authenticated users
):
    """Main dashboard KPIs: ticket counts, routing breakdown, SLA rate."""
    tickets = get_tickets_collection()
    feedback = get_feedback_collection()

    total = await tickets.count_documents({})
    open_count = await tickets.count_documents({"status": "open"})
    resolved_count = await tickets.count_documents({"status": "resolved"})
    auto_resolved = await tickets.count_documents(
        {
            "ai_analysis.routing_decision": "AUTO_RESOLVE",
            "status": "resolved",
        }
    )
    breached = await tickets.count_documents(
        {"ai_analysis.sla_breach_probability": {"$gt": 0.75}}
    )

    # Routing breakdown
    routing_pipeline = [
        {"$group": {"_id": "$ai_analysis.routing_decision", "count": {"$sum": 1}}}
    ]
    routing_docs = await tickets.aggregate(routing_pipeline).to_list(10)
    routing = {d["_id"]: d["count"] for d in routing_docs if d["_id"]}

    # Category breakdown
    cat_pipeline = [{"$group": {"_id": "$ai_analysis.category", "count": {"$sum": 1}}}]
    cat_docs = await tickets.aggregate(cat_pipeline).to_list(20)
    by_category = {d["_id"]: d["count"] for d in cat_docs if d["_id"]}

    # Avg processing time (last 100 tickets)
    perf_pipeline = [
        {"$match": {"ai_analysis.processing_time_ms": {"$exists": True}}},
        {"$sort": {"created_at": -1}},
        {"$limit": 100},
        {
            "$group": {
                "_id": None,
                "avg_ms": {"$avg": "$ai_analysis.processing_time_ms"},
            }
        },
    ]
    perf = await tickets.aggregate(perf_pipeline).to_list(1)
    avg_processing_ms = round(perf[0]["avg_ms"], 1) if perf else 0

    auto_rate = round(auto_resolved / resolved_count, 4) if resolved_count else 0
    sla_breach_rate = round(breached / total, 4) if total else 0

    return {
        "total_tickets": total,
        "open_tickets": open_count,
        "resolved_tickets": resolved_count,
        "auto_resolved_count": auto_resolved,
        "auto_resolve_rate": auto_rate,
        "sla_breach_rate": sla_breach_rate,
        "routing_breakdown": routing,
        "by_category": by_category,
        "avg_processing_time_ms": avg_processing_ms,
        "knowledge_base_size": retrieval_service.get_collection_stats().get(
            "resolved_tickets", 0
        ),
    }


@router.get("/model-performance")
async def get_model_performance(
    current_user: dict = Depends(require_role("admin")),
):
    """Return ML model metrics from the latest evaluation run."""
    import json
    from pathlib import Path

    eval_path = (
        Path(__file__).parent.parent / "ml" / "artifacts" / "evaluation_results.json"
    )

    if not eval_path.exists():
        return {"error": "No evaluation results found. Run ml/evaluate.py first."}

    with open(eval_path, "r") as f:
        return json.load(f)


@router.get("/confidence-distribution")
async def get_confidence_distribution(
    days: int = Query(default=7, ge=1, le=90),
    current_user: dict = Depends(get_current_user),  # Allow all authenticated users
):
    """Histogram of confidence scores over the last N days."""
    tickets = get_tickets_collection()
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    pipeline = [
        {
            "$match": {
                "created_at": {"$gte": cutoff},
                "ai_analysis.confidence_score": {"$exists": True},
            }
        },
        {
            "$project": {
                "bucket": {
                    "$multiply": [
                        {
                            "$floor": {
                                "$multiply": ["$ai_analysis.confidence_score", 10]
                            }
                        },
                        10,
                    ]
                }
            }
        },
        {"$group": {"_id": "$bucket", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]

    docs = await tickets.aggregate(pipeline).to_list(20)
    distribution = [
        {"range": f"{int(d['_id'])}-{int(d['_id'])+10}%", "count": d["count"]}
        for d in docs
        if d["_id"] is not None
    ]

    return {"days": days, "confidence_distribution": distribution}


@router.get("/ticket-volume")
async def get_ticket_volume(
    days: int = Query(default=30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),  # Allow all authenticated users
):
    """Daily ticket volume chart data for the last N days."""
    tickets = get_tickets_collection()
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    pipeline = [
        {"$match": {"created_at": {"$gte": cutoff}}},
        {
            "$group": {
                "_id": {
                    "year": {"$year": "$created_at"},
                    "month": {"$month": "$created_at"},
                    "day": {"$dayOfMonth": "$created_at"},
                },
                "count": {"$sum": 1},
                "auto_resolved": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$ai_analysis.routing_decision", "AUTO_RESOLVE"]},
                            1,
                            0,
                        ]
                    }
                },
            }
        },
        {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1}},
    ]

    docs = await tickets.aggregate(pipeline).to_list(None)
    data = [
        {
            "date": f"{d['_id']['year']}-{d['_id']['month']:02d}-{d['_id']['day']:02d}",
            "total": d["count"],
            "auto_resolved": d["auto_resolved"],
        }
        for d in docs
    ]

    return {"days": days, "volume": data}


@router.get("/sla-breakdown")
async def get_sla_breakdown(
    current_user: dict = Depends(get_current_user),  # Allow all authenticated users
):
    """SLA compliance data per category."""
    tickets = get_tickets_collection()

    pipeline = [
        {
            "$group": {
                "_id": "$ai_analysis.category",
                "total": {"$sum": 1},
                "at_risk": {
                    "$sum": {
                        "$cond": [
                            {"$gt": ["$ai_analysis.sla_breach_probability", 0.5]},
                            1,
                            0,
                        ]
                    }
                },
                "breached": {
                    "$sum": {
                        "$cond": [
                            {"$gt": ["$ai_analysis.sla_breach_probability", 0.75]},
                            1,
                            0,
                        ]
                    }
                },
            }
        }
    ]

    docs = await tickets.aggregate(pipeline).to_list(20)
    data = [
        {
            "category": d["_id"],
            "total": d["total"],
            "at_risk": d["at_risk"],
            "breached": d["breached"],
            "compliance_rate": round(1.0 - (d["breached"] / max(d["total"], 1)), 4),
        }
        for d in docs
        if d["_id"]
    ]

    return {"sla_breakdown": data}


@router.get("/root-cause-alerts")
async def get_root_cause_alerts(
    status: Optional[str] = "open",
    current_user: dict = Depends(get_current_user),  # Allow all authenticated users
):
    """Fetch incident spike alerts."""
    alerts_coll = get_root_cause_alerts_collection()
    query = {}
    if status:
        query["status"] = status

    cursor = alerts_coll.find(query).sort("timestamp", -1).limit(50)
    docs = await cursor.to_list(length=50)
    for d in docs:
        d.pop("_id", None)
        if hasattr(d.get("timestamp"), "isoformat"):
            d["timestamp"] = d["timestamp"].isoformat()

    return {"alerts": docs, "total": len(docs)}
