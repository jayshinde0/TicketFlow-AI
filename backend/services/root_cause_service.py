"""
services/root_cause_service.py — Background root cause analysis engine.
Runs every 5 minutes; detects ticket spikes and generates incident alerts.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict
from loguru import logger

from core.config import settings
from core.database import (
    get_tickets_collection,
    get_root_cause_alerts_collection,
)
from services.llm_service import llm_service
from services.notification_service import notification_service


class RootCauseService:
    """
    Spike detection and root cause analysis engine.
    
    Runs every 5 minutes (triggered by APScheduler in main.py).
    Detects ticket volume spikes per domain and generates incident alerts.
    """

    async def _get_recent_tickets(
        self,
        category: str,
        window_minutes: int,
    ) -> List[dict]:
        """Query recent tickets in a category within time window."""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        try:
            collection = get_tickets_collection()
            cursor = collection.find({
                "ai_analysis.category": category,
                "created_at": {"$gte": cutoff},
            })
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"RootCause query error: {e}")
            return []

    def _extract_top_keywords(
        self,
        tickets: List[dict],
        top_n: int = 5,
    ) -> List[str]:
        """Extract most common TF-IDF-style keywords from spike tickets."""
        from sklearn.feature_extraction.text import TfidfVectorizer
        import numpy as np

        texts = []
        for t in tickets:
            text = t.get("cleaned_text") or t.get("description", "")
            if text:
                texts.append(text)

        if not texts:
            return []

        try:
            tfidf = TfidfVectorizer(
                max_features=50,
                stop_words="english",
                ngram_range=(1, 2),
            )
            X = tfidf.fit_transform(texts)
            feature_names = tfidf.get_feature_names_out()
            scores = X.mean(axis=0).A1
            top_indices = np.argsort(scores)[::-1][:top_n]
            return [feature_names[i] for i in top_indices]
        except Exception:
            return []

    def _determine_severity(self, category: str, ticket_count: int) -> str:
        """Determine alert severity based on domain and volume."""
        if category == "Security":
            return "P0"
        elif category in ("Database", "Network") and ticket_count >= 5:
            return "P0"
        elif ticket_count >= 8:
            return "P1"
        return "P2"

    async def run_detection(self) -> List[dict]:
        """
        Main spike detection loop — called every 5 minutes.

        Returns:
            List of newly created alert dicts.
        """
        thresholds = settings.ROOT_CAUSE_THRESHOLDS
        new_alerts = []
        alerts_collection = get_root_cause_alerts_collection()

        for category, config in thresholds.items():
            count_threshold = config["count"]
            window_minutes = config["window_minutes"]

            tickets = await self._get_recent_tickets(category, window_minutes)
            ticket_count = len(tickets)

            if ticket_count < count_threshold:
                continue  # No spike

            # Check if we already have an open alert for this category
            existing = await alerts_collection.find_one({
                "category": category,
                "status": "open",
            })
            if existing:
                continue  # Already alerted

            logger.warning(
                f"SPIKE DETECTED: {category} | "
                f"{ticket_count} tickets in {window_minutes} min"
            )

            # Extract common keywords
            keywords = self._extract_top_keywords(tickets)

            # Generate root cause hypothesis via LLM
            hypothesis = await llm_service.generate_root_cause_hypothesis(
                keywords=keywords,
                category=category,
                ticket_count=ticket_count,
                window_minutes=window_minutes,
            )

            severity = self._determine_severity(category, ticket_count)

            # Build alert document
            alert = {
                "alert_id": f"RCA-{str(uuid.uuid4())[:8].upper()}",
                "timestamp": datetime.now(timezone.utc),
                "category": category,
                "ticket_count": ticket_count,
                "time_window_minutes": window_minutes,
                "common_keywords": keywords,
                "root_cause_hypothesis": hypothesis,
                "severity": severity,
                "affected_ticket_ids": [
                    t.get("ticket_id") for t in tickets
                    if t.get("ticket_id")
                ],
                "status": "open",
                "resolved_at": None,
                "resolution_note": None,
            }

            # Store in MongoDB
            await alerts_collection.insert_one(dict(alert))

            # Broadcast to all dashboards
            await notification_service.notify_root_cause_alert({
                **alert,
                "timestamp": alert["timestamp"].isoformat(),
            })

            new_alerts.append(alert)
            logger.info(
                f"Root cause alert created: {alert['alert_id']} "
                f"| Severity: {severity} | Hypothesis: {hypothesis[:80]}"
            )

        return new_alerts


# Module-level singleton
root_cause_service = RootCauseService()
