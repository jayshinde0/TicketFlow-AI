"""
Enhanced 3-tier hybrid classifier: ML → Keywords → LLM
Uses Ollama for final arbitration on uncertain cases.
"""
import asyncio
from loguru import logger
from services.classifier_service import classifier_service
from services.llm_provider_factory import llm_provider as ollama_provider
from core.config import settings
from ml.data_loader import ALL_CATEGORIES


class EnhancedHybridClassifier:
    """
    3-tier classification:
    1. ML (fast, 70% accurate)
    2. Keywords (medium, 80% accurate)
    3. LLM (slow, 95% accurate)
    """
    
    STRONG_CATEGORIES = {
        "Network", "Auth", "Security", "Email", "Hardware", "Access", "Database"
    }
    
    WEAK_CATEGORIES = {
        "Software", "ServiceRequest", "Billing"
    }
    
    async def classify(
        self,
        cleaned_text: str,
        user_tier: str = "Standard",
        submission_hour: int = 0,
        word_count: int = 0,
        urgency_keyword_count: int = 0,
        sentiment_score: float = 0.5,
    ) -> dict:
        """
        Enhanced classification with 3 tiers.
        Returns: {category, model_confidence, method, ...}
        """
        
        # ─── TIER 1: ML Classification (Fast) ────────────────────────
        logger.info("TIER 1: ML Classification")
        ml_result = classifier_service.classify(
            cleaned_text=cleaned_text,
            user_tier=user_tier,
            submission_hour=submission_hour,
            word_count=word_count,
            urgency_keyword_count=urgency_keyword_count,
            sentiment_score=sentiment_score,
        )
        
        ml_category = ml_result["category"]
        ml_confidence = ml_result["model_confidence"]
        
        logger.debug(f"  ML: {ml_category} ({ml_confidence:.2f})")
        
        # If ML is very confident, use it
        if ml_confidence >= 0.75:
            logger.info(f"✓ TIER 1 ACCEPT: {ml_category} ({ml_confidence:.2f})")
            ml_result["classification_method"] = "ml_high_confidence"
            return ml_result
        
        # ─── TIER 2: Keyword Classification (Medium) ───────────────────
        logger.info("TIER 2: Keyword Classification")
        keyword_result = self._keyword_classify(cleaned_text)
        keyword_category = keyword_result["category"]
        keyword_score = keyword_result["score"]
        
        logger.debug(f"  Keywords: {keyword_category} ({keyword_score:.2f})")
        
        # If keywords are strong, use them
        if keyword_score >= 0.70:
            logger.info(f"✓ TIER 2 ACCEPT: {keyword_category} ({keyword_score:.2f})")
            ml_result["category"] = keyword_category
            ml_result["model_confidence"] = keyword_score
            ml_result["classification_method"] = "keywords_high_match"
            return ml_result
        
        # ─── TIER 3: LLM Classification (Accurate but Slow) ──────────────
        logger.warning("TIER 3: LLM Classification (uncertain case)")
        
        try:
            llm_result = await asyncio.wait_for(
                ollama_provider.classify_zero_shot(cleaned_text, ALL_CATEGORIES),
                timeout=20.0,
            )
            llm_category = llm_result.get("category", ml_category)
            llm_confidence = llm_result.get("confidence", 0.5)
            
            logger.info(
                f"  LLM: {llm_category} ({llm_confidence:.2f}) "
                f"(reasoning: {llm_result.get('reasoning', 'N/A')[:100]}...)"
            )
            
            # LLM is the tiebreaker - always trust it for uncertain cases
            if llm_confidence >= 0.65:
                logger.info(f"✓ TIER 3 ACCEPT: {llm_category} ({llm_confidence:.2f})")
                ml_result["category"] = llm_category
                ml_result["model_confidence"] = llm_confidence
                ml_result["classification_method"] = "llm_zero_shot"
                ml_result["llm_reasoning"] = llm_result.get("reasoning", "")
                return ml_result
        
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"  LLM failed ({str(e)[:50]}), falling back to keywords")
        
        # ─── FALLBACK: Use best between ML and Keywords ────────────────
        if keyword_score > ml_confidence:
            logger.warning(f"Fallback: Keywords ({keyword_score:.2f}) > ML ({ml_confidence:.2f})")
            ml_result["category"] = keyword_category
            ml_result["model_confidence"] = keyword_score
            ml_result["classification_method"] = "keywords_fallback"
        else:
            logger.warning(f"Fallback: Using ML ({ml_confidence:.2f})")
            ml_result["classification_method"] = "ml_fallback"
        
        return ml_result
    
    def _keyword_classify(self, text: str) -> dict:
        """Keyword-based classification with scoring"""
        text_lower = text.lower()
        scores = {}
        
        for category, keywords in settings.DOMAIN_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw.lower() in text_lower)
            scores[category] = matches
        
        max_score = max(scores.values()) if scores else 0
        
        if max_score == 0:
            return {"category": "Software", "score": 0.0}
        
        best_category = max(scores, key=scores.get)
        # Normalize score to 0-1 range (assume max 5 matches = 1.0)
        confidence = min(max_score / 5.0, 1.0)
        
        logger.debug(f"Keyword scores: {scores}, best: {best_category} ({confidence:.2f})")
        
        return {"category": best_category, "score": confidence}


enhanced_hybrid_classifier = EnhancedHybridClassifier()