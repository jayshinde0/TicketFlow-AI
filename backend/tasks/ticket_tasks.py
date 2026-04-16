"""
tasks/ticket_tasks.py — Celery tasks for background processing.
Handles knowledge article generation and model retraining triggers.
"""

from celery import Celery
from loguru import logger

from core.config import settings

# Celery app instance
celery_app = Celery(
    "ticketflow_tasks",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/1",
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_expires=3600,  # 1 hour
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "tasks.ticket_tasks.build_knowledge_article": {"queue": "knowledge"},
        "tasks.ticket_tasks.trigger_retraining": {"queue": "ml"},
    },
)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # retry after 60 seconds
    name="tasks.ticket_tasks.build_knowledge_article",
)
def build_knowledge_article(
    self,
    ticket_id: str,
    ticket_text: str,
    category: str,
    solution: str,
    resolution_time_hours: float,
):
    """
    Background task: Build a KB article from a resolved ticket.
    Calls the async knowledge_builder_service synchronously.
    """
    import asyncio

    async def _run():
        from services.knowledge_builder_service import knowledge_builder_service

        await knowledge_builder_service.build_article_from_ticket(
            ticket_id=ticket_id,
            ticket_text=ticket_text,
            category=category,
            solution=solution,
            resolution_time_hours=resolution_time_hours,
        )

    try:
        asyncio.run(_run())
        logger.info(f"KB article built for ticket {ticket_id}")
    except Exception as exc:
        logger.error(f"KB article task failed for {ticket_id}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    max_retries=1,
    name="tasks.ticket_tasks.trigger_retraining",
)
def trigger_retraining(self):
    """
    Background task: Check feedback threshold and retrain if needed.
    Scheduled by APScheduler or triggered manually via admin API.
    """
    import asyncio

    async def _run():
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

    try:
        asyncio.run(_run())
    except Exception as exc:
        logger.error(f"Retraining task failed: {exc}")
        raise self.retry(exc=exc)
