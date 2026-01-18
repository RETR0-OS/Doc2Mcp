"""Tool registry that manages auto-generated MCP tools with lazy content loading."""

import hashlib
import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any

from doc2mcp.fetchers.web import WebFetcher
from doc2mcp.indexer.tool_generator import GeneratedTool, index_documentation_source

logger = logging.getLogger(__name__)


class ContentCache:
    """Simple file-based content cache."""
    
    def __init__(self, cache_dir: str | Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _url_to_path(self, url: str) -> Path:
        """Convert URL to cache file path."""
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        return self.cache_dir / f"{url_hash}.txt"
    
    def get(self, url: str) -> str | None:
        """Get cached content for a URL."""
        path = self._url_to_path(url)
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None
    
    def set(self, url: str, content: str) -> None:
        """Cache content for a URL."""
        path = self._url_to_path(url)
        path.write_text(content, encoding="utf-8")


class ToolRegistry:
    """
    Registry for auto-generated documentation tools.
    
    Manages tool definitions and lazy content loading.
    """
    
    def __init__(
        self,
        cache_dir: str = "./.doc2mcp_cache",
        max_tools_per_source: int = 50
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_tools = max_tools_per_source
        
        # In-memory tool registry
        self._tools: dict[str, GeneratedTool] = {}
        self._sources: dict[str, list[str]] = {}  # source_id -> [tool_ids]
        
        # Content cache
        self._content_cache = ContentCache(self.cache_dir / "content")
        self._fetcher = WebFetcher()
        
        # Load persisted tools
        self._load_registry()
    
    def _load_registry(self):
        """Load persisted tool registry from disk."""
        registry_file = self.cache_dir / "registry.json"
        if registry_file.exists():
            try:
                with open(registry_file) as f:
                    data = json.load(f)
                
                for tool_data in data.get("tools", []):
                    tool = GeneratedTool(**tool_data)
                    self._tools[tool.tool_id] = tool
                    
                    if tool.parent_source not in self._sources:
                        self._sources[tool.parent_source] = []
                    self._sources[tool.parent_source].append(tool.tool_id)
                
                logger.info(f"Loaded {len(self._tools)} tools from registry")
            except Exception as e:
                logger.warning(f"Failed to load registry: {e}")
    
    def _save_registry(self):
        """Persist tool registry to disk."""
        registry_file = self.cache_dir / "registry.json"
        try:
            data = {
                "tools": [asdict(t) for t in self._tools.values()]
            }
            # Don't save content to registry (it's in separate cache)
            for tool_data in data["tools"]:
                tool_data["content"] = None
            
            with open(registry_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save registry: {e}")
    
    async def add_source(self, source_id: str, base_url: str) -> list[GeneratedTool]:
        """
        Add a documentation source and generate tools.
        
        Args:
            source_id: Identifier for the source
            base_url: Documentation base URL
            
        Returns:
            List of generated tools
        """
        # Remove existing tools for this source
        if source_id in self._sources:
            for tool_id in self._sources[source_id]:
                self._tools.pop(tool_id, None)
            self._sources.pop(source_id)
        
        # Generate new tools
        tools = await index_documentation_source(
            source_id,
            base_url,
            max_tools=self.max_tools
        )
        
        # Register tools
        self._sources[source_id] = []
        for tool in tools:
            self._tools[tool.tool_id] = tool
            self._sources[source_id].append(tool.tool_id)
        
        # Persist
        self._save_registry()
        
        logger.info(f"Added source {source_id} with {len(tools)} tools")
        return tools
    
    def remove_source(self, source_id: str):
        """Remove all tools for a documentation source."""
        if source_id in self._sources:
            for tool_id in self._sources[source_id]:
                self._tools.pop(tool_id, None)
            self._sources.pop(source_id)
            self._save_registry()
    
    def get_tool(self, tool_id: str) -> GeneratedTool | None:
        """Get a tool by ID."""
        return self._tools.get(tool_id)
    
    def get_all_tools(self) -> list[GeneratedTool]:
        """Get all registered tools."""
        return list(self._tools.values())
    
    def get_source_tools(self, source_id: str) -> list[GeneratedTool]:
        """Get all tools for a specific source."""
        tool_ids = self._sources.get(source_id, [])
        return [self._tools[tid] for tid in tool_ids if tid in self._tools]
    
    def list_sources(self) -> dict[str, int]:
        """List all sources and their tool counts."""
        return {sid: len(tids) for sid, tids in self._sources.items()}
    
    async def get_tool_content(self, tool_id: str) -> str | None:
        """
        Get content for a tool (fetches lazily if not cached).
        
        Args:
            tool_id: The tool ID
            
        Returns:
            The documentation content or None
        """
        tool = self._tools.get(tool_id)
        if not tool:
            return None
        
        # Check cache first
        cached = self._content_cache.get(tool.url)
        if cached:
            logger.debug(f"Cache hit for {tool_id}")
            return cached
        
        # Fetch content
        logger.info(f"Fetching content for {tool_id}: {tool.url}")
        try:
            result = await self._fetcher.fetch_with_links(tool.url)
            content = result.get("content", "")
            
            if content:
                # Cache the content
                self._content_cache.set(tool.url, content)
                return content
        except Exception as e:
            logger.error(f"Failed to fetch content for {tool_id}: {e}")
        
        return None
    
    def to_mcp_tools(self) -> list[dict[str, Any]]:
        """Convert all tools to MCP tool definitions."""
        return [tool.to_mcp_tool() for tool in self._tools.values()]
    
    def search_tools(self, query: str, limit: int = 10) -> list[GeneratedTool]:
        """
        Search tools by query (keyword matching).
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            Matching tools sorted by relevance
        """
        query_words = set(query.lower().split())
        
        scored = []
        for tool in self._tools.values():
            # Score based on keyword matches
            tool_keywords = set(tool.keywords)
            name_words = set(tool.name.lower().split())
            
            # Check matches
            keyword_matches = len(query_words & tool_keywords)
            name_matches = len(query_words & name_words)
            
            # Exact match in tool_id
            id_match = 1 if any(w in tool.tool_id for w in query_words) else 0
            
            score = keyword_matches * 2 + name_matches * 3 + id_match * 5
            
            if score > 0:
                scored.append((score, tool))
        
        # Sort by score descending
        scored.sort(key=lambda x: -x[0])
        
        return [t for _, t in scored[:limit]]


# Global registry instance
_registry: ToolRegistry | None = None


def get_registry(cache_dir: str = "./.doc2mcp_cache") -> ToolRegistry:
    """Get or create the global tool registry."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry(cache_dir=cache_dir)
    return _registry
