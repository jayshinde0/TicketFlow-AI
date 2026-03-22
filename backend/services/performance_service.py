"""
services/performance_service.py — Per-ticket performance logging and analytics.
Stores per-stage timing breakdown and provides p50/p95/p99 latency metrics.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from loguru import logger


class PerformanceService:
    """
    Captures per-ticket pipeline stage timings and provides
    aggregate latency metrics (p50, p95, p99).
    """

    async def log_pipeline_performance(
        self,
        ticket_id: str,
        stage_timings: Dict[str, int],
    ) -> None:
        """
        Store per-stage timing for a ticket in the performance_logs collection.
        """
        try:
            from core.database import get_db
            db = get_db()
            if db is None:
                return

            doc = {
                "ticket_id": ticket_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **stage_timings,
            }
            await db["performance_logs"].insert_one(doc)
        except Exception as e:
            logger.debug(f"Performance log failed (non-fatal): {e}")

    async def get_latency_metrics(
        self, hours: int = 24
    ) -> Dict[str, Any]:
        """
        Calculate p50, p95, p99 latency for total pipeline time
        over the last N hours.
        """
        try:
            from core.database import get_db
            db = get_db()
            if db is None:
                return self._empty_metrics()

            cutoff = (
                datetime.now(timezone.utc) - timedelta(hours=hours)
            ).isoformat()

            cursor = db["performance_logs"].find(
                {"timestamp": {"$gte": cutoff}},
                {"total_ms": 1, "_id": 0},
            ).sort("timestamp", -1).limit(1000)

            totals = []
            async for doc in cursor:
                t = doc.get("total_ms")
                if t is not None:
                    totals.append(t)

            if not totals:
                return self._empty_metrics()

            totals.sort()
            n = len(totals)

            return {
                "sample_count": n,
                "period_hours": hours,
                "p50_ms": totals[int(n * 0.5)],
                "p95_ms": totals[int(n * 0.95)] if n >= 20 else totals[-1],
                "p99_ms": totals[int(n * 0.99)] if n >= 100 else totals[-1],
                "min_ms": totals[0],
                "max_ms": totals[-1],
                "avg_ms": int(sum(totals) / n),
            }

        except Exception as e:
            logger.error(f"Latency metrics failed: {e}")
            return self._empty_metrics()

    async def get_stage_breakdown(
        self, hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get average time per pipeline stage over the last N hours.
        """
        try:
            from core.database import get_db
            db = get_db()
            if db is None:
                return {}

            cutoff = (
                datetime.now(timezone.utc) - timedelta(hours=hours)
            ).isoformat()

            pipeline = [
                {"$match": {"timestamp": {"$gte": cutoff}}},
                {"$group": {
                    "_id": None,
                    "avg_preprocessing_ms": {"$avg": "$preprocessing_ms"},
                    "avg_classification_ms": {"$avg": "$classification_ms"},
                    "avg_retrieval_ms": {"$avg": "$retrieval_ms"},
                    "avg_sentiment_ms": {"$avg": "$sentiment_ms"},
                    "avg_sla_prediction_ms": {"$avg": "$sla_prediction_ms"},
                    "avg_routing_ms": {"$avg": {"$ifNull": ["$hitl_routing_ms", 0]}},
                    "avg_llm_generation_ms": {"$avg": "$llm_generation_ms"},
                    "avg_safety_check_ms": {"$avg": "$safety_check_ms"},
                    "avg_threat_analysis_ms": {"$avg": {"$ifNull": ["$threat_analysis_ms", 0]}},
                    "avg_total_ms": {"$avg": "$total_ms"},
                    "count": {"$sum": 1},
                }},
            ]

            result = {}
            async for doc in db["performance_logs"].aggregate(pipeline):
                doc.pop("_id", None)
                # Round all values
                result = {k: round(v) if isinstance(v, float) else v for k, v in doc.items()}

            return result

        except Exception as e:
            logger.error(f"Stage breakdown failed: {e}")
            return {}

    def _empty_metrics(self) -> Dict[str, Any]:
        return {
            "sample_count": 0,
            "period_hours": 24,
            "p50_ms": 0,
            "p95_ms": 0,
            "p99_ms": 0,
            "min_ms": 0,
            "max_ms": 0,
            "avg_ms": 0,
        }


# Module-level singleton
performance_service = PerformanceService()
