"""
utils/text_cleaner.py — Low-level text cleaning utilities.
Used by NLP service and ML training pipeline.
"""

import re
import unicodedata
from typing import List

# Common English contractions to expand before cleaning
CONTRACTIONS: dict = {
    "can't": "cannot",
    "won't": "will not",
    "n't": " not",
    "'re": " are",
    "'ve": " have",
    "'ll": " will",
    "'d": " would",
    "'m": " am",
    "it's": "it is",
    "that's": "that is",
    "i'm": "i am",
    "you're": "you are",
    "he's": "he is",
    "she's": "she is",
    "we're": "we are",
    "they're": "they are",
    "i've": "i have",
    "you've": "you have",
    "we've": "we have",
    "i'll": "i will",
    "you'll": "you will",
    "they'll": "they will",
    "i'd": "i would",
    "you'd": "you would",
    "isn't": "is not",
    "aren't": "are not",
    "wasn't": "was not",
    "weren't": "were not",
    "hasn't": "has not",
    "haven't": "have not",
    "hadn't": "had not",
    "doesn't": "does not",
    "don't": "do not",
    "didn't": "did not",
}

# Regex for common noise patterns
RE_URL = re.compile(r"https?://\S+|www\.\S+")
RE_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[a-z]{2,}\b", re.IGNORECASE)
RE_IP = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
RE_TICKET_ID = re.compile(r"\bTKT-\d+\b", re.IGNORECASE)
RE_MULTIPLE_SPACES = re.compile(r"\s{2,}")
RE_NON_ASCII = re.compile(r"[^\x00-\x7F]+")
RE_SPECIAL_CHARS = re.compile(r"[^a-zA-Z0-9\s.,!?'-]")
RE_REPEATED_CHARS = re.compile(r"(.)\1{3,}")  # aaaa → a


def expand_contractions(text: str) -> str:
    """Expand English contractions: can't → cannot, won't → will not."""
    # Case-insensitive replacement
    pattern = re.compile(
        "(%s)" % "|".join(re.escape(k) for k in CONTRACTIONS.keys()), re.IGNORECASE
    )

    def replace(match):
        return CONTRACTIONS[match.group(0).lower()]

    return pattern.sub(replace, text)


def normalize_unicode(text: str) -> str:
    """Normalize unicode characters to ASCII equivalents where possible."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def remove_urls(text: str, replacement: str = " URL ") -> str:
    """Replace URLs with placeholder token."""
    return RE_URL.sub(replacement, text)


def remove_emails(text: str, replacement: str = " EMAIL ") -> str:
    """Replace email addresses with placeholder token."""
    return RE_EMAIL.sub(replacement, text)


def remove_ip_addresses(text: str, replacement: str = " IP ") -> str:
    """Replace IP addresses with placeholder."""
    return RE_IP.sub(replacement, text)


def remove_ticket_ids(text: str) -> str:
    """Remove ticket ID references to prevent data leakage in ML."""
    return RE_TICKET_ID.sub("TICKET_REF", text)


def fix_repeated_characters(text: str) -> str:
    """Reduce excessive character repetition: soooo → so, !!! → !."""
    return RE_REPEATED_CHARS.sub(r"\1\1", text)


def basic_clean(text: str) -> str:
    """
    Apply a standard cleaning pipeline suitable for TF-IDF vectorization.
    Preserves case — caller should .lower() if needed.

    Steps:
    1. Normalize unicode
    2. Expand contractions
    3. Remove URLs, emails, IPs
    4. Fix repeated characters
    5. Remove excessive special characters
    6. Collapse multiple whitespace
    """
    text = normalize_unicode(text)
    text = expand_contractions(text)
    text = remove_urls(text)
    text = remove_emails(text)
    text = remove_ip_addresses(text)
    text = remove_ticket_ids(text)
    text = fix_repeated_characters(text)
    text = RE_SPECIAL_CHARS.sub(" ", text)
    text = RE_MULTIPLE_SPACES.sub(" ", text)
    return text.strip()


def count_urgency_keywords(text: str) -> int:
    """
    Count presence of urgency-signaling words.
    Used as an ML feature alongside TF-IDF.
    """
    urgency_words = {
        "urgent",
        "asap",
        "immediately",
        "critical",
        "emergency",
        "broken",
        "down",
        "outage",
        "cannot",
        "unable",
        "failed",
        "error",
        "crash",
        "blocked",
        "help",
        "please",
        "important",
        "serious",
        "severe",
        "priority",
        "escalate",
        "stuck",
    }
    text_lower = text.lower()
    return sum(1 for word in urgency_words if word in text_lower)


def count_all_caps_words(text: str) -> int:
    """Count words in ALL CAPS (signals frustration/urgency)."""
    return sum(1 for word in text.split() if word.isupper() and len(word) > 1)


def extract_text_features(text: str) -> dict:
    """
    Extract scalar numeric features from raw ticket text.
    These supplement TF-IDF in the Random Forest classifier.

    Returns:
        Dict with keys: word_count, char_count, question_mark_count,
        exclamation_count, all_caps_word_count, urgency_keyword_count,
        avg_word_length, sentence_count
    """
    words = text.split()
    sentences = re.split(r"[.!?]+", text)
    sentences = [s for s in sentences if s.strip()]

    return {
        "word_count": len(words),
        "char_count": len(text),
        "question_mark_count": text.count("?"),
        "exclamation_count": text.count("!"),
        "all_caps_word_count": count_all_caps_words(text),
        "urgency_keyword_count": count_urgency_keywords(text),
        "avg_word_length": (sum(len(w) for w in words) / len(words) if words else 0.0),
        "sentence_count": len(sentences),
    }
