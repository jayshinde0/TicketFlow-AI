"""
utils/helpers.py — General utility functions shared across services.
"""

import uuid
import random
import string
from datetime import datetime, timezone
from typing import Any, Optional


def generate_uuid() -> str:
    """Generate a random UUID4 string."""
    return str(uuid.uuid4())


def generate_ticket_id(prefix: str = "TKT") -> str:
    """
    Generate a human-readable ticket ID like TKT-A3F8.
    Combines prefix with random alphanumeric characters.
    """
    chars = random.choices(string.ascii_uppercase + string.digits, k=6)
    return f"{prefix}-{''.join(chars)}"


def utcnow() -> datetime:
    """Get current UTC datetime with timezone info."""
    return datetime.now(timezone.utc)


def truncate_text(text: str, max_chars: int = 200) -> str:
    """Safely truncate text to max_chars, appending '...' if cut."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 3] + "..."


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Division that returns default instead of ZeroDivisionError."""
    if denominator == 0:
        return default
    return numerator / denominator


def clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp a float value between min and max."""
    return max(min_val, min(max_val, value))


def mongo_doc_to_dict(doc: Optional[dict]) -> Optional[dict]:
    """
    Convert a MongoDB document to a JSON-serializable dict.
    Removes the _id field and converts ObjectId to string.
    """
    if doc is None:
        return None
    result = dict(doc)
    result.pop("_id", None)
    return result


def paginate(
    total: int,
    page: int,
    page_size: int
) -> dict:
    """
    Compute pagination metadata.

    Returns:
        Dict with total, page, page_size, total_pages, skip, limit.
    """
    import math
    total_pages = math.ceil(total / page_size) if page_size > 0 else 0
    skip = (page - 1) * page_size
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "skip": skip,
        "limit": page_size,
    }


def tier_to_int(tier: str) -> int:
    """Encode user tier as ordinal integer for ML features."""
    mapping = {"Free": 0, "Standard": 1, "Premium": 2, "Enterprise": 3}
    return mapping.get(tier, 1)


def priority_to_int(priority: str) -> int:
    """Encode priority as ordinal integer for ML features."""
    mapping = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
    return mapping.get(priority, 1)


def boost_priority(current_priority: str) -> str:
    """
    Increase priority by one level. Used when sentiment is very negative.
    Critical stays at Critical.
    """
    order = ["Low", "Medium", "High", "Critical"]
    idx = order.index(current_priority) if current_priority in order else 1
    return order[min(idx + 1, len(order) - 1)]
