"""
routers/admin.py — Admin-only endpoints: model versions, retraining, knowledge base.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from loguru import logger

from core.database import (
    get_model_versions_collection,
    get_knowledge_articles_collection,
)
from core.security import require_role
from services.retraining_service import retraining_service
from services.notification_service import notification_service
from utils.helpers import paginate

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/model-versions")
async def get_model_versions(
    current_user: dict = Depends(require_role("admin")),
):
    """List all trained model versions."""
    collection = get_model_versions_collection()
    cursor = collection.find({}).sort("trained_at", -1).limit(20)
    docs = await cursor.to_list(20)
    for d in docs:
        d.pop("_id", None)
        if hasattr(d.get("trained_at"), "isoformat"):
            d["trained_at"] = d["trained_at"].isoformat()
    return {"versions": docs, "total": len(docs)}


@router.post("/retrain")
async def trigger_retraining(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_role("admin")),
):
    """
    Manually trigger model retraining.
    Runs as a background task to avoid HTTP timeout.
    """
    pending = await retraining_service.count_pending_feedback()

    async def _background_retrain():
        result = await retraining_service.run_retraining()
        await notification_service.notify_retraining_complete(
            new_f1=result.get("new_f1", 0.0),
            old_f1=result.get("old_f1", 0.0),
            promoted=result.get("promoted", False),
        )

    background_tasks.add_task(_background_retrain)

    return {
        "message": "Retraining started in background.",
        "pending_feedback_count": pending,
        "triggered_by": current_user["email"],
    }


@router.get("/knowledge-base")
async def get_knowledge_articles(
    category: str = None,
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(require_role("admin", "agent")),
):
    """List all auto-generated knowledge base articles."""
    collection = get_knowledge_articles_collection()
    query = {"category": category} if category else {}

    total = await collection.count_documents(query)
    paging = paginate(total, page, page_size)

    cursor = (
        collection.find(query)
        .sort("usage_count", -1)
        .skip(paging["skip"])
        .limit(paging["limit"])
    )
    docs = await cursor.to_list(paging["limit"])
    for d in docs:
        d.pop("_id", None)
        if hasattr(d.get("created_at"), "isoformat"):
            d["created_at"] = d["created_at"].isoformat()

    return {
        "articles": docs,
        "total": paging["total"],
        "page": paging["page"],
        "total_pages": paging["total_pages"],
    }


@router.get("/system-health")
async def get_system_health(
    current_user: dict = Depends(require_role("admin")),
):
    """Check connectivity to all system components."""
    from services.retrieval_service import retrieval_service

    health = {
        "api": "ok",
        "mongodb": "unknown",
        "chromadb": "unknown",
        "ollama": "unknown",
    }

    # MongoDB
    try:
        from core.database import get_tickets_collection

        col = get_tickets_collection()
        await col.find_one({}, {"_id": 1})
        health["mongodb"] = "ok"
    except Exception as e:
        health["mongodb"] = f"error: {str(e)[:50]}"

    # ChromaDB
    try:
        stats = retrieval_service.get_collection_stats()
        health["chromadb"] = "ok"
        health["chromadb_stats"] = stats
    except Exception as e:
        health["chromadb"] = f"error: {str(e)[:50]}"

    # Ollama
    try:
        import httpx
        from core.config import settings

        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.OLLAMA_URL}/api/tags")
            health["ollama"] = (
                "ok" if resp.status_code == 200 else f"http_{resp.status_code}"
            )
    except Exception as e:
        health["ollama"] = f"unavailable: {str(e)[:50]}"

    return health
