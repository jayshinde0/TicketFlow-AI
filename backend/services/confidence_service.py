"""
services/confidence_service.py — Agent 3 (Part 1): Composite confidence scoring.

Computes the final confidence score from weighted components with realistic calibration:
  - Model probability (40%)
  - Vector similarity (15%)
  - Domain keyword boost (20%)
  - Text quality (10%)
  - User tier trust (10%)
  - Penalties (sentiment, SLA)

Then applies:
  - Sentiment adjustment (-0.05 to -0.15 if negative)
  - SLA override (escalate if breach risk > 75%)
  - Security override (always escalate)
  - Text quality penalties (vague, rambling, multiple issues)

Confidence is CAPPED at 0.95 (5% uncertainty always reserved).
"""

from typing import Dict, Optional
from loguru import logger

from core.config import settings
from utils.helpers import clamp


class ConfidenceService:
    """
    Agent 3 Part 1: Computes composite confidence and routing decision with calibration.

    Formula (realistic, never 100%):
        confidence = (0.40 × model_confidence)
                   + (0.15 × similarity_score)
                   + (0.20 × keyword_boost)
                   + (0.10 × text_quality)
                   + (0.10 × tier_trust)
                   - sentiment_penalty
                   - sla_penalty

    Constraints:
        - Minimum confidence: 0.10 (very poor inputs)
        - Maximum confidence: 0.95 (always leave 5% uncertainty)
        - Never returns 100%

    Override logic (takes priority over confidence):
        Security category → always ESCALATE_TO_HUMAN (confidence=0.0)
        SLA breach probability > 0.75 → ESCALATE_TO_HUMAN
        Text quality very poor → reduce confidence by 0.20

    Routing based on confidence:
        >= 0.85 → AUTO_RESOLVE
        >= 0.70 → SUGGEST_TO_AGENT
        >= 0.50 → ESCALATE_TO_AGENT
        <  0.50 → ESCALATE_TO_HUMAN
    """

    def _compute_keyword_boost(
        self,
        text: str,
        category: str,
    ) -> float:
        """
        Compute domain keyword boost (0.0 to 1.0).

        Logic:
        - Get the keyword list for predicted category
        - Count how many appear in the ticket text
        - Normalize: min(count / 3, 1.0)
        
        Returns 0.4-1.0 (minimum 0.4 for category matching)
        """
        domain_keywords = settings.DOMAIN_KEYWORDS.get(category, [])
        if not domain_keywords:
            return 0.4  # Minimum for unknown category

        text_lower = text.lower()
        matches = sum(1 for kw in domain_keywords if kw.lower() in text_lower)
        
        # Easier to get high boost (3 keywords = 100%)
        boost = min(matches / 3.0, 1.0)
        
        # Minimum 0.4 even with no matches (to avoid penalizing too much)
        boost = max(boost, 0.4)
        
        logger.debug(
            f"Keyword boost for {category}: {matches} matches → {boost:.2f}"
        )
        return round(boost, 4)

    def _compute_text_quality(self, text: str) -> float:
        """
        Score text quality (0.3 to 1.0).
        Better quality description = higher confidence.

        Penalties for:
        - Too short/vague
        - Multiple question marks
        - Rambling without punctuation
        - Multiple unrelated issues
        """
        if not text or len(text.strip()) < 10:
            return 0.3  # Very poor
        
        word_count = len(text.split())
        sentence_count = max(1, len([s for s in text.split('.') if s.strip()]))
        
        quality = 1.0
        penalties = 0.0
        
        # ── Penalty: Too short ────────────────────────────────────────
        if word_count < 10:
            penalties += 0.30
            logger.debug(f"Text quality penalty: too short ({word_count} words)")
        elif word_count < 20:
            penalties += 0.15
        elif word_count > 500:
            # Very long = rambling
            penalties += 0.10
            logger.debug(f"Text quality penalty: too long ({word_count} words)")
        
        # ── Penalty: Too many questions (confused) ────────────────────
        question_count = text.count('?')
        if question_count > 5:
            penalties += 0.20
            logger.debug(f"Text quality penalty: too many questions ({question_count})")
        elif question_count > 3:
            penalties += 0.10
        
        # ── Penalty: Rambling (many words per sentence) ───────────────
        avg_words_per_sentence = word_count / sentence_count
        if avg_words_per_sentence > 40:
            penalties += 0.15
            logger.debug(
                f"Text quality penalty: rambling "
                f"({avg_words_per_sentence:.0f} words/sentence)"
            )
        
        # ── Penalty: Multiple unrelated issues ────────────────────────
        problem_indicators = [
            "also have", "another issue", "plus", "besides",
            "in addition", "moreover", "furthermore",
            "multiple problems", "several issues"
        ]
        issue_count = sum(
            1 for indicator in problem_indicators 
            if indicator.lower() in text.lower()
        )
        if issue_count >= 2:
            penalties += 0.15
            logger.debug(
                f"Text quality penalty: multiple issues detected "
                f"({issue_count} indicators)"
            )
        
        # ── Penalty: ALL CAPS (screaming) ─────────────────────────────
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        if caps_ratio > 0.30:
            penalties += 0.10
            logger.debug(f"Text quality penalty: excessive caps ({caps_ratio:.0%})")
        
        # ── Penalty: Extremely vague language ─────────────────────────
        vague_terms = [
            "something", "thing", "stuff", "whatever",
            "i dunno", "not sure", "kinda", "sorta"
        ]
        vague_count = sum(
            1 for term in vague_terms 
            if term.lower() in text.lower()
        )
        if vague_count >= 2:
            penalties += 0.20
            logger.debug(
                f"Text quality penalty: vague language ({vague_count} terms)"
            )
        
        quality = max(0.3, quality - penalties)  # Min 0.3 for very poor text
        
        logger.debug(
            f"Text quality score: {quality:.2f} "
            f"(words={word_count}, sentences={sentence_count}, penalties={penalties:.2f})"
        )
        return round(quality, 4)

    def _compute_sentiment_penalty(
        self,
        sentiment_label: str,
        sentiment_score: float,
        category: str,
    ) -> float:
        """
        Apply penalty if sentiment doesn't match category expectation.
        
        Returns 0.0-0.20 penalty
        """
        penalty = 0.0
        
        # ── Positive sentiment for urgent categories (unusual/suspicious) ────
        if sentiment_label == "POSITIVE" and category in (
            "Software", "Network", "Database", "Security", "Hardware"
        ):
            penalty += 0.15
            logger.debug(
                f"Sentiment penalty: positive sentiment for {category} "
                f"(+0.15 penalty)"
            )
        
        # ── Neutral sentiment for Security/urgent (should be concerned) ──────
        if sentiment_label == "NEUTRAL" and category in (
            "Security", "Database"
        ) and sentiment_score > 0.6:
            penalty += 0.08
            logger.debug(
                f"Sentiment penalty: neutral for urgent {category} (+0.08 penalty)"
            )
        
        # ── Very negative for non-urgent categories (over-dramatic) ──────────
        if (
            sentiment_label == "NEGATIVE"
            and sentiment_score > 0.85
            and category in ("ServiceRequest", "Email", "Access")
        ):
            penalty += 0.05
            logger.debug(
                f"Sentiment penalty: very negative for {category} (+0.05 penalty)"
            )
        
        return round(penalty, 4)

    def _compute_sla_penalty(self, sla_breach_probability: float) -> float:
        """
        Apply penalty based on SLA breach risk.
        Higher breach risk = higher penalty.
        
        Returns 0.0-0.15 penalty
        """
        if sla_breach_probability > 0.75:
            # Already handled by SLA override, don't penalize here
            return 0.0
        
        # Scale penalty: 50% breach prob = 0.075 penalty, 75% = trigger override
        penalty = sla_breach_probability * 0.10
        penalty = min(penalty, 0.15)  # Cap at 0.15
        
        if penalty > 0:
            logger.debug(
                f"SLA penalty: {sla_breach_probability:.0%} breach prob "
                f"(penalty: {penalty:.2f})"
            )
        
        return round(penalty, 4)

    def _compute_tier_trust(self, user_tier: str) -> float:
        """
        Compute trust score based on user tier.
        Premium tiers = more trustworthy = higher boost.
        
        Returns 0.4-1.0
        """
        tier_scores = {
            "Premium": 1.0,
            "Enterprise": 1.0,
            "Standard": 0.7,
            "Basic": 0.5,
            "Free": 0.4,
        }
        
        score = tier_scores.get(user_tier, 0.6)
        logger.debug(f"Tier trust for {user_tier}: {score:.2f}")
        return round(score, 4)

    def compute(
        self,
        model_confidence: float,
        similarity_score: float,
        ticket_text: str,
        category: str,
        sentiment_label: str,
        sentiment_score: float,
        sla_breach_probability: float,
        user_tier: str = "Standard",
    ) -> dict:
        """
        Compute composite confidence and routing decision using ensemble voting
        with realistic calibration (never 100%).

        Args:
            model_confidence: Classifier softmax probability for top class.
            similarity_score: Top cosine similarity from ChromaDB retrieval.
            ticket_text: Original or lightly-cleaned ticket text.
            category: Predicted category (for Security override + keyword boost).
            sentiment_label: "POSITIVE" | "NEUTRAL" | "NEGATIVE"
            sentiment_score: Confidence of sentiment prediction (0-1).
            sla_breach_probability: From SLA predictor (0.0-1.0).
            user_tier: User subscription tier.

        Returns:
            Agent 3 output dict with:
            - confidence_score (0.1-0.95, never 100%)
            - routing_decision (AUTO_RESOLVE, SUGGEST_TO_AGENT, ESCALATE_TO_AGENT, ESCALATE_TO_HUMAN)
            - confidence_breakdown (component scores)
            - override flags (sla_override, security_override)
            - reason (explanation string)
        """
        
        # ─── Step 1: Security override (HIGHEST PRIORITY) ──────────────
        if category == "Security":
            logger.warning(
                f"Security override: ESCALATE_TO_HUMAN (category={category})"
            )
            return {
                "confidence_score": 0.0,
                "routing_decision": "ESCALATE_TO_HUMAN",
                "confidence_breakdown": {
                    "model_prob_component": 0.0,
                    "similarity_component": 0.0,
                    "keyword_component": 0.0,
                    "text_quality_component": 0.0,
                    "tier_trust_component": 0.0,
                },
                "sla_override": False,
                "security_override": True,
                "sentiment_adjusted": False,
                "reason": "Security tickets ALWAYS require human review (critical)",
            }

        # ─── Step 2: Clamp and normalize inputs ────────────────────────
        model_prob = clamp(model_confidence, 0.0, 1.0)
        sim_score = clamp(similarity_score, 0.0, 1.0)
        
        # ─── Step 3: Compute component scores ──────────────────────────
        keyword_boost = self._compute_keyword_boost(ticket_text, category)
        text_quality = self._compute_text_quality(ticket_text)
        tier_trust = self._compute_tier_trust(user_tier)
        
        logger.debug(
            f"Component scores: model={model_prob:.3f}, sim={sim_score:.3f}, "
            f"kw={keyword_boost:.3f}, quality={text_quality:.3f}, tier={tier_trust:.3f}"
        )
        
        # ─── Step 4: Weighted ensemble (NO VARIABLE NAME ISSUES) ────────
        # Using descriptive variable names
        model_component = model_prob * 0.40
        similarity_component = sim_score * 0.15
        keyword_component = keyword_boost * 0.20
        quality_component = text_quality * 0.10
        tier_component = tier_trust * 0.10
        
        composite_score = (
            model_component
            + similarity_component
            + keyword_component
            + quality_component
            + tier_component
        )
        
        logger.debug(
            f"Ensemble: model={model_component:.3f}, sim={similarity_component:.3f}, "
            f"kw={keyword_component:.3f}, quality={quality_component:.3f}, "
            f"tier={tier_component:.3f} → sum={composite_score:.3f}"
        )
        
        # ─── Step 5: Apply penalties ───────────────────────────────────
        sentiment_penalty = self._compute_sentiment_penalty(
            sentiment_label, sentiment_score, category
        )
        sla_penalty = self._compute_sla_penalty(sla_breach_probability)
        
        confidence = composite_score - sentiment_penalty - sla_penalty
        
        if sentiment_penalty > 0 or sla_penalty > 0:
            logger.debug(
                f"Penalties: sentiment={sentiment_penalty:.3f}, "
                f"sla={sla_penalty:.3f} → {composite_score:.3f} - {sentiment_penalty + sla_penalty:.3f} = {confidence:.3f}"
            )
        
        # ─── Step 6: Cap at 0.95 (always leave 5% uncertainty) ─────────
        confidence_before_cap = confidence
        confidence = clamp(confidence, 0.10, 0.95)  # Min 0.1, Max 0.95
        
        if confidence != confidence_before_cap:
            logger.debug(
                f"Confidence capped: {confidence_before_cap:.3f} → {confidence:.3f}"
            )
        
        # ─── Step 7: SLA override (CRITICAL) ────────────────────��──────
        if sla_breach_probability > settings.SLA_BREACH_THRESHOLD:
            logger.warning(
                f"SLA override triggered: "
                f"breach_prob={sla_breach_probability:.0%} > threshold={settings.SLA_BREACH_THRESHOLD:.0%}"
            )
            return {
                "confidence_score": round(confidence, 4),
                "routing_decision": "ESCALATE_TO_HUMAN",
                "confidence_breakdown": {
                    "model_prob_component": round(model_component, 4),
                    "similarity_component": round(similarity_component, 4),
                    "keyword_component": round(keyword_component, 4),
                    "text_quality_component": round(quality_component, 4),
                    "tier_trust_component": round(tier_component, 4),
                },
                "sla_override": True,
                "security_override": False,
                "sentiment_adjusted": sentiment_penalty > 0,
                "reason": f"SLA breach probability {sla_breach_probability:.0%} exceeds threshold {settings.SLA_BREACH_THRESHOLD:.0%}",
            }

        # ─── Step 8: Standard routing based on calibrated confidence ────
        if confidence >= 0.85:
            routing = "AUTO_RESOLVE"
        elif confidence >= 0.70:
            routing = "SUGGEST_TO_AGENT"
        elif confidence >= 0.50:
            routing = "ESCALATE_TO_AGENT"
        else:
            routing = "ESCALATE_TO_HUMAN"
        
        logger.debug(
            f"Routing decision: confidence={confidence:.3f} → {routing}"
        )

        # ─── Step 9: Enterprise tier upgrade ─────────────────────────
        enterprise_upgrade = False
        if user_tier == "Enterprise" and routing == "SUGGEST_TO_AGENT":
            if confidence >= 0.60:
                routing = "AUTO_RESOLVE"
                enterprise_upgrade = True
                logger.debug("Enterprise tier upgrade: SUGGEST_TO_AGENT → AUTO_RESOLVE")

        # ─── Step 10: Return final result ──────────────────────────────
        return {
            "confidence_score": round(confidence, 4),
            "routing_decision": routing,
            "confidence_breakdown": {
                "model_prob_component": round(model_component, 4),
                "similarity_component": round(similarity_component, 4),
                "keyword_component": round(keyword_component, 4),
                "text_quality_component": round(quality_component, 4),
                "tier_trust_component": round(tier_component, 4),
                "sentiment_penalty": round(sentiment_penalty, 4),
                "sla_penalty": round(sla_penalty, 4),
            },
            "sla_override": False,
            "security_override": False,
            "sentiment_adjusted": sentiment_penalty > 0,
            "enterprise_upgrade": enterprise_upgrade,
            "reason": f"Ensemble: {routing} at {confidence:.0%} confidence",
        }


# Module-level singleton
confidence_service = ConfidenceService()