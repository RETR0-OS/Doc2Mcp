"""Web scraping fetcher for documentation."""

import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from doc2mcp.config import WebSource

JINA_READER_PREFIX = "https://r.jina.ai/"


@dataclass
class FetchResult:
    """Result of fetching a documentation page."""

    url: str
    content: str
    title: str
    links: list[dict[str, str]] = field(default_factory=list)  # [{"url": "...", "text": "..."}]


class WebFetcher:
    """Fetches and parses documentation from web URLs.

    Uses Jina AI Reader by default to handle JavaScript-rendered pages
    and convert them to clean markdown.
    """

    def __init__(self, timeout: int = 30, use_jina: bool = True) -> None:
        self.timeout = timeout
        self.use_jina = use_jina
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
        result = await self.fetch_with_links(source.url)
        return result.content

    async def fetch_with_links(self, url: str, base_domain: str | None = None) -> FetchResult:
        """Fetch documentation and extract links for crawling.

        Args:
            url: The URL to fetch.
            base_domain: If provided, only include links to this domain.

        Returns:
            FetchResult with content, title, and links.
        """
        if self.use_jina:
            return await self._fetch_with_jina(url, base_domain)

        source = WebSource(url=url)
        return await self._fetch_direct_with_links(source, base_domain)

    async def _fetch_with_jina(self, url: str, base_domain: str | None = None) -> FetchResult:
        """Fetch and convert a webpage using Jina AI Reader.

        Jina Reader handles JavaScript rendering and returns clean markdown.

        Args:
            url: The URL to fetch.
            base_domain: If provided, only include links to this domain.

        Returns:
            FetchResult with markdown content and extracted links.
        """
        client = await self._get_client()
        jina_url = f"{JINA_READER_PREFIX}{url}"
        response = await client.get(jina_url)
        response.raise_for_status()

        content = response.text

        # Clean up whitespace
        content = re.sub(r"\n{3,}", "\n\n", content)
        content = content.strip()

        # Extract title from markdown (first # heading)
        title = self._extract_markdown_title(content)

        # Extract links from markdown
        links = self._extract_markdown_links(content, url, base_domain)

        return FetchResult(url=url, content=content, title=title, links=links)

    async def _fetch_direct_with_links(
        self, source: WebSource, base_domain: str | None = None
    ) -> FetchResult:
        """Fetch directly without Jina and extract links.

        Args:
            source: Web source configuration with URL and optional selectors.
            base_domain: If provided, only include links to this domain.

        Returns:
            FetchResult with content and links.
        """
        client = await self._get_client()
        response = await client.get(source.url)
        response.raise_for_status()

        html = response.text
        soup = BeautifulSoup(html, "lxml")

        # Extract title
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""

        # Extract links before removing elements
        links = self._extract_html_links(soup, source.url, base_domain)

        # Extract content
        content = self._extract_content(html, source.selectors)

        return FetchResult(url=source.url, content=content, title=title, links=links)

    async def _fetch_direct(self, source: WebSource) -> str:
        """Fetch directly without Jina (for static HTML sites).

        Args:
            source: Web source configuration with URL and optional selectors.

        Returns:
            Extracted text content from the page.
        """
        result = await self._fetch_direct_with_links(source)
        return result.content

    def _extract_markdown_title(self, content: str) -> str:
        """Extract title from markdown content.

        Args:
            content: Markdown content.

        Returns:
            The first heading or empty string.
        """
        # Look for first # heading
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if match:
            return match.group(1).strip()

        # Fallback: first non-empty line
        for line in content.split("\n"):
            line = line.strip()
            if line and not line.startswith("[") and not line.startswith("!"):
                return line[:100]

        return ""

    def _extract_markdown_links(
        self, content: str, base_url: str, base_domain: str | None = None
    ) -> list[dict[str, str]]:
        """Extract links from markdown content.

        Args:
            content: Markdown content.
            base_url: Base URL for resolving relative links.
            base_domain: If provided, only include links to this domain.

        Returns:
            List of link dictionaries with url and text.
        """
        # Match markdown links: [text](url)
        link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
        matches = re.findall(link_pattern, content)

        links = []
        seen_urls = set()

        for text, href in matches:
            # Skip anchors, images, and non-http links
            if href.startswith("#") or href.startswith("mailto:"):
                continue
            if any(href.lower().endswith(ext) for ext in [".png", ".jpg", ".gif", ".svg", ".ico"]):
                continue

            # Resolve relative URLs
            full_url = urljoin(base_url, href)

            # Filter by domain if specified
            if base_domain:
                parsed = urlparse(full_url)
                if parsed.netloc and base_domain not in parsed.netloc:
                    continue

            # Deduplicate
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            links.append({"url": full_url, "text": text.strip()})

        return links

    def _extract_html_links(
        self, soup: BeautifulSoup, base_url: str, base_domain: str | None = None
    ) -> list[dict[str, str]]:
        """Extract links from HTML.

        Args:
            soup: BeautifulSoup object.
            base_url: Base URL for resolving relative links.
            base_domain: If provided, only include links to this domain.

        Returns:
            List of link dictionaries with url and text.
        """
        links = []
        seen_urls = set()

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            text = a_tag.get_text(strip=True)

            # Skip anchors and non-http links
            if href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
                continue

            # Resolve relative URLs
            full_url = urljoin(base_url, href)

            # Filter by domain if specified
            if base_domain:
                parsed = urlparse(full_url)
                if parsed.netloc and base_domain not in parsed.netloc:
                    continue

            # Deduplicate
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            if text:  # Only include links with text
                links.append({"url": full_url, "text": text})

        return links

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
