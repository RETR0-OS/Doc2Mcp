"""Factory for creating LLM providers."""

import os
from typing import Literal

from doc2mcp.llm.base import LLMProvider


ProviderType = Literal["gemini", "openai", "local"]


def create_llm_provider(
    provider: ProviderType | None = None,
    **kwargs,
) -> LLMProvider:
    """Create an LLM provider based on configuration.
    
    Args:
        provider: The provider type. If None, reads from LLM_PROVIDER env var.
        **kwargs: Additional arguments passed to the provider constructor.
        
    Returns:
        An LLM provider instance.
        
    Raises:
        ValueError: If provider is unknown or not configured.
    """
    if provider is None:
        provider = os.environ.get("LLM_PROVIDER", "gemini").lower()
    
    if provider == "gemini":
        from doc2mcp.llm.gemini import GeminiProvider
        return GeminiProvider(**kwargs)
    
    elif provider == "openai":
        from doc2mcp.llm.openai import OpenAIProvider
        return OpenAIProvider(**kwargs)
    
    elif provider == "local":
        from doc2mcp.llm.local import LocalLLMProvider
        return LocalLLMProvider(**kwargs)
    
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider}. "
            f"Supported providers: gemini, openai, local"
        )
