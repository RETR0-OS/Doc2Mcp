"""Local LLM provider (Ollama-compatible)."""

import os

import httpx

from doc2mcp.llm.base import LLMProvider, LLMResponse


class LocalLLMProvider(LLMProvider):
    """Local LLM provider using Ollama-compatible API."""
    
    def __init__(
        self,
        base_url: str | None = None,
        model: str = "llama3.2",
    ):
        self.base_url = base_url or os.environ.get("LOCAL_LLM_URL", "http://localhost:11434")
        self.model = model
        self.client = httpx.AsyncClient(timeout=120.0)
    
    @property
    def name(self) -> str:
        return "local"
    
    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.1,
        json_response: bool = False,
    ) -> LLMResponse:
        """Generate a response using local Ollama API."""
        # Build the full prompt with system instruction
        full_prompt = prompt
        if system_instruction:
            full_prompt = f"{system_instruction}\n\n{prompt}"
        
        # Use Ollama's generate endpoint
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            }
        }
        
        if json_response:
            payload["format"] = "json"
        
        response = await self.client.post(
            f"{self.base_url}/api/generate",
            json=payload,
        )
        response.raise_for_status()
        
        data = response.json()
        
        return LLMResponse(
            text=data.get("response", ""),
            tokens_in=data.get("prompt_eval_count"),
            tokens_out=data.get("eval_count"),
            model=self.model,
        )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
