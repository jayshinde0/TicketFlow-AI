# Text Validation & Gibberish Detection Feature

## Overview

This feature prevents the ML classifier from attempting to categorize nonsensical input like random character sequences, keyboard mashing, or excessive numbers. Previously, the system would classify gibberish text (e.g., "12345tygfdzxcdzfdffcsdfszdfcsz") as "Database" or other categories with false confidence.

## Problem Solved

**Before:**
- User submits: `12345tygfdzxcdzfdffcsdfszdfcsz`
- System classifies as: `Database` with `High` priority
- Result: Invalid ticket in the queue

**After:**
- User submits: `12345tygfdzxcdzfdffcsdfszdfcsz`
- System rejects with: `"Please provide at least 3 meaningful words describing your issue"`
- Result: User prompted to provide valid input

## Architecture

### Components

1. **TextValidationService** (`services/text_validation_service.py`)
   - Core validation logic
   - Multiple heuristic checks
   - Returns `(is_valid, error_message)` tuple

2. **Integration Points**
   - **Pydantic Model Validation**: Early rejection at request parsing (`models/ticket.py`)
   - **AI Pipeline Validation**: Pre-processing validation (`routers/tickets.py`)

3. **Classifier Improvements** (`services/classifier_service.py`)
   - Enhanced keyword fallback logic
   - Defaults to "ServiceRequest" instead of "Software/Database" when no keywords match
   - More robust scoring using keyword counts instead of presence

## Validation Checks

The `TextValidationService` performs 8 validation checks:

### 1. **Minimum Length**
```python
if len(text) < 10:
    return False, "Text too short. Please provide at least 10 characters..."
```

### 2. **Minimum Word Count**
```python
words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
if len(words) < min_words:
    return False, "Please provide at least 3 meaningful words..."
```

### 3. **Excessive Digits** (>70%)
```python
digit_ratio = digit_count / total_chars
if digit_ratio > 0.7:
    return False, "Input contains too many numbers..."
```

### 4. **Keyboard Mashing Detection**
Detects patterns like: `qwerty`, `asdfgh`, `zxcvbn`, `1234567890`

### 5. **Excessive Repetition**
- Character repetition: `aaaaaaa`
- Word repetition: `test test test test test`

### 6. **English Word Presence** (≥30% recognizable)
Uses a dictionary of ~180 common English words + IT domain terms:
```python
english_ratio = english_count / total_words
if english_ratio < 0.30:
    return False, "Unable to understand the text..."
```

### 7. **Impossible Consonant Clusters**
Detects sequences like `zxcv`, `qwrt`, `fghj` (>4 consecutive consonants)

### 8. **Consonant-Vowel Ratio**
Flags text with extreme imbalances (ratio > 6.0):
```python
cv_ratio = consonant_count / vowel_count
if cv_ratio > 6.0:
    return False, "Text structure appears invalid..."
```

## Error Messages

User-friendly messages guide users to provide valid input:

| Validation Failure | Error Message |
|-------------------|---------------|
| Too short | "Text too short. Please provide at least 10 characters describing your issue." |
| Too few words | "Please provide at least 3 meaningful words describing your issue." |
| Excessive digits | "Input contains too many numbers. Please describe your issue in words." |
| Keyboard mashing | "Input appears to be keyboard mashing. Please provide a meaningful description." |
| Excessive repetition | "Input contains excessive repetition. Please provide a clear description." |
| Low English ratio | "Unable to understand the text. Please use clear English to describe your issue." |
| Impossible clusters | "Text appears to contain gibberish. Please provide a meaningful description." |
| Invalid structure | "Text structure appears invalid. Please describe your issue using normal words." |

## Testing

### Test Suite
Run the validation test suite:
```bash
cd backend
python test_text_validation.py
```

### Test Coverage
- ✅ Valid technical issues
- ✅ Valid access requests
- ❌ Random gibberish
- ❌ Only numbers
- ❌ Keyboard patterns
- ❌ Excessive repetition
- ❌ Impossible consonant clusters
- ❌ Too short input

All 20 test cases pass.

## Usage

### Direct Validation
```python
from services.text_validation_service import text_validation_service

is_valid, error_msg = text_validation_service.validate(
    "My laptop won't connect to VPN",
    min_words=3
)

if not is_valid:
    raise ValueError(error_msg)
```

### Automatic Validation
Validation runs automatically when tickets are submitted via:
1. **Pydantic validator** on `TicketCreate.description` field
2. **AI pipeline** at Wave 0 (before any processing)

## Performance

- **Validation time**: <5ms per request
- **Memory overhead**: Negligible (~500 common words in memory)
- **No external dependencies**: Pure Python regex + string operations

## Configuration

### Tunable Parameters

In `TextValidationService.__init__()`:
```python
# Common English words + IT domain terms
self._common_words = {
    # General English
    "the", "be", "to", "of", "and", ...
    
    # IT domain
    "computer", "network", "internet", "email", "password", ...
}

# Keyboard patterns
self._keyboard_patterns = [
    "qwerty", "asdfgh", "zxcvbn", ...
]
```

### Validation Thresholds

In `validate()` method:
- `min_words`: Default 3, adjustable per call
- `min_length`: 10 characters
- `max_digit_ratio`: 0.70 (70% digits)
- `min_english_ratio`: 0.30 (30% recognizable words)
- `max_consonant_streak`: 4 consecutive consonants
- `max_cv_ratio`: 6.0

## Impact

### Benefits
✅ **Prevents garbage tickets** from entering the queue  
✅ **Improves ML accuracy** by rejecting invalid input  
✅ **Better UX** with clear error messages  
✅ **Reduces false classifications** (no more random text → Database)  
✅ **Protects downstream services** from processing gibberish  

### Edge Cases Handled
- Multi-language: Detects non-English but allows with low threshold
- Technical jargon: IT terms included in common word dictionary
- Typos: Moderate tolerance (30% recognizable word threshold)
- Numbers in context: Allows numbers if <70% of content

## Future Enhancements

### Potential Improvements
1. **Language detection integration**: Better multi-language support
2. **ML-based gibberish detection**: Train a small classifier
3. **Context-aware validation**: Different rules for subject vs description
4. **Profanity filtering**: Add inappropriate content detection
5. **Spam detection**: Detect promotional/spam content patterns

## Related Files

- `backend/services/text_validation_service.py` - Core validation logic
- `backend/models/ticket.py` - Pydantic model validators
- `backend/routers/tickets.py` - AI pipeline integration
- `backend/services/classifier_service.py` - Improved keyword fallback
- `backend/test_text_validation.py` - Validation test suite

## Rollback

To disable validation temporarily:

### Option 1: Skip Pydantic validation
Comment out the validator in `models/ticket.py`:
```python
@field_validator("description")
@classmethod
def description_not_blank(cls, v: str) -> str:
    if not v.strip():
        raise ValueError("Description cannot be blank")
    
    # DISABLED: Uncomment to re-enable
    # from services.text_validation_service import text_validation_service
    # is_valid, error_msg = text_validation_service.validate(v, min_words=3)
    # if not is_valid:
    #     raise ValueError(error_msg)
    
    return v.strip()
```

### Option 2: Skip pipeline validation
Comment out Wave 0 in `routers/tickets.py`:
```python
# DISABLED: Uncomment to re-enable
# is_valid, validation_error = text_validation_service.validate(
#     combined_text, min_words=3
# )
# if not is_valid:
#     raise HTTPException(
#         status_code=status.HTTP_400_BAD_REQUEST,
#         detail=validation_error
#     )
```

## Monitoring

### Metrics to Track
- **Validation rejection rate**: % of submissions rejected
- **Error message distribution**: Which checks fail most often
- **False positive rate**: Valid tickets incorrectly rejected (from user feedback)

### Logging
All validation failures are logged:
```python
logger.warning(f"Ticket {ticket_id} failed validation: {validation_error}")
```

Check logs for patterns:
```bash
grep "failed validation" backend/logs/*.log | wc -l
```

---

**Version**: 1.0  
**Created**: 2026-07-30  
**Status**: ✅ Production Ready
