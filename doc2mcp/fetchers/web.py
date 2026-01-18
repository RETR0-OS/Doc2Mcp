"""Web scraping fetcher for documentation."""

import re
from typing import Any

import httpx
from bs4 import BeautifulSoup

from doc2mcp.config import WebSource


class WebFetcher:
    """Fetches and parses documentation from web URLs."""

    def __init__(self, timeout: int = 30) -> None:
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": "Doc2MCP/0.1.0 (Documentation Fetcher)",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
            )
        return self._client

    async def fetch(self, source: WebSource) -> str:
        """Fetch documentation from a web URL.

        Args:
            source: Web source configuration with URL and optional selectors.

        Returns:
            Extracted text content from the page.
        """
        client = await self._get_client()
        response = await client.get(source.url)
        response.raise_for_status()

        html = response.text
        return self._extract_content(html, source.selectors)

    def _extract_content(
        self, html: str, selectors: dict[str, str] | None = None
    ) -> str:
        """Extract text content from HTML.

        Args:
            html: Raw HTML content.
            selectors: Optional CSS selectors for content/exclude areas.

        Returns:
            Cleaned text content.
        """
        soup = BeautifulSoup(html, "lxml")

        # Remove script and style elements
        for element in soup(["script", "style", "noscript"]):
            element.decompose()

        # Apply exclude selectors if provided
        if selectors and "exclude" in selectors:
            for selector in selectors["exclude"].split(","):
                selector = selector.strip()
                for element in soup.select(selector):
                    element.decompose()

        # Find content area
        content_element: Any = soup
        if selectors and "content" in selectors:
            for selector in selectors["content"].split(","):
                selector = selector.strip()
                found = soup.select_one(selector)
                if found:
                    content_element = found
                    break

        # Extract text
        text = content_element.get_text(separator="\n", strip=True)

        # Clean up whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)

        return text.strip()

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
