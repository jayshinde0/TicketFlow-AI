"""
tasks/background_tasks.py — FastAPI BackgroundTasks wrappers.
Replaces Celery entirely. Tasks run in the same process as the API server.
"""

import asyncio
from loguru import logger


async def build_knowledge_article_task(
    ticket_id: str,
    ticket_text: str,
    category: str,
    solution: str,
    resolution_time_hours: float,
):
    """Background task: build a KB article from a resolved ticket."""
    try:
        from services.knowledge_builder_service import knowledge_builder_service

        await knowledge_builder_service.build_article_from_ticket(
            ticket_id=ticket_id,
            ticket_text=ticket_text,
            category=category,
            solution=solution,
            resolution_time_hours=resolution_time_hours,
        )
        logger.info(f"KB article built for ticket {ticket_id}")
    except Exception as e:
        logger.error(f"KB article task failed for {ticket_id}: {e}")


async def check_and_retrain_task():
    """Background task: check feedback threshold and retrain if needed."""
    try:
        from services.retraining_service import retraining_service
        from services.notification_service import notification_service

        should = await retraining_service.should_retrain()
        if not should:
            logger.debug("Retraining not needed yet.")
            return

        result = await retraining_service.run_retraining()
        if result.get("success"):
            await notification_service.notify_retraining_complete(
                new_f1=result["new_f1"],
                old_f1=result["old_f1"],
                promoted=result["promoted"],
            )
            logger.info(
                f"Retraining complete: {result['old_f1']:.3f} → {result['new_f1']:.3f} "
                f"({'promoted' if result['promoted'] else 'rejected'})"
            )
    except Exception as e:
        logger.error(f"Retraining task failed: {e}")
