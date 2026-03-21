"""
routers/feedback.py — Agent feedback endpoints (approve / edit / reject).
Used by the Learning Agent (Agent 5) for retraining data collection.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from core.database import get_feedback_collection, get_tickets_collection
from core.security import get_current_user, require_role
from models.feedback import (
    FeedbackApprove, FeedbackEdit, FeedbackReject, FeedbackEscalate,
    FeedbackResponse, FeedbackStats,
)
from utils.helpers import utcnow

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])


# ─── Debug endpoint (remove after fixing) ────────────────────────────
@router.post("/{ticket_id}/approve-debug")
async def approve_debug(ticket_id: str):
    """Debug endpoint — no auth, step by step."""
    results = {}

    try:
        collection = get_tickets_collection()
        ticket = await collection.find_one({"ticket_id": ticket_id})
        results["step1_ticket_found"] = ticket is not None
        if not ticket:
            return {"error": "ticket not found", "steps": results}
        results["step1_status"] = ticket.get("status")
        results["step1_category"] = (
            ticket.get("ai_analysis") or {}
        ).get("category")
    except Exception as e:
        return {"crashed_at": "step1_get_ticket", "error": str(e)}

    try:
        from services.retrieval_service import retrieval_service
        results["step2_retrieval_service"] = str(type(retrieval_service))
    except Exception as e:
        return {"crashed_at": "step2_retrieval_service", "error": str(e)}

    try:
        from services.audit_service import audit_service
        results["step3_audit_service"] = str(type(audit_service))
    except Exception as e:
        return {"crashed_at": "step3_audit_service", "error": str(e)}

    try:
        from services.notification_service import notification_service
        results["step4_notification_service"] = str(
            type(notification_service)
        )
    except Exception as e:
        return {"crashed_at": "step4_notification_service", "error": str(e)}

    try:
        from services.retraining_service import retraining_service
        results["step5_retraining_service"] = str(type(retraining_service))
    except Exception as e:
        return {"crashed_at": "step5_retraining_service", "error": str(e)}

    try:
        from services.retraining_service import retraining_service
        should = await retraining_service.should_retrain()
        results["step6_should_retrain"] = should
    except Exception as e:
        return {"crashed_at": "step6_should_retrain_call", "error": str(e)}

    return {"all_steps_passed": True, "steps": results}


# ─── Private helpers ──────────────────────────────────────────────────

async def _get_ticket_or_404(ticket_id: str) -> dict:
    """Fetch ticket from MongoDB or raise 404."""
    collection = get_tickets_collection()
    doc = await collection.find_one({"ticket_id": ticket_id})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{ticket_id}' not found.",
        )
    doc.pop("_id", None)  # remove MongoDB ObjectId — not serializable
    return doc


async def _resolve_ticket(
    ticket_id: str,
    agent_id: str,
    action: str,
    final_response: str,
    corrected_category: str = None,
    corrected_priority: str = None,
) -> None:
    """Mark ticket as resolved in MongoDB."""
    tickets = get_tickets_collection()
    now = utcnow()

    update_fields = {
        "status": "resolved",
        "updated_at": now,
        "resolution": {
            "agent_id": agent_id,
            "action": action,
            "final_response": final_response,
            "resolved_at": now,
        },
    }

    if corrected_category:
        update_fields["ai_analysis.category"] = corrected_category
    if corrected_priority:
        update_fields["ai_analysis.priority"] = corrected_priority

    await tickets.update_one(
        {"ticket_id": ticket_id},
        {"$set": update_fields},
    )


async def _store_feedback(
    ticket_id: str,
    agent_id: str,
    action: str,
    ticket_doc: dict,
    corrected_response: str = None,
    corrected_category: str = None,
    corrected_priority: str = None,
    note: str = None,
) -> None:
    """
    Store feedback record for Agent 5 retraining.
    All sub-steps are individually guarded so one failure
    does not crash the entire approve/edit/reject flow.
    """
    # Step A — insert feedback document
    try:
        ai = ticket_doc.get("ai_analysis") or {}
        feedback_doc = {
            "ticket_id": ticket_id,
            "agent_id": agent_id,
            "timestamp": utcnow(),
            "original_category": ai.get("category"),
            "corrected_category": corrected_category,
            "original_priority": ai.get("priority"),
            "corrected_priority": corrected_priority,
            "original_response": ai.get("generated_response"),
            "corrected_response": corrected_response,
            "action": action,
            "correction_note": note,
            "used_for_retraining": False,
        }
        feedback_coll = get_feedback_collection()
        await feedback_coll.insert_one(feedback_doc)
        logger.debug(f"Feedback stored for ticket {ticket_id}")
    except Exception as e:
        logger.warning(f"[_store_feedback] insert failed for {ticket_id}: {e}")
        return  # don't continue if we can't even store feedback

    # Step B — check retraining threshold (non-fatal)
    try:
        from services.retraining_service import retraining_service
        should_retrain = await retraining_service.should_retrain()
        if should_retrain:
            logger.info(
                "Feedback threshold reached — retraining should be triggered."
            )
    except Exception as e:
        logger.warning(
            f"[_store_feedback] retraining check failed (non-fatal): {e}"
        )


async def _add_to_chromadb(
    ticket_id: str,
    ticket_doc: dict,
    solution: str,
    category: str,
    priority: str,
    resolution_time_hours: float = 1.0,
) -> None:
    """Add resolved ticket to ChromaDB (non-fatal if service unavailable)."""
    try:
        from services.retrieval_service import retrieval_service
        cleaned_text = (
            ticket_doc.get("cleaned_text")
            or ticket_doc.get("description", "")
        )
        if not cleaned_text:
            logger.warning(
                f"[_add_to_chromadb] No text for ticket {ticket_id}, skipping."
            )
            return
        await retrieval_service.add_resolved_ticket(
            ticket_id=ticket_id,
            text=cleaned_text,
            solution=solution,
            category=category,
            priority=priority,
            resolution_time_hours=resolution_time_hours,
        )
        logger.debug(f"Ticket {ticket_id} added to ChromaDB")
    except Exception as e:
        logger.warning(
            f"[_add_to_chromadb] ChromaDB update failed (non-fatal): {e}"
        )


async def _audit_action(
    ticket_id: str, action: str, note: str
) -> None:
    """Update audit log (non-fatal)."""
    try:
        from services.audit_service import audit_service
        await audit_service.update_agent_action(ticket_id, action, note)
    except Exception as e:
        logger.warning(f"[_audit_action] Audit log failed (non-fatal): {e}")


async def _notify_resolved(ticket_id: str, action: str) -> None:
    """Send resolution notification (non-fatal)."""
    try:
        from services.notification_service import notification_service
        await notification_service.notify_ticket_resolved(
            ticket_id, {"action": action}
        )
    except Exception as e:
        logger.warning(
            f"[_notify_resolved] Notification failed (non-fatal): {e}"
        )


# ─── POST /{ticket_id}/approve ────────────────────────────────────────

@router.post("/{ticket_id}/approve", response_model=FeedbackResponse)
async def approve_suggestion(
    ticket_id: str,
    body: FeedbackApprove = None,
    current_user: dict = Depends(
        require_role("agent", "admin", "senior_engineer")
    ),
):
    """Agent approves the AI-generated suggestion as-is."""
    try:
        ticket = await _get_ticket_or_404(ticket_id)
        ai = ticket.get("ai_analysis") or {}
        final_response = (
            ai.get("generated_response") or "Issue has been resolved."
        )

        # Core action — must succeed
        await _resolve_ticket(
            ticket_id=ticket_id,
            agent_id=current_user["user_id"],
            action="approved",
            final_response=final_response,
        )

        # Store feedback — must succeed (contains its own sub-guards)
        await _store_feedback(
            ticket_id=ticket_id,
            agent_id=current_user["user_id"],
            action="approved",
            ticket_doc=ticket,
            note=body.note if body else None,
        )

        # Non-fatal side effects
        await _add_to_chromadb(
            ticket_id=ticket_id,
            ticket_doc=ticket,
            solution=final_response,
            category=ai.get("category", "Software"),
            priority=ai.get("priority", "Medium"),
            resolution_time_hours=1.0,
        )
        await _audit_action(ticket_id, "approved", "resolved via AI response")
        await _notify_resolved(ticket_id, "approved")

        logger.info(
            f"Ticket {ticket_id} approved by {current_user['user_id']}"
        )
        return FeedbackResponse(
            success=True,
            message="Ticket approved and resolved successfully.",
            ticket_id=ticket_id,
            action="approved",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"APPROVE CRASHED for {ticket_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve ticket: {str(e)}",
        )


# ─── POST /{ticket_id}/edit ───────────────────────────────────────────

@router.post("/{ticket_id}/edit", response_model=FeedbackResponse)
async def edit_and_approve(
    ticket_id: str,
    body: FeedbackEdit,
    current_user: dict = Depends(
        require_role("agent", "admin", "senior_engineer")
    ),
):
    """Agent edits the AI response and approves the corrected version."""
    try:
        ticket = await _get_ticket_or_404(ticket_id)
        ai = ticket.get("ai_analysis") or {}

        effective_category = (
            body.corrected_category or ai.get("category", "Software")
        )
        effective_priority = (
            body.corrected_priority or ai.get("priority", "Medium")
        )

        # Core action — must succeed
        await _resolve_ticket(
            ticket_id=ticket_id,
            agent_id=current_user["user_id"],
            action="edited",
            final_response=body.corrected_response,
            corrected_category=body.corrected_category,
            corrected_priority=body.corrected_priority,
        )

        # Store feedback — must succeed
        await _store_feedback(
            ticket_id=ticket_id,
            agent_id=current_user["user_id"],
            action="edited",
            ticket_doc=ticket,
            corrected_response=body.corrected_response,
            corrected_category=body.corrected_category,
            corrected_priority=body.corrected_priority,
            note=body.note,
        )

        # Non-fatal side effects
        await _add_to_chromadb(
            ticket_id=ticket_id,
            ticket_doc=ticket,
            solution=body.corrected_response,
            category=effective_category,
            priority=effective_priority,
            resolution_time_hours=1.5,
        )
        await _audit_action(ticket_id, "edited", "resolved with agent edits")
        await _notify_resolved(ticket_id, "edited")

        logger.info(
            f"Ticket {ticket_id} edited and approved by "
            f"{current_user['user_id']}"
        )
        return FeedbackResponse(
            success=True,
            message="Ticket resolved with your corrections applied.",
            ticket_id=ticket_id,
            action="edited",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"EDIT CRASHED for {ticket_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to edit ticket: {str(e)}",
        )


# ─── POST /{ticket_id}/reject ─────────────────────────────────────────

@router.post("/{ticket_id}/reject", response_model=FeedbackResponse)
async def reject_and_resolve(
    ticket_id: str,
    body: FeedbackReject,
    current_user: dict = Depends(
        require_role("agent", "admin", "senior_engineer")
    ),
):
    """Agent rejects AI response and sends a manual resolution."""
    try:
        ticket = await _get_ticket_or_404(ticket_id)
        ai = ticket.get("ai_analysis") or {}

        # Core action — must succeed
        await _resolve_ticket(
            ticket_id=ticket_id,
            agent_id=current_user["user_id"],
            action="rejected",
            final_response=body.manual_response,
            corrected_category=body.corrected_category,
            corrected_priority=body.corrected_priority,
        )

        # Store feedback — must succeed
        await _store_feedback(
            ticket_id=ticket_id,
            agent_id=current_user["user_id"],
            action="rejected",
            ticket_doc=ticket,
            corrected_response=body.manual_response,
            corrected_category=body.corrected_category,
            corrected_priority=body.corrected_priority,
            note=body.rejection_reason,
        )

        # Non-fatal side effects
        await _audit_action(
            ticket_id, "rejected", "manually resolved by agent"
        )
        await _notify_resolved(ticket_id, "rejected")

        logger.info(
            f"Ticket {ticket_id} rejected and manually resolved by "
            f"{current_user['user_id']}"
        )
        return FeedbackResponse(
            success=True,
            message="Ticket manually resolved.",
            ticket_id=ticket_id,
            action="rejected",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"REJECT CRASHED for {ticket_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject ticket: {str(e)}",
        )


# ─── GET /stats ───────────────────────────────────────────────────────

@router.get("/stats", response_model=FeedbackStats)
async def get_feedback_stats(
    current_user: dict = Depends(require_role("admin", "agent")),
):
    """Aggregate feedback statistics for the admin dashboard."""
    collection = get_feedback_collection()

    pipeline = [
        {
            "$group": {
                "_id": None,
                "total": {"$sum": 1},
                "approved": {
                    "$sum": {
                        "$cond": [{"$eq": ["$action", "approved"]}, 1, 0]
                    }
                },
                "edited": {
                    "$sum": {
                        "$cond": [{"$eq": ["$action", "edited"]}, 1, 0]
                    }
                },
                "rejected": {
                    "$sum": {
                        "$cond": [{"$eq": ["$action", "rejected"]}, 1, 0]
                    }
                },
                "escalated": {
                    "$sum": {
                        "$cond": [{"$eq": ["$action", "escalated"]}, 1, 0]
                    }
                },
                "pending": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$used_for_retraining", False]}, 1, 0
                        ]
                    }
                },
                "cat_corrections": {
                    "$sum": {
                        "$cond": [
                            {"$ne": ["$corrected_category", None]}, 1, 0
                        ]
                    }
                },
                "pri_corrections": {
                    "$sum": {
                        "$cond": [
                            {"$ne": ["$corrected_priority", None]}, 1, 0
                        ]
                    }
                },
            }
        }
    ]

    results = await collection.aggregate(pipeline).to_list(length=1)
    stats = results[0] if results else {}
    total = max(stats.get("total", 0), 1)  # avoid division by zero

    return FeedbackStats(
        total_feedback=stats.get("total", 0),
        approved_count=stats.get("approved", 0),
        edited_count=stats.get("edited", 0),
        rejected_count=stats.get("rejected", 0),
        escalated_count=stats.get("escalated", 0),
        approval_rate=round(stats.get("approved", 0) / total, 4),
        edit_rate=round(stats.get("edited", 0) / total, 4),
        rejection_rate=round(stats.get("rejected", 0) / total, 4),
        pending_retraining=stats.get("pending", 0),
        category_correction_rate=round(
            stats.get("cat_corrections", 0) / total, 4
        ),
        priority_correction_rate=round(
            stats.get("pri_corrections", 0) / total, 4
        ),
    )