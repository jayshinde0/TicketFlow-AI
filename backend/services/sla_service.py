"""
services/sla_service.py — SLA breach prediction and deadline tracking.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
from loguru import logger

from core.config import settings
from ml.models.sla_predictor import SLAPredictor, get_sla_minutes


class SLAService:
    """
    Handles SLA breach prediction and real-time SLA tracking.

    - predict_breach_probability(): uses ML model to predict if ticket will breach
    - get_sla_deadline(): returns datetime of SLA deadline
    - get_minutes_remaining(): live countdown calculation
    - is_breached(): check if SLA has already been breached
    """

    def __init__(self):
        self._sla_predictor = None
        self._loaded = False

    def _get_predictor(self) -> Optional[SLAPredictor]:
        """Lazy-load SLA predictor."""
        if not self._loaded:
            try:
                self._sla_predictor = SLAPredictor.load()
                logger.info("SLAPredictor loaded.")
            except FileNotFoundError:
                logger.warning(
                    "SLA model not found. Run ml/train.py. Using heuristic fallback."
                )
            self._loaded = True
        return self._sla_predictor

    def predict_breach_probability(
        self,
        category: str,
        priority: str,
        user_tier: str,
        submission_hour: int,
        submission_day: int,
        word_count: int,
        urgency_keyword_count: int,
        sentiment_score: float,
        current_queue_length: int = 5,
        similar_ticket_avg_hours: float = 2.0,
    ) -> float:
        """
        Predict SLA breach probability using the ML model.

        Returns:
            Float 0.0-1.0 (probability of breach).
        """
        predictor = self._get_predictor()

        ticket_features = {
            "category": category,
            "priority": priority,
            "user_tier": user_tier,
            "submission_hour": submission_hour,
            "submission_day_of_week": submission_day,
            "word_count": word_count,
            "urgency_keyword_count": urgency_keyword_count,
            "sentiment_score": sentiment_score,
            "current_queue_length": current_queue_length,
            "similar_ticket_avg_resolution_hours": similar_ticket_avg_hours,
        }

        if predictor:
            return predictor.predict_breach_probability(ticket_features)

        # Heuristic fallback when model not available
        risk_map = {"Critical": 0.80, "High": 0.50, "Medium": 0.25, "Low": 0.10}
        base = risk_map.get(priority, 0.30)
        if category in ("Security", "Database"):
            base = min(base + 0.30, 0.95)
        if submission_hour < 8 or submission_hour >= 18:
            base = min(base + 0.10, 0.95)
        return round(base, 4)

    async def predict_async(self, **kwargs) -> float:
        """Async wrapper for predict_breach_probability."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.predict_breach_probability(**kwargs)
        )

    def get_sla_deadline(
        self,
        category: str,
        priority: str,
        submitted_at: datetime,
    ) -> datetime:
        """
        Calculate the SLA deadline datetime.

        Args:
            category: Ticket domain.
            priority: Ticket priority.
            submitted_at: Ticket creation time (UTC).

        Returns:
            datetime of SLA deadline (UTC).
        """
        sla_minutes = get_sla_minutes(category, priority)
        return submitted_at + timedelta(minutes=sla_minutes)

    def get_minutes_remaining(
        self,
        sla_deadline: datetime,
        now: Optional[datetime] = None,
    ) -> float:
        """
        Calculate minutes remaining until SLA breach.
        Negative values indicate breach has already occurred.
        """
        if now is None:
            now = datetime.now(timezone.utc)

        # Ensure both are timezone-aware
        if sla_deadline.tzinfo is None:
            sla_deadline = sla_deadline.replace(tzinfo=timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        delta = sla_deadline - now
        return delta.total_seconds() / 60.0

    def is_breached(
        self,
        category: str,
        priority: str,
        submitted_at: datetime,
        now: Optional[datetime] = None,
    ) -> bool:
        """Check if the SLA deadline has passed."""
        deadline = self.get_sla_deadline(category, priority, submitted_at)
        mins = self.get_minutes_remaining(deadline, now)
        return mins < 0

    def get_sla_info(
        self,
        category: str,
        priority: str,
        submitted_at: datetime,
    ) -> dict:
        """
        Return full SLA info dict for a ticket.

        Returns:
            {
                sla_minutes: int,
                deadline: datetime,
                minutes_remaining: float,
                is_breached: bool,
                urgency_level: "critical"|"warning"|"ok"
            }
        """
        sla_minutes = get_sla_minutes(category, priority)
        deadline = self.get_sla_deadline(category, priority, submitted_at)
        mins_remaining = self.get_minutes_remaining(deadline)
        breached = mins_remaining < 0

        # Urgency level for frontend color coding
        if breached:
            urgency = "critical"
        elif mins_remaining < sla_minutes * 0.20:  # < 20% time left
            urgency = "warning"
        else:
            urgency = "ok"

        return {
            "sla_minutes": sla_minutes,
            "deadline": deadline.isoformat(),
            "minutes_remaining": round(mins_remaining, 1),
            "is_breached": breached,
            "urgency_level": urgency,
        }


# Module-level singleton
sla_service = SLAService()
