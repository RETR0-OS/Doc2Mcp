"""Sitemap-based URL index for faster documentation search.

This module provides lazy indexing of documentation sites by:
1. Trying to fetch sitemap.xml first
2. Falling back to BFS crawling if no sitemap
3. Storing URL metadata for fast keyword-based matching
"""

import asyncio
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict
from urllib.parse import urljoin, urlparse

import httpx


class IndexedUrl(TypedDict):
    """Structure for an indexed URL."""

    url: str
    path_segments: list[str]  # URL path split into segments
    title_hint: str  # From link text or URL
    keywords: list[str]  # Extracted from URL/title
    depth: int  # Depth from root
    priority: float  # From sitemap or computed
    changefreq: str | None  # From sitemap (daily, weekly, etc.)


class DomainIndex(TypedDict):
    """Structure for a domain's URL index."""

    domain: str
    indexed_at: str
    sitemap_url: str | None
    source_type: str  # "sitemap" or "crawl"
    urls: list[IndexedUrl]
    url_count: int


@dataclass
class UrlMatch:
    """A URL match result with relevance score."""

    url: str
    title_hint: str
    score: float
    match_reasons: list[str]


class SitemapIndex:
    """URL index for fast documentation lookup.

    Implements lazy indexing - domains are indexed on first search request.
    Supports sitemap.xml parsing with fallback to BFS crawling.
    """

    def __init__(
        self,
        index_path: str | Path = "./sitemap_index.json",
        ttl: int = 86400,  # 24 hours default
        max_urls_per_domain: int = 1000,
        crawl_depth: int = 3,
        parallel_fetch_limit: int = 10,
    ) -> None:
        self.index_path = Path(index_path)
        self.ttl = ttl
        self.max_urls_per_domain = max_urls_per_domain
        self.crawl_depth = crawl_depth
        self.parallel_fetch_limit = parallel_fetch_limit
        self._index: dict[str, DomainIndex] = {}
        self._indexing_locks: dict[str, asyncio.Lock] = {}
        self._load_index()

    def _load_index(self) -> None:
        """Load index from disk."""
        if self.index_path.exists():
            try:
                with open(self.index_path, encoding="utf-8") as f:
                    self._index = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._index = {}

    def _save_index(self) -> None:
        """Save index to disk."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(self._index, f, indent=2, ensure_ascii=False)

    def _is_stale(self, domain: str) -> bool:
        """Check if a domain's index is stale."""
        if domain not in self._index:
            return True

        indexed_at = self._index[domain].get("indexed_at", "")
        if not indexed_at:
            return True

        try:
            indexed_time = datetime.fromisoformat(indexed_at)
            age = (datetime.now(timezone.utc) - indexed_time).total_seconds()
            return age > self.ttl
        except (ValueError, TypeError):
            return True

    def _extract_keywords(self, url: str, title_hint: str = "") -> list[str]:
        """Extract keywords from URL path and title hint."""
        keywords = set()

        # Extract from URL path
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split("/") if p]

        for part in path_parts:
            # Split on common delimiters
            words = re.split(r"[-_.]", part.lower())
            for word in words:
                # Filter out common non-informative parts
                if len(word) > 2 and word not in {"html", "htm", "php", "asp", "www", "com", "org", "index"}:
                    keywords.add(word)

        # Extract from title hint
        if title_hint:
            title_words = re.split(r"[\s\-_|/\\:]+", title_hint.lower())
            for word in title_words:
                if len(word) > 2:
                    keywords.add(word)

        return list(keywords)

    def _extract_path_segments(self, url: str) -> list[str]:
        """Extract meaningful path segments from URL."""
        parsed = urlparse(url)
        segments = [s for s in parsed.path.split("/") if s]
        # Filter out file extensions and common non-informative segments
        cleaned = []
        for seg in segments:
            # Remove common extensions
            seg = re.sub(r"\.(html?|php|asp|aspx|jsp)$", "", seg, flags=re.IGNORECASE)
            if seg and seg.lower() not in {"index", "default"}:
                cleaned.append(seg)
        return cleaned

    def _compute_depth(self, url: str, base_url: str) -> int:
        """Compute URL depth relative to base URL."""
        base_parsed = urlparse(base_url)
        url_parsed = urlparse(url)

        base_segments = len([s for s in base_parsed.path.split("/") if s])
        url_segments = len([s for s in url_parsed.path.split("/") if s])

        return max(0, url_segments - base_segments)

    async def _fetch_sitemap(self, domain: str) -> list[IndexedUrl] | None:
        """Try to fetch and parse sitemap.xml for a domain.

        Returns list of IndexedUrl or None if no sitemap found.
        """
        sitemap_urls = [
            f"https://{domain}/sitemap.xml",
            f"https://{domain}/sitemap_index.xml",
            f"https://www.{domain}/sitemap.xml" if not domain.startswith("www.") else None,
        ]
        sitemap_urls = [u for u in sitemap_urls if u]

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            for sitemap_url in sitemap_urls:
                try:
                    response = await client.get(sitemap_url)
                    if response.status_code == 200:
                        return self._parse_sitemap(response.text, sitemap_url)
                except Exception:
                    continue

            # Try robots.txt for sitemap reference
            try:
                robots_url = f"https://{domain}/robots.txt"
                response = await client.get(robots_url)
                if response.status_code == 200:
                    for line in response.text.split("\n"):
                        if line.lower().startswith("sitemap:"):
                            sitemap_url = line.split(":", 1)[1].strip()
                            try:
                                response = await client.get(sitemap_url)
                                if response.status_code == 200:
                                    return self._parse_sitemap(response.text, sitemap_url)
                            except Exception:
                                continue
            except Exception:
                pass

        return None

    def _parse_sitemap(self, xml_content: str, sitemap_url: str) -> list[IndexedUrl]:
        """Parse sitemap XML and extract URLs with metadata."""
        urls: list[IndexedUrl] = []

        try:
            # Handle both regular sitemaps and sitemap indexes
            root = ET.fromstring(xml_content)

            # Remove namespace for easier parsing
            namespace = ""
            if root.tag.startswith("{"):
                namespace = root.tag.split("}")[0] + "}"

            # Check if this is a sitemap index
            sitemap_refs = root.findall(f".//{namespace}sitemap/{namespace}loc")
            if sitemap_refs:
                # This is a sitemap index - we'd need to fetch sub-sitemaps
                # For now, just extract URLs from the first level
                pass

            # Extract URLs
            for url_elem in root.findall(f".//{namespace}url"):
                loc = url_elem.find(f"{namespace}loc")
                if loc is None or not loc.text:
                    continue

                url = loc.text.strip()
                parsed = urlparse(url)

                # Extract priority
                priority_elem = url_elem.find(f"{namespace}priority")
                priority = 0.5
                if priority_elem is not None and priority_elem.text:
                    try:
                        priority = float(priority_elem.text)
                    except ValueError:
                        pass

                # Extract changefreq
                changefreq_elem = url_elem.find(f"{namespace}changefreq")
                changefreq = None
                if changefreq_elem is not None and changefreq_elem.text:
                    changefreq = changefreq_elem.text.strip()

                # Build IndexedUrl
                path_segments = self._extract_path_segments(url)
                title_hint = path_segments[-1] if path_segments else ""
                title_hint = title_hint.replace("-", " ").replace("_", " ").title()

                indexed_url = IndexedUrl(
                    url=url,
                    path_segments=path_segments,
                    title_hint=title_hint,
                    keywords=self._extract_keywords(url, title_hint),
                    depth=len(path_segments),
                    priority=priority,
                    changefreq=changefreq,
                )
                urls.append(indexed_url)

                if len(urls) >= self.max_urls_per_domain:
                    break

        except ET.ParseError:
            return []

        return urls

    async def _crawl_urls(self, start_url: str, domain: str) -> list[IndexedUrl]:
        """BFS crawl to discover URLs when no sitemap is available."""
        urls: list[IndexedUrl] = []
        visited: set[str] = set()
        to_visit: list[tuple[str, int, str]] = [(start_url, 0, "")]  # (url, depth, title_hint)

        async with httpx.AsyncClient(
            timeout=15,
            follow_redirects=True,
            headers={"User-Agent": "Doc2MCP/0.1.0 (Documentation Indexer)"},
        ) as client:
            while to_visit and len(urls) < self.max_urls_per_domain:
                # Process batch
                batch = []
                while to_visit and len(batch) < self.parallel_fetch_limit:
                    url, depth, title_hint = to_visit.pop(0)
                    if url not in visited and depth <= self.crawl_depth:
                        visited.add(url)
                        batch.append((url, depth, title_hint))

                if not batch:
                    break

                # Fetch batch in parallel
                tasks = [self._fetch_links(client, url, domain) for url, _, _ in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for (url, depth, title_hint), result in zip(batch, results):
                    if isinstance(result, Exception):
                        continue

                    fetched_title, links = result

                    # Add this URL to index
                    final_title = fetched_title or title_hint
                    indexed_url = IndexedUrl(
                        url=url,
                        path_segments=self._extract_path_segments(url),
                        title_hint=final_title,
                        keywords=self._extract_keywords(url, final_title),
                        depth=depth,
                        priority=max(0.1, 1.0 - depth * 0.2),  # Higher priority for shallower pages
                        changefreq=None,
                    )
                    urls.append(indexed_url)

                    # Add discovered links to queue
                    for link_url, link_text in links:
                        if link_url not in visited:
                            to_visit.append((link_url, depth + 1, link_text))

        return urls

    async def _fetch_links(
        self, client: httpx.AsyncClient, url: str, domain: str
    ) -> tuple[str, list[tuple[str, str]]]:
        """Fetch a page and extract links.

        Returns (title, [(url, link_text), ...])
        """
        response = await client.get(url)
        response.raise_for_status()

        html = response.text
        title = ""
        links: list[tuple[str, str]] = []

        # Simple regex-based extraction (avoiding full HTML parsing for speed)
        # Extract title
        title_match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()

        # Extract links
        link_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>'
        for match in re.finditer(link_pattern, html, re.IGNORECASE):
            href, text = match.groups()

            # Skip anchors, mailto, javascript
            if href.startswith(("#", "mailto:", "javascript:", "tel:")):
                continue

            # Resolve relative URLs
            full_url = urljoin(url, href)
            parsed = urlparse(full_url)

            # Filter to same domain
            if domain in parsed.netloc:
                # Normalize URL (remove fragments)
                normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                if parsed.query:
                    normalized += f"?{parsed.query}"

                links.append((normalized, text.strip()))

        return title, links

    async def ensure_indexed(self, domain: str, start_url: str | None = None) -> DomainIndex:
        """Ensure a domain is indexed, indexing it if needed.

        This is the main entry point - called lazily on first search.

        Args:
            domain: The domain to index.
            start_url: Optional starting URL for crawling.

        Returns:
            The domain's index data.
        """
        # Get or create lock for this domain
        if domain not in self._indexing_locks:
            self._indexing_locks[domain] = asyncio.Lock()

        async with self._indexing_locks[domain]:
            # Check if already indexed and not stale
            if not self._is_stale(domain):
                return self._index[domain]

            # Try sitemap first
            urls = await self._fetch_sitemap(domain)
            source_type = "sitemap"
            sitemap_url = f"https://{domain}/sitemap.xml" if urls else None

            # Fall back to crawling
            if not urls:
                source_type = "crawl"
                crawl_start = start_url or f"https://{domain}/"
                urls = await self._crawl_urls(crawl_start, domain)

            # Store index
            self._index[domain] = DomainIndex(
                domain=domain,
                indexed_at=datetime.now(timezone.utc).isoformat(),
                sitemap_url=sitemap_url,
                source_type=source_type,
                urls=urls,
                url_count=len(urls),
            )
            self._save_index()

            return self._index[domain]

    def find_relevant_urls(
        self,
        query: str,
        domain: str,
        max_results: int = 10,
    ) -> list[UrlMatch]:
        """Find URLs relevant to a query using keyword matching.

        This is the fast, LLM-free lookup for candidate URLs.

        Args:
            query: Search query.
            domain: Domain to search in.
            max_results: Maximum results to return.

        Returns:
            List of UrlMatch objects sorted by relevance.
        """
        if domain not in self._index:
            return []

        domain_index = self._index[domain]
        query_words = set(re.split(r"[\s\-_/\\:]+", query.lower()))
        query_words = {w for w in query_words if len(w) > 2}

        matches: list[UrlMatch] = []

        for indexed_url in domain_index["urls"]:
            score = 0.0
            reasons: list[str] = []

            # Score based on keyword matches
            url_keywords = set(indexed_url["keywords"])
            keyword_matches = query_words & url_keywords
            if keyword_matches:
                score += len(keyword_matches) * 2.0
                reasons.append(f"keywords: {', '.join(keyword_matches)}")

            # Score based on path segment matches
            path_words = set()
            for seg in indexed_url["path_segments"]:
                path_words.update(re.split(r"[-_]", seg.lower()))

            path_matches = query_words & path_words
            if path_matches:
                score += len(path_matches) * 1.5
                reasons.append(f"path: {', '.join(path_matches)}")

            # Score based on title hint matches
            title_words = set(re.split(r"[\s\-_]+", indexed_url["title_hint"].lower()))
            title_matches = query_words & title_words
            if title_matches:
                score += len(title_matches) * 2.5
                reasons.append(f"title: {', '.join(title_matches)}")

            # Boost by sitemap priority
            score *= (0.5 + indexed_url["priority"])

            # Slight penalty for deep pages
            score *= max(0.5, 1.0 - indexed_url["depth"] * 0.1)

            if score > 0:
                matches.append(UrlMatch(
                    url=indexed_url["url"],
                    title_hint=indexed_url["title_hint"],
                    score=score,
                    match_reasons=reasons,
                ))

        # Sort by score descending
        matches.sort(key=lambda m: m.score, reverse=True)
        return matches[:max_results]

    def get_domain_stats(self, domain: str) -> dict | None:
        """Get statistics about a domain's index."""
        if domain not in self._index:
            return None

        idx = self._index[domain]
        return {
            "domain": domain,
            "indexed_at": idx["indexed_at"],
            "source_type": idx["source_type"],
            "url_count": idx["url_count"],
            "sitemap_url": idx["sitemap_url"],
        }

    def clear(self, domain: str | None = None) -> int:
        """Clear index data.

        Args:
            domain: If provided, only clear this domain. Otherwise clear all.

        Returns:
            Number of domains cleared.
        """
        if domain:
            if domain in self._index:
                del self._index[domain]
                self._save_index()
                return 1
            return 0
        else:
            count = len(self._index)
            self._index = {}
            self._save_index()
            return count
