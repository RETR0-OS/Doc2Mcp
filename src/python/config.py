"""Configuration management for Doc2MCP server"""
import os
from typing import Optional


class Config:
    """Centralized configuration"""
    
    def __init__(self):
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY")
        self.doc_urls: Optional[str] = os.getenv("DOC_URLS")
        self.phoenix_endpoint: str = os.getenv("PHOENIX_ENDPOINT", "http://localhost:6006/v1/traces")
        self.gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        self.max_pages: int = int(os.getenv("MAX_PAGES", "25"))
        self.request_timeout: float = float(os.getenv("REQUEST_TIMEOUT", "30.0"))
        self.content_limit: int = int(os.getenv("CONTENT_LIMIT", "50000"))
        
    def validate(self) -> bool:
        """Validate required configuration"""
        if not self.doc_urls:
            return False
        return True
