"""OpenAI LLM provider."""

import os

from openai import AsyncOpenAI

from doc2mcp.llm.base import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""
    
    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI provider")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = model
    
    @property
    def name(self) -> str:
        return "openai"
    
    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.1,
        json_response: bool = False,
    ) -> LLMResponse:
        """Generate a response using OpenAI."""
        messages = []
        
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        
        messages.append({"role": "user", "content": prompt})
        
        kwargs = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        if json_response:
            kwargs["response_format"] = {"type": "json_object"}
        
        response = await self.client.chat.completions.create(**kwargs)
        
        return LLMResponse(
            text=response.choices[0].message.content or "",
            tokens_in=response.usage.prompt_tokens if response.usage else None,
            tokens_out=response.usage.completion_tokens if response.usage else None,
            model=self.model,
        )
