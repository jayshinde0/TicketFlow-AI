"""
services/retraining_service.py — Agent 5: Learning Agent.

Monitors feedback count and triggers model retraining when threshold
is reached. Evaluates new model and promotes only if F1 improves.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from loguru import logger

from core.config import settings


class RetrainingService:
    """
    Agent 5 — The Learning Agent.

    Responsibilities:
    1. Count unused feedback since last retrain
    2. When count >= FEEDBACK_RETRAIN_THRESHOLD: trigger retraining
    3. Load training data + feedback corrections
    4. Retrain category + priority classifiers
    5. Evaluate new model vs current model
    6. Promote if new F1 > old F1 - 0.02 (within tolerance)
    7. Log model version to MongoDB
    """

    # ─── Version helpers ─────────────────────────────────────────────

    def _get_current_model_version(self) -> str:
        """Get model version identifier from artifacts file."""
        version_file = (
            Path(__file__).parent.parent / "ml" / "artifacts" / "current_version.txt"
        )
        if version_file.exists():
            return version_file.read_text().strip()
        return "v1"

    def _save_model_version(self, version: str) -> None:
        """Persist current model version string to disk."""
        version_file = (
            Path(__file__).parent.parent / "ml" / "artifacts" / "current_version.txt"
        )
        version_file.parent.mkdir(parents=True, exist_ok=True)
        version_file.write_text(version)

    def _increment_version(self, current: str) -> str:
        """Increment version string: v1 → v2, v3 → v4, etc."""
        try:
            num = int(current.lstrip("v") or "1")
            return f"v{num + 1}"
        except ValueError:
            return "v2"

    # ─── Feedback queries ─────────────────────────────────────────────

    async def count_pending_feedback(self) -> int:
        """Count feedback records not yet used for retraining."""
        try:
            from core.database import get_feedback_collection

            collection = get_feedback_collection()
            count = await collection.count_documents({"used_for_retraining": False})
            return count
        except Exception as e:
            logger.warning(f"count_pending_feedback failed: {e}")
            return 0

    async def should_retrain(self) -> bool:
        """
        Returns True if unused feedback count >= threshold.
        Always safe — returns False on any error.
        """
        try:
            pending = await self.count_pending_feedback()
            threshold = settings.FEEDBACK_RETRAIN_THRESHOLD
            logger.debug(f"Pending feedback: {pending}/{threshold}")
            return pending >= threshold
        except Exception as e:
            logger.warning(f"should_retrain check failed (non-fatal): {e}")
            return False

    async def get_feedback_for_retraining(self) -> list:
        """Load all unused feedback records for model fine-tuning."""
        try:
            from core.database import get_feedback_collection

            collection = get_feedback_collection()
            cursor = collection.find({"used_for_retraining": False})
            docs = await cursor.to_list(length=None)
            # Remove MongoDB _id — not serializable outside MongoDB context
            for doc in docs:
                doc.pop("_id", None)
            return docs
        except Exception as e:
            logger.error(f"get_feedback_for_retraining failed: {e}")
            return []

    async def mark_feedback_used(self) -> int:
        """
        Mark ALL pending feedback records as used_for_retraining=True.
        Returns count of records updated.
        """
        try:
            from core.database import get_feedback_collection

            collection = get_feedback_collection()
            result = await collection.update_many(
                {"used_for_retraining": False},
                {"$set": {"used_for_retraining": True}},
            )
            logger.info(f"Marked {result.modified_count} feedback records as used.")
            return result.modified_count
        except Exception as e:
            logger.error(f"mark_feedback_used failed: {e}")
            return 0

    async def get_retraining_status(self) -> dict:
        """
        Return current retraining status for the admin dashboard.
        """
        try:
            pending = await self.count_pending_feedback()
            threshold = settings.FEEDBACK_RETRAIN_THRESHOLD
            current_version = self._get_current_model_version()

            from core.database import get_model_versions_collection

            version_coll = get_model_versions_collection()
            active_model = await version_coll.find_one({"is_active": True})

            return {
                "current_version": current_version,
                "pending_feedback": pending,
                "threshold": threshold,
                "progress_pct": round(min(pending / max(threshold, 1), 1.0) * 100, 1),
                "ready_to_retrain": pending >= threshold,
                "last_trained_at": (
                    active_model.get("trained_at") if active_model else None
                ),
                "last_f1": (active_model.get("category_f1") if active_model else None),
            }
        except Exception as e:
            logger.warning(f"get_retraining_status failed: {e}")
            return {
                "current_version": "v1",
                "pending_feedback": 0,
                "threshold": settings.FEEDBACK_RETRAIN_THRESHOLD,
                "progress_pct": 0.0,
                "ready_to_retrain": False,
                "last_trained_at": None,
                "last_f1": None,
            }

    # ─── Core retraining pipeline ─────────────────────────────────────

    async def run_retraining(self) -> dict:
        """
        Execute the full retraining pipeline.

        Steps:
        1. Load original training data
        2. Load feedback corrections
        3. Retrain all models (skips GridSearch for speed)
        4. Evaluate and compare to current model
        5. Promote or reject new model
        6. Log result to MongoDB model_versions collection

        Returns:
            Dict with retraining outcome details.
        """
        logger.info("═══ Starting Model Retraining ═══")
        start_time = datetime.now(timezone.utc)

        # Add project root to path so ml.train is importable
        sys.path.insert(0, str(Path(__file__).parent.parent))

        # Import training pipeline
        try:
            from ml.train import train_all_models
        except ImportError as e:
            logger.error(f"Cannot import training module: {e}")
            return {"success": False, "error": str(e)}

        # Load feedback
        feedback_docs = await self.get_feedback_for_retraining()
        logger.info(f"Retraining with {len(feedback_docs)} feedback corrections.")

        # Run training
        try:
            metrics = train_all_models(
                data_dir=None,
                use_grid_search=False,
                skip_sla=False,
                feedback_docs=feedback_docs,
            )
        except Exception as e:
            logger.error(f"train_all_models failed: {e}")
            return {"success": False, "error": str(e)}

        # Compare with current model
        new_f1 = metrics.get("category_f1_macro", 0.0)
        current_version = self._get_current_model_version()

        try:
            from core.database import get_model_versions_collection

            version_collection = get_model_versions_collection()
            current_doc = await version_collection.find_one({"is_active": True})
            old_f1 = current_doc.get("category_f1", 0.0) if current_doc else 0.0
        except Exception as e:
            logger.warning(f"Failed to load current model metrics: {e}")
            old_f1 = 0.0

        # Promote if within tolerance
        promoted = new_f1 >= (old_f1 - 0.02)

        if promoted:
            new_version = self._increment_version(current_version)
            self._save_model_version(new_version)

            try:
                from core.database import get_model_versions_collection

                version_collection = get_model_versions_collection()
                await version_collection.update_many(
                    {"is_active": True},
                    {"$set": {"is_active": False}},
                )
            except Exception as e:
                logger.warning(f"Failed to deactivate old model version: {e}")

            logger.info(
                f"Model promoted: {current_version} → {new_version} "
                f"(F1: {old_f1:.4f} → {new_f1:.4f})"
            )
        else:
            new_version = current_version
            logger.warning(
                f"New model not promoted. "
                f"F1 regression: {old_f1:.4f} → {new_f1:.4f}. "
                f"Keeping {current_version}."
            )

        # Log version record to MongoDB
        version_doc = {
            "version": new_version,
            "trained_at": datetime.now(timezone.utc),
            "training_size": metrics.get("training_samples", 0),
            "category_f1": round(new_f1, 4),
            "priority_f1": round(metrics.get("priority_f1_macro", 0.0), 4),
            "sla_auc": round(metrics.get("sla_auc_roc", 0.0), 4),
            "feedback_examples_added": len(feedback_docs),
            "is_active": promoted,
            "evaluation_metrics": metrics.get("per_category_metrics", {}),
            "promoted": promoted,
        }

        try:
            from core.database import get_model_versions_collection

            version_collection = get_model_versions_collection()
            await version_collection.insert_one(version_doc)
        except Exception as e:
            logger.warning(f"Failed to save version doc to MongoDB: {e}")

        # Mark feedback as used only if promoted
        if promoted:
            await self.mark_feedback_used()

        end_time = datetime.now(timezone.utc)
        duration_seconds = int((end_time - start_time).total_seconds())

        result = {
            "success": True,
            "version": new_version,
            "promoted": promoted,
            "old_f1": round(old_f1, 4),
            "new_f1": round(new_f1, 4),
            "f1_delta": round(new_f1 - old_f1, 4),
            "feedback_used": len(feedback_docs),
            "training_duration_seconds": duration_seconds,
        }

        logger.info(f"Retraining complete: {result}")
        return result

    # ─── Manual trigger (admin endpoint) ─────────────────────────────

    async def trigger_manual_retraining(self) -> dict:
        """
        Manually trigger retraining from the admin dashboard.
        Bypasses the threshold check.
        """
        logger.info("Manual retraining triggered by admin.")
        pending = await self.count_pending_feedback()

        if pending == 0:
            logger.info(
                "No pending feedback for retraining. "
                "Running with original data only."
            )

        return await self.run_retraining()


# ─── Module-level singleton ───────────────────────────────────────────
retraining_service = RetrainingService()
