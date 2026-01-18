"""Gemini LLM provider."""

import os

from google import genai
from google.genai import types

from doc2mcp.llm.base import LLMProvider, LLMResponse


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider."""
    
    def __init__(self, api_key: str | None = None, model: str = "gemini-2.0-flash-exp"):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required for Gemini provider")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model = model
    
    @property
    def name(self) -> str:
        return "gemini"
    
    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.1,
        json_response: bool = False,
    ) -> LLMResponse:
        """Generate a response using Gemini."""
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            max_output_tokens=max_tokens,
            temperature=temperature,
        )
        
        if json_response:
            config.response_mime_type = "application/json"
        
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config,
        )
        
        tokens_in = getattr(
            getattr(response, "usage_metadata", None),
            "prompt_token_count",
            None,
        )
        tokens_out = getattr(
            getattr(response, "usage_metadata", None),
            "candidates_token_count",
            None,
        )
        
        return LLMResponse(
            text=response.text,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            model=self.model,
        )
