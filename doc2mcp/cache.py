"""JSON file-based cache for documentation pages."""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict


class CachedPage(TypedDict):
    """Structure for a cached documentation page."""

    url: str
    title: str
    summary: str
    content: str
    links: list[dict[str, str]]  # [{"url": "...", "text": "..."}]
    fetched_at: str
    domain: str


class PageCache:
    """File-based cache for documentation pages with similarity-based lookup.

    Pages are stored with descriptive keys that can be used for similarity matching
    to find relevant cached content without re-fetching.
    """

    def __init__(self, cache_path: str | Path = "./doc_cache.json") -> None:
        self.cache_path = Path(cache_path)
        self._cache: dict[str, CachedPage] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        """Load cache from disk."""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, encoding="utf-8") as f:
                    self._cache = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._cache = {}

    def _save_cache(self) -> None:
        """Save cache to disk."""
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(self._cache, f, indent=2, ensure_ascii=False)

    def _make_key(self, url: str) -> str:
        """Create a cache key from URL."""
        return hashlib.sha256(url.encode()).hexdigest()[:16]

    def get(self, url: str) -> CachedPage | None:
        """Get a cached page by URL.

        Args:
            url: The URL to look up.

        Returns:
            Cached page data or None if not found.
        """
        key = self._make_key(url)
        return self._cache.get(key)

    def put(
        self,
        url: str,
        title: str,
        summary: str,
        content: str,
        links: list[dict[str, str]],
        domain: str,
    ) -> None:
        """Store a page in the cache.

        Args:
            url: The page URL.
            title: Page title for similarity matching.
            summary: Brief summary of page content for similarity matching.
            content: Full page content.
            links: List of links found on the page.
            domain: The domain this page belongs to.
        """
        key = self._make_key(url)
        self._cache[key] = CachedPage(
            url=url,
            title=title,
            summary=summary,
            content=content,
            links=links,
            fetched_at=datetime.now(timezone.utc).isoformat(),
            domain=domain,
        )
        self._save_cache()

    def find_similar(self, query: str, domain: str | None = None) -> list[CachedPage]:
        """Find cached pages that might be relevant to a query.

        Uses simple keyword matching on titles and summaries.
        The LLM can use this to find potentially relevant cached pages.

        Args:
            query: Search query to match against.
            domain: Optional domain to filter results.

        Returns:
            List of potentially relevant cached pages, sorted by relevance.
        """
        query_words = set(query.lower().split())
        results: list[tuple[int, CachedPage]] = []

        for page in self._cache.values():
            if domain and page["domain"] != domain:
                continue

            # Score based on word matches in title and summary
            title_words = set(page["title"].lower().split())
            summary_words = set(page["summary"].lower().split())

            title_matches = len(query_words & title_words)
            summary_matches = len(query_words & summary_words)

            score = title_matches * 2 + summary_matches  # Title weighted higher

            if score > 0:
                results.append((score, page))

        # Sort by score descending
        results.sort(key=lambda x: x[0], reverse=True)
        return [page for _, page in results]

    def get_all_for_domain(self, domain: str) -> list[CachedPage]:
        """Get all cached pages for a domain.

        Args:
            domain: The domain to get pages for.

        Returns:
            List of all cached pages for the domain.
        """
        return [page for page in self._cache.values() if page["domain"] == domain]

    def get_index(self, domain: str | None = None) -> list[dict[str, str]]:
        """Get an index of all cached pages (URL, title, summary only).

        Useful for giving the LLM a quick overview of what's cached.

        Args:
            domain: Optional domain to filter results.

        Returns:
            List of page summaries.
        """
        results = []
        for page in self._cache.values():
            if domain and page["domain"] != domain:
                continue
            results.append({
                "url": page["url"],
                "title": page["title"],
                "summary": page["summary"],
            })
        return results

    def clear(self, domain: str | None = None) -> int:
        """Clear cached pages.

        Args:
            domain: If provided, only clear pages for this domain.
                   If None, clear all pages.

        Returns:
            Number of pages cleared.
        """
        if domain is None:
            count = len(self._cache)
            self._cache = {}
        else:
            keys_to_remove = [
                key for key, page in self._cache.items()
                if page["domain"] == domain
            ]
            count = len(keys_to_remove)
            for key in keys_to_remove:
                del self._cache[key]

        self._save_cache()
        return count
