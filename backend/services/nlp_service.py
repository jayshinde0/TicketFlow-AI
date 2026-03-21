"""
services/nlp_service.py — Text preprocessing pipeline using spaCy + NLTK.
Runs on every incoming ticket before the AI pipeline.
"""

import re
import asyncio
from typing import Optional
from loguru import logger
from functools import lru_cache

import nltk
import spacy
from langdetect import detect, LangDetectException

from utils.text_cleaner import basic_clean, extract_text_features


# ─── NLTK downloads (run once on startup) ─────────────────────────────
def ensure_nltk_data():
    """Download required NLTK datasets if not present."""
    for resource in ["stopwords", "punkt", "wordnet"]:
        try:
            nltk.data.find(f"tokenizers/{resource}")
        except LookupError:
            nltk.download(resource, quiet=True)


# ─── spaCy model loader ───────────────────────────────────────────────
_spacy_nlp = None

def get_spacy_nlp():
    """Lazy-load spaCy model (only once per process)."""
    global _spacy_nlp
    if _spacy_nlp is None:
        try:
            _spacy_nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])
            logger.info("spaCy en_core_web_sm model loaded.")
        except OSError:
            logger.warning(
                "spaCy en_core_web_sm not found. "
                "Run: python -m spacy download en_core_web_sm"
            )
            _spacy_nlp = None
    return _spacy_nlp


class NLPService:
    """
    Text preprocessing service for TicketFlow AI.

    Pipeline:
    1. basic_clean (URL/email removal, contraction expansion)
    2. Language detection
    3. spaCy tokenization + lemmatization + stopword removal
    4. Short word filtering (< 2 chars)
    5. Reconstruct cleaned text string
    6. Extract scalar features for ML
    """

    def __init__(self):
        ensure_nltk_data()
        from nltk.corpus import stopwords
        self._stopwords = set(stopwords.words("english"))
        # Add IT-specific stopwords that add noise
        self._stopwords.update({
            "please", "help", "thank", "thanks", "hi", "hello",
            "dear", "regards", "sincerely", "team", "sir", "madam",
        })
        self._nlp = None  # lazy-loaded

    def _get_nlp(self):
        if self._nlp is None:
            self._nlp = get_spacy_nlp()
        return self._nlp

    def detect_language(self, text: str) -> str:
        """
        Detect the language of input text.
        Returns ISO 639-1 code (e.g., 'en', 'fr').
        Defaults to 'en' on detection failure.
        """
        try:
            if len(text.strip()) < 20:
                return "en"
            return detect(text[:500])  # only need first 500 chars
        except LangDetectException:
            return "en"

    def lemmatize_and_clean(self, text: str) -> str:
        """
        Full spaCy preprocessing:
        - Tokenize
        - Lemmatize
        - Remove stopwords and punctuation
        - Filter short tokens

        Falls back to basic_clean if spaCy is unavailable.
        """
        nlp = self._get_nlp()

        if nlp is None:
            # Simple fallback: just lowercase + split + filter stopwords
            tokens = text.lower().split()
            filtered = [
                t for t in tokens
                if t not in self._stopwords and len(t) > 2
            ]
            return " ".join(filtered)

        doc = nlp(text[:5000])  # cap at 5000 chars for spaCy
        tokens = []
        for token in doc:
            # Skip: stopwords, punctuation, spaces, very short tokens
            if (
                token.is_stop
                or token.is_punct
                or token.is_space
                or len(token.text) < 2
                or token.lemma_ in self._stopwords
            ):
                continue
            # Use lemma (lowercase)
            lemma = token.lemma_.lower().strip()
            if lemma and len(lemma) > 1:
                tokens.append(lemma)

        return " ".join(tokens)

    def preprocess(self, raw_text: str) -> dict:
        """
        Full preprocessing pipeline for a ticket text.

        Args:
            raw_text: Original user input.

        Returns:
            Dict with:
                cleaned_text: spaCy-processed string (for ML)
                language: detected ISO 639-1 code
                features: scalar feature dict (word_count, urgency, etc.)
                is_english: bool
        """
        # Step 1: Basic cleaning (URLs, emails, special chars)
        step1 = basic_clean(raw_text)

        # Step 2: Language detection
        language = self.detect_language(step1)

        # Step 3: Extract scalar features from cleaned-but-not-lemmatized text
        # (we want features based on user's original phrasing, not lemmas)
        scalar_features = extract_text_features(step1)

        # Step 4: Lemmatize for ML
        cleaned_text = self.lemmatize_and_clean(step1.lower())

        # Ensure non-empty — fall back to basic clean if spaCy shredded everything
        if len(cleaned_text.split()) < 3:
            cleaned_text = step1.lower()

        return {
            "cleaned_text": cleaned_text,
            "language": language,
            "is_english": language == "en",
            "features": scalar_features,
            "original_cleaned": step1,  # URL-removed but not lemmatized
        }

    async def preprocess_async(self, raw_text: str) -> dict:
        """Async wrapper — runs preprocessing in thread pool to avoid blocking."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.preprocess, raw_text)


# Module-level singleton
nlp_service = NLPService()
