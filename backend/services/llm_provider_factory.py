"""
services/llm_provider_factory.py — Environment-based LLM provider selector.

Usage:
    from services.llm_provider_factory import get_llm_provider

    provider = get_llm_provider()
    text = await provider.generate(prompt)

Provider selection (controlled by LLM_PROVIDER env var):
    "ollama"  → OllamaProvider  (local dev, default)
    "qwen"    → QwenProvider    (production)
"""

from loguru import logger
from core.config import settings


def get_llm_provider():
    """
    Return the active LLM provider instance based on LLM_PROVIDER env var.

    Returns:
        OllamaProvider or QwenProvider — both share the same interface.

    Raises:
        ValueError: If LLM_PROVIDER is set to an unknown value.
    """
    provider_name = settings.LLM_PROVIDER.lower().strip()

    if provider_name == "ollama":
        from services.ollama_provider import ollama_provider

        logger.debug("LLM provider: Ollama (local)")
        return ollama_provider

    if provider_name == "qwen":
        from services.qwen_provider import qwen_provider

        logger.debug("LLM provider: Qwen (production)")
        return qwen_provider

    raise ValueError(
        f"Unknown LLM_PROVIDER='{provider_name}'. " f"Valid options: 'ollama', 'qwen'"
    )


# Convenience singleton — resolved once at import time
llm_provider = get_llm_provider()
