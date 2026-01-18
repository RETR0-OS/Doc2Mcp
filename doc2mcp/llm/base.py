"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    
    text: str
    tokens_in: int | None = None
    tokens_out: int | None = None
    model: str | None = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.1,
        json_response: bool = False,
    ) -> LLMResponse:
        """Generate a response from the LLM.
        
        Args:
            prompt: The user prompt.
            system_instruction: Optional system instruction.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.
            json_response: Whether to request JSON output.
            
        Returns:
            LLMResponse with generated text and metadata.
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name."""
        pass
