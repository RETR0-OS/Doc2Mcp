"""Deep research agent for intelligent documentation search."""

import json
import os
from typing import Any
from urllib.parse import urlparse

from opentelemetry import trace

from doc2mcp.cache import PageCache
from doc2mcp.compression import ContentCompressor
from doc2mcp.config import Config, LocalSource, ToolConfig, WebSource
from doc2mcp.fetchers.local import LocalFetcher
from doc2mcp.fetchers.web import FetchResult, WebFetcher
from doc2mcp.llm import create_llm_provider, LLMProvider
from doc2mcp.sitemap_index import SitemapIndex
from doc2mcp.tracing.phoenix import trace_doc_retrieval, trace_llm_call

# Default max pages to explore per query
DEFAULT_MAX_PAGES = 10


class DocSearchAgent:
    """Deep research agent that iteratively explores documentation.

    This agent:
    1. Starts from configured source URLs
    2. Fetches pages and caches them with descriptive summaries
    3. Uses an LLM to decide which links to follow based on the query
    4. Continues until it finds sufficient information or hits limits
    5. Returns the most relevant documentation
    """

    def __init__(
        self,
        config: Config,
        cache_path: str = "./doc_cache.json",
        sitemap_index_path: str = "./sitemap_index.json",
        max_pages: int = DEFAULT_MAX_PAGES,
        llm_provider: LLMProvider | None = None,
    ) -> None:
        self.config = config
        self.max_pages = max_pages
        self.web_fetcher = WebFetcher(timeout=config.settings.request_timeout)
        self.local_fetcher = LocalFetcher()
        self.cache = PageCache(cache_path)

        # Initialize sitemap index for faster URL lookup
        sitemap_settings = config.settings.sitemap_index
        self.sitemap_index = SitemapIndex(
            index_path=sitemap_index_path,
            ttl=sitemap_settings.ttl,
            max_urls_per_domain=sitemap_settings.max_urls_per_domain,
            parallel_fetch_limit=sitemap_settings.parallel_fetch_limit,
        )
        self.sitemap_enabled = sitemap_settings.enabled

        # Initialize content compressor for token optimization
        compression_settings = config.settings.compression
        self.compressor = ContentCompressor(
            aggressiveness=compression_settings.aggressiveness,
            min_content_length=compression_settings.min_content_length,
            enabled=compression_settings.enabled,
        )

        # Initialize LLM provider (supports Gemini, OpenAI, Local)
        self.llm = llm_provider or create_llm_provider()

        # System prompts
        self.nav_system_instruction = self._get_navigation_prompt()
        self.synthesis_system_instruction = self._get_synthesis_prompt()

        self.tracer = trace.get_tracer("doc2mcp.agent")

    def _get_navigation_prompt(self) -> str:
        """System prompt for navigation decisions."""
        return """You are a documentation research assistant. Your job is to analyze documentation pages and decide how to navigate to find relevant information.

You will be given:
1. A user's query about what they need to find
2. Content from the current page
3. Links available on the page

You must respond with a JSON object containing:
{
    "has_sufficient_info": boolean,  // true if current content fully answers the query
    "relevant_content": string,      // extract of relevant content found (if any)
    "summary": string,               // brief summary of this page (for caching)
    "links_to_explore": [            // links worth exploring (max 3, most promising first)
        {"url": "...", "reason": "..."}
    ]
}

Guidelines:
- Be conservative with "has_sufficient_info" - only true if the query is fully answered
- Extract ONLY directly relevant content, not the whole page
- Prioritize links that seem most likely to contain the answer
- If the page is not relevant at all, return empty relevant_content and suggest better links
- Focus on official documentation, API references, and getting-started guides"""

    def _get_synthesis_prompt(self) -> str:
        """System prompt for final answer synthesis."""
        return """You are a documentation search assistant. Your job is to:
1. Read the provided documentation excerpts from multiple sources
2. Synthesize a comprehensive answer to the user's query
3. Preserve code examples, API signatures, and technical details
4. Format the output clearly with proper markdown
5. Include source references

If the documentation doesn't fully answer the query, say what's missing.
Do NOT make up information - only use what's in the provided documentation."""

    async def search(self, tool_name: str, query: str) -> dict[str, Any]:
        """Search for documentation using deep exploration.

        Args:
            tool_name: Name of the tool to search documentation for.
            query: Search query describing what information is needed.

        Returns:
            Dictionary containing:
                - content: The relevant documentation text
                - sources: List of source URLs/paths used
                - tool: Tool name and description
                - pages_explored: Number of pages explored
        """
        with self.tracer.start_as_current_span("doc_search") as span:
            span.set_attribute("tool_name", tool_name)
            span.set_attribute("query", query)

            # Get tool config
            tool_config = self.config.tools.get(tool_name)
            if not tool_config:
                available = list(self.config.tools.keys())
                return {
                    "error": f"Tool '{tool_name}' not found",
                    "available_tools": available,
                    "content": None,
                    "sources": [],
                }

            # Perform deep search
            result = await self._deep_search(query, tool_config)

            # Trace the retrieval
            trace_doc_retrieval(
                tool_name=tool_name,
                query=query,
                sources=result["sources"],
                content_length=len(result["content"]) if result["content"] else 0,
            )

            return {
                **result,
                "tool": {
                    "name": tool_config.name,
                    "description": tool_config.description,
                },
            }

    async def _deep_search(
        self, query: str, tool_config: ToolConfig
    ) -> dict[str, Any]:
        """Perform deep iterative search through documentation.

        Uses sitemap index for fast URL lookup when available,
        falling back to full exploration if no good matches found.

        Args:
            query: The user's search query.
            tool_config: Configuration for the tool.

        Returns:
            Dictionary with content, sources, and exploration stats.
        """
        # Collect relevant content from exploration
        collected_content: list[dict[str, str]] = []  # [{"url": ..., "content": ...}]
        visited_urls: set[str] = set()
        sources: list[str] = []

        # Queue of URLs to explore: (url, priority)
        to_explore: list[tuple[str, int]] = []

        # Get starting URLs and domain restrictions
        start_urls, domains = self._get_starting_points(tool_config)

        # Check cache for similar content first
        for domain in domains:
            cached = self.cache.find_similar(query, domain)
            for page in cached[:3]:  # Use top 3 cached matches
                if page["url"] not in visited_urls:
                    collected_content.append({
                        "url": page["url"],
                        "content": page["content"][:5000],  # Limit cached content
                    })
                    visited_urls.add(page["url"])
                    sources.append(f"[cached] {page['url']}")

        # Try to get candidate URLs from sitemap index (fast path)
        sitemap_candidates = await self._get_sitemap_candidates(query, tool_config)

        if sitemap_candidates:
            # Use sitemap candidates as starting points with high priority
            for url, score in sitemap_candidates:
                if url not in visited_urls:
                    # Lower priority number = higher priority (explored first)
                    # High-scoring matches get priority 0-4, lower scores get 5-9
                    priority = max(0, min(9, int(10 - score)))
                    to_explore.append((url, priority))
                    sources.append(f"[sitemap-match] {url}")

        # Add original starting URLs as fallback (lower priority)
        for url in start_urls:
            if url not in visited_urls:
                to_explore.append((url, 10))  # Lower priority than sitemap matches

        # Exploration loop
        pages_explored = 0
        has_sufficient = False

        while to_explore and pages_explored < self.max_pages and not has_sufficient:
            # Get next URL (sort by priority, lower is better)
            to_explore.sort(key=lambda x: x[1])
            current_url, _ = to_explore.pop(0)

            if current_url in visited_urls:
                continue

            visited_urls.add(current_url)
            pages_explored += 1

            # Check cache first
            cached_page = self.cache.get(current_url)

            if cached_page:
                # Use cached content
                fetch_result = FetchResult(
                    url=cached_page["url"],
                    content=cached_page["content"],
                    title=cached_page["title"],
                    links=cached_page["links"],
                )
            else:
                # Fetch the page
                try:
                    base_domain = domains[0] if domains else None
                    fetch_result = await self.web_fetcher.fetch_with_links(
                        current_url, base_domain
                    )
                except Exception as e:
                    # Skip failed fetches
                    continue

            # Ask LLM to analyze the page
            nav_result = await self._analyze_page(query, fetch_result)

            # Cache the page with summary
            if not cached_page and fetch_result.content:
                self.cache.put(
                    url=fetch_result.url,
                    title=fetch_result.title,
                    summary=nav_result.get("summary", ""),
                    content=fetch_result.content,
                    links=fetch_result.links,
                    domain=domains[0] if domains else urlparse(current_url).netloc,
                )

            # Collect relevant content
            if nav_result.get("relevant_content"):
                collected_content.append({
                    "url": current_url,
                    "content": nav_result["relevant_content"],
                })
                sources.append(current_url)

            # Check if we have enough
            if nav_result.get("has_sufficient_info"):
                has_sufficient = True
                break

            # Add recommended links to queue
            for i, link in enumerate(nav_result.get("links_to_explore", [])):
                link_url = link.get("url", "")
                if link_url and link_url not in visited_urls:
                    # Priority based on position in recommendations
                    to_explore.append((link_url, pages_explored * 10 + i))

        # Handle local sources (not part of deep search)
        local_content = await self._fetch_local_sources(tool_config)
        if local_content:
            collected_content.append({
                "url": "[local]",
                "content": local_content,
            })
            sources.append("[local sources]")

        # Synthesize final answer
        sitemap_used = len(sitemap_candidates) > 0

        if not collected_content:
            return {
                "content": "No relevant documentation found.",
                "sources": sources,
                "pages_explored": pages_explored,
                "sitemap_used": sitemap_used,
                "sitemap_candidates": len(sitemap_candidates),
            }

        final_content = await self._synthesize_answer(query, collected_content)

        # Truncate if needed
        max_len = self.config.settings.max_content_length
        if len(final_content) > max_len:
            final_content = final_content[:max_len] + "\n\n[Content truncated...]"

        return {
            "content": final_content,
            "sources": sources,
            "pages_explored": pages_explored,
            "sitemap_used": sitemap_used,
            "sitemap_candidates": len(sitemap_candidates),
        }

    def _get_starting_points(
        self, tool_config: ToolConfig
    ) -> tuple[list[str], list[str]]:
        """Extract starting URLs and domains from tool config.

        Args:
            tool_config: Configuration for the tool.

        Returns:
            Tuple of (list of starting URLs, list of allowed domains).
        """
        urls = []
        domains = []

        for source in tool_config.sources:
            if isinstance(source, WebSource):
                urls.append(source.url)
                parsed = urlparse(source.url)
                if parsed.netloc and parsed.netloc not in domains:
                    domains.append(parsed.netloc)

        return urls, domains

    async def _get_sitemap_candidates(
        self, query: str, tool_config: ToolConfig
    ) -> list[tuple[str, float]]:
        """Get candidate URLs from sitemap index based on query.

        Args:
            query: The search query.
            tool_config: Configuration for the tool.

        Returns:
            List of (url, score) tuples for relevant URLs.
        """
        if not self.sitemap_enabled:
            return []

        sitemap_settings = self.config.settings.sitemap_index
        candidates: list[tuple[str, float]] = []

        for source in tool_config.sources:
            if not isinstance(source, WebSource):
                continue

            parsed = urlparse(source.url)
            domain = parsed.netloc

            # Ensure domain is indexed (lazy indexing)
            try:
                await self.sitemap_index.ensure_indexed(domain, source.url)
            except Exception:
                # Skip if indexing fails - will fall back to normal search
                continue

            # Find relevant URLs from index
            matches = self.sitemap_index.find_relevant_urls(
                query=query,
                domain=domain,
                max_results=sitemap_settings.max_url_candidates,
            )

            # Filter by minimum score
            for match in matches:
                if match.score >= sitemap_settings.min_match_score:
                    candidates.append((match.url, match.score))

        # Sort by score descending
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:sitemap_settings.max_url_candidates]

    async def _analyze_page(
        self, query: str, fetch_result: FetchResult
    ) -> dict[str, Any]:
        """Use LLM to analyze a page and decide next steps.

        Args:
            query: The user's search query.
            fetch_result: The fetched page content and links.

        Returns:
            Navigation decision with relevant content and links to explore.
        """
        # Truncate content for analysis
        content = fetch_result.content[:50000]

        # Compress content to reduce token usage
        compression_settings = self.config.settings.compression
        compressed_content = self.compressor.compress(
            content,
            aggressiveness=compression_settings.analysis_aggressiveness,
        )

        # Format links for the prompt
        links_text = "\n".join(
            f"- [{link['text']}]({link['url']})"
            for link in fetch_result.links[:50]  # Limit links shown
        )

        prompt = f"""Query: {query}

Current page: {fetch_result.url}
Title: {fetch_result.title}

Page content:
{compressed_content.compressed_text}

Available links on this page:
{links_text}

Analyze this page and respond with a JSON object."""

        with self.tracer.start_as_current_span("nav_decision") as span:
            span.set_attribute("url", fetch_result.url)
            span.set_attribute("content_compressed", compressed_content.was_compressed)
            if compressed_content.was_compressed:
                span.set_attribute("tokens_saved", compressed_content.tokens_saved)
                span.set_attribute("compression_ratio", compressed_content.compression_ratio)

            try:
                response = await self.llm.generate(
                    prompt=prompt,
                    system_instruction=self.nav_system_instruction,
                    max_tokens=4096,
                    temperature=0.1,
                    json_response=True,
                )

                result_text = response.text

                # Trace the call
                trace_llm_call(
                    model=response.model or self.llm.name,
                    messages=[{"role": "user", "content": prompt[:500]}],
                    response=result_text[:500],
                    tokens_in=response.tokens_in,
                    tokens_out=response.tokens_out,
                )

                return json.loads(result_text)

            except (json.JSONDecodeError, Exception) as e:
                # Return safe default on error
                return {
                    "has_sufficient_info": False,
                    "relevant_content": "",
                    "summary": fetch_result.title,
                    "links_to_explore": [],
                }

    async def _synthesize_answer(
        self, query: str, collected_content: list[dict[str, str]]
    ) -> str:
        """Synthesize final answer from collected content.

        Args:
            query: The user's search query.
            collected_content: List of content excerpts from explored pages.

        Returns:
            Synthesized documentation answer.
        """
        # Format collected content
        content_parts = []
        for item in collected_content:
            content_parts.append(f"## Source: {item['url']}\n\n{item['content']}")

        combined = "\n\n---\n\n".join(content_parts)

        # Truncate if needed
        if len(combined) > 100000:
            combined = combined[:100000] + "\n\n[Content truncated...]"

        # Compress combined content to reduce token usage (light compression for synthesis)
        compression_settings = self.config.settings.compression
        compressed_content = self.compressor.compress(
            combined,
            aggressiveness=compression_settings.synthesis_aggressiveness,
        )

        prompt = f"""Query: {query}

Documentation excerpts found:

{compressed_content.compressed_text}

Please synthesize a comprehensive answer to the query using the documentation above. Include code examples if available."""

        with self.tracer.start_as_current_span("synthesis") as span:
            span.set_attribute("content_compressed", compressed_content.was_compressed)
            if compressed_content.was_compressed:
                span.set_attribute("tokens_saved", compressed_content.tokens_saved)
                span.set_attribute("compression_ratio", compressed_content.compression_ratio)

            response = await self.llm.generate(
                prompt=prompt,
                system_instruction=self.synthesis_system_instruction,
                max_tokens=8192,
                temperature=0.1,
                json_response=False,
            )

            result = response.text

            trace_llm_call(
                model=response.model or self.llm.name,
                messages=[{"role": "user", "content": prompt[:500]}],
                response=result[:500],
                tokens_in=response.tokens_in,
                tokens_out=response.tokens_out,
            )

            return result

    async def _fetch_local_sources(self, tool_config: ToolConfig) -> str:
        """Fetch content from local sources.

        Args:
            tool_config: Configuration for the tool.

        Returns:
            Combined local documentation content.
        """
        parts = []
        for source in tool_config.sources:
            if isinstance(source, LocalSource):
                try:
                    content = await self.local_fetcher.fetch(source)
                    if content:
                        parts.append(content)
                except Exception:
                    pass
        return "\n\n".join(parts)

    async def list_tools(self) -> list[dict[str, str]]:
        """List all available tools.

        Returns:
            List of tool info dictionaries with name and description.
        """
        return [
            {
                "id": tool_id,
                "name": tool_config.name,
                "description": tool_config.description,
            }
            for tool_id, tool_config in self.config.tools.items()
        ]

    async def close(self) -> None:
        """Clean up resources."""
        await self.web_fetcher.close()
