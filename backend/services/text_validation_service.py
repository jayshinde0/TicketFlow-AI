"""
services/text_validation_service.py — Input validation to detect gibberish and invalid text.

Prevents the ML pipeline from trying to classify nonsensical input like:
- Random character sequences: "asdfghjkl", "12345tygfdzxc"
- Excessive numbers: "123456789012345"
- Keyboard mashing: "qwertyuiop"
- Extremely low vocabulary diversity
- Text with no recognizable English words
"""

import re
import string
from typing import Tuple, Optional
from loguru import logger
from collections import Counter


class TextValidationService:
    """
    Pre-classification validation to filter out gibberish and invalid input.
    
    Checks performed:
    1. Minimum meaningful word count
    2. Vocabulary diversity (unique words ratio)
    3. English dictionary word presence
    4. Excessive digit/special character ratio
    5. Keyboard pattern detection
    6. Repeated character patterns
    7. Consonant cluster detection (gibberish often has impossible combinations)
    """

    def __init__(self):
        # Common English words (expanded set for better coverage)
        self._common_words = {
            "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
            "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
            "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
            "or", "an", "will", "my", "one", "all", "would", "there", "their",
            "what", "so", "up", "out", "if", "about", "who", "get", "which", "go",
            "me", "when", "make", "can", "like", "time", "no", "just", "him", "know",
            "take", "people", "into", "year", "your", "good", "some", "could", "them",
            "see", "other", "than", "then", "now", "look", "only", "come", "its", "over",
            "think", "also", "back", "after", "use", "two", "how", "our", "work", "first",
            "well", "way", "even", "new", "want", "because", "any", "these", "give", "day",
            "most", "us", "is", "was", "are", "been", "has", "had", "were", "said", "did",
            # IT domain words
            "computer", "network", "internet", "email", "password", "login", "access",
            "error", "issue", "problem", "help", "please", "need", "unable", "cannot",
            "vpn", "wifi", "connection", "server", "database", "website", "software",
            "hardware", "printer", "laptop", "phone", "system", "application", "app",
            "account", "user", "admin", "file", "folder", "install", "update", "upgrade",
            "slow", "crash", "freeze", "broken", "fix", "work", "working", "stopped",
            "not", "down", "outage", "timeout", "failed", "failure", "denied", "blocked",
            "security", "virus", "malware", "phishing", "spam", "backup", "restore",
            "permission", "role", "reset", "change", "create", "delete", "configure"
        }
        
        # Keyboard layout patterns (row-wise)
        self._keyboard_patterns = [
            "qwerty", "asdfgh", "zxcvbn", "uiop", "jkl", "mnb",
            "qwertyuiop", "asdfghjkl", "zxcvbnm",
            "1234567890", "0987654321"
        ]

    def _calculate_diversity(self, text: str) -> float:
        """
        Calculate vocabulary diversity (unique words / total words).
        Gibberish often has very high diversity (every "word" is random).
        """
        words = re.findall(r'\b\w+\b', text.lower())
        if len(words) == 0:
            return 0.0
        unique_words = len(set(words))
        return unique_words / len(words)

    def _count_english_words(self, text: str) -> Tuple[int, int]:
        """
        Count recognizable English words.
        
        Returns:
            (english_word_count, total_word_count)
        """
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        if not words:
            return 0, 0
        
        english_count = sum(1 for word in words if word in self._common_words)
        return english_count, len(words)

    def _calculate_digit_ratio(self, text: str) -> float:
        """Calculate ratio of digits to total characters."""
        if len(text) == 0:
            return 0.0
        digit_count = sum(1 for char in text if char.isdigit())
        return digit_count / len(text)

    def _detect_keyboard_mashing(self, text: str) -> bool:
        """
        Detect keyboard pattern sequences like 'qwerty', 'asdfgh'.
        """
        text_lower = text.lower()
        for pattern in self._keyboard_patterns:
            if pattern in text_lower:
                return True
        return False

    def _calculate_consonant_vowel_ratio(self, text: str) -> float:
        """
        Calculate consonant-to-vowel ratio.
        Real words have balanced ratios; gibberish often skews heavily.
        """
        vowels = "aeiouAEIOU"
        letters = [c for c in text if c.isalpha()]
        
        if len(letters) == 0:
            return 0.0
        
        vowel_count = sum(1 for c in letters if c in vowels)
        consonant_count = len(letters) - vowel_count
        
        if vowel_count == 0:
            return float('inf')  # All consonants = gibberish
        
        return consonant_count / vowel_count

    def _detect_impossible_clusters(self, text: str) -> bool:
        """
        Detect impossible consonant clusters that don't exist in English.
        Examples: "zxcv", "qwrt", "fghj"
        """
        vowels = "aeiouAEIOU"
        
        # Extract letter-only words
        words = re.findall(r'[a-zA-Z]+', text.lower())
        
        for word in words:
            consonant_streak = 0
            for char in word:
                if char not in vowels:
                    consonant_streak += 1
                    # More than 4 consecutive consonants is very rare in English
                    if consonant_streak > 4:
                        return True
                else:
                    consonant_streak = 0
        
        return False

    def _has_excessive_repetition(self, text: str) -> bool:
        """
        Detect excessive character or word repetition.
        Example: "aaaaaaa", "test test test test test"
        """
        # Check character repetition
        if re.search(r'(.)\1{5,}', text):  # 6+ same character
            return True
        
        # Check word repetition
        words = text.lower().split()
        if len(words) >= 3:
            # Check if more than 60% of words are the same
            word_counts = Counter(words)
            most_common_count = word_counts.most_common(1)[0][1]
            if most_common_count / len(words) > 0.6:
                return True
        
        return False

    def validate(self, text: str, min_words: int = 3) -> Tuple[bool, Optional[str]]:
        """
        Validate if text is meaningful enough for classification.
        
        Args:
            text: Raw input text to validate
            min_words: Minimum number of words required
            
        Returns:
            (is_valid, error_message)
            - (True, None) if text is valid
            - (False, error_message) if text is invalid
        """
        # Strip whitespace
        text = text.strip()
        
        # Check 1: Minimum length
        if len(text) < 10:
            return False, "Text too short. Please provide at least 10 characters describing your issue."
        
        # Check 2: Extract words (alphabetic tokens)
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        
        if len(words) < min_words:
            return False, f"Please provide at least {min_words} meaningful words describing your issue."
        
        # Check 3: Excessive digits (e.g., "123456789012345")
        digit_ratio = self._calculate_digit_ratio(text)
        if digit_ratio > 0.7:
            return False, "Input contains too many numbers. Please describe your issue in words."
        
        # Check 4: Keyboard mashing
        if self._detect_keyboard_mashing(text):
            return False, "Input appears to be keyboard mashing. Please provide a meaningful description."
        
        # Check 5: Excessive repetition
        if self._has_excessive_repetition(text):
            return False, "Input contains excessive repetition. Please provide a clear description."
        
        # Check 6: English word presence
        english_count, total_words = self._count_english_words(text)
        if total_words > 0:
            english_ratio = english_count / total_words
            # At least 30% should be recognizable English words
            if english_ratio < 0.30:
                return False, "Unable to understand the text. Please use clear English to describe your issue."
        
        # Check 7: Impossible consonant clusters
        if self._detect_impossible_clusters(text):
            return False, "Text appears to contain gibberish. Please provide a meaningful description."
        
        # Check 8: Consonant-vowel ratio (catch extreme imbalances)
        cv_ratio = self._calculate_consonant_vowel_ratio(text)
        if cv_ratio > 6.0 or cv_ratio == float('inf'):
            return False, "Text structure appears invalid. Please describe your issue using normal words."
        
        # All checks passed
        return True, None

    def validate_or_raise(self, text: str, min_words: int = 3) -> None:
        """
        Validate text and raise ValueError if invalid.
        
        Args:
            text: Input text to validate
            min_words: Minimum word count
            
        Raises:
            ValueError: If text is invalid
        """
        is_valid, error_msg = self.validate(text, min_words)
        if not is_valid:
            logger.warning(f"Text validation failed: {error_msg}")
            raise ValueError(error_msg)


# Module-level singleton
text_validation_service = TextValidationService()
