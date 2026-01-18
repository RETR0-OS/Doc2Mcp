"""Tool generator that creates MCP tools from documentation pages."""

import hashlib
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from doc2mcp.indexer.sitemap_parser import PageInfo, SitemapParser

logger = logging.getLogger(__name__)


@dataclass
class GeneratedTool:
    """A generated MCP tool for a documentation page."""
    tool_id: str
    name: str
    description: str
    url: str
    keywords: list[str] = field(default_factory=list)
    parent_source: str = ""  # The original doc source ID
    content: str | None = None  # Lazy loaded
    
    def to_mcp_tool(self) -> dict[str, Any]:
        """Convert to MCP tool definition."""
        return {
            "name": self.tool_id,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }


class ToolGenerator:
    """Generate MCP tools from documentation sites."""
    
    def __init__(self, max_tools_per_source: int = 50):
        """
        Initialize generator.
        
        Args:
            max_tools_per_source: Maximum tools to generate per documentation source
        """
        self.max_tools = max_tools_per_source
    
    async def generate_from_url(self, source_id: str, base_url: str) -> list[GeneratedTool]:
        """
        Generate tools from a documentation URL.
        
        Args:
            source_id: Identifier for the documentation source (e.g., "react")
            base_url: The documentation base URL
            
        Returns:
            List of generated tools
        """
        parser = SitemapParser(base_url, max_pages=self.max_tools * 2)
        pages = await parser.parse()
        
        logger.info(f"Found {len(pages)} pages for {source_id}")
        
        tools = []
        seen_ids = set()
        
        for page in pages[:self.max_tools]:
            tool = self._page_to_tool(source_id, page)
            
            # Ensure unique IDs
            if tool.tool_id in seen_ids:
                tool.tool_id = f"{tool.tool_id}_{self._short_hash(page.url)}"
            seen_ids.add(tool.tool_id)
            
            tools.append(tool)
        
        logger.info(f"Generated {len(tools)} tools for {source_id}")
        return tools
    
    def _page_to_tool(self, source_id: str, page: PageInfo) -> GeneratedTool:
        """Convert a page info to a generated tool."""
        # Create tool ID from source + path
        path_id = self._path_to_id(page.path)
        tool_id = f"{source_id}_{path_id}" if path_id else source_id
        
        # Clean up the ID
        tool_id = re.sub(r'[^a-zA-Z0-9_]', '_', tool_id)
        tool_id = re.sub(r'_+', '_', tool_id).strip('_').lower()
        
        # Limit length
        if len(tool_id) > 64:
            tool_id = tool_id[:60] + self._short_hash(page.url)
        
        # Create description
        description = self._generate_description(page)
        
        return GeneratedTool(
            tool_id=tool_id,
            name=page.title,
            description=description,
            url=page.url,
            keywords=page.keywords,
            parent_source=source_id
        )
    
    def _path_to_id(self, path: str) -> str:
        """Convert URL path to a tool ID component."""
        # Remove common prefixes
        path = re.sub(r'^/(docs|api|reference|guide|en|v\d+|latest)/?', '', path)
        
        # Split and join
        segments = [s for s in path.split('/') if s]
        
        if not segments:
            return ""
        
        # Use last 2-3 meaningful segments
        meaningful = segments[-3:] if len(segments) > 2 else segments
        
        return '_'.join(meaningful)
    
    def _generate_description(self, page: PageInfo) -> str:
        """Generate a description for the tool."""
        desc = f"Documentation: {page.title}"
        
        if page.keywords:
            # Add top keywords
            top_keywords = page.keywords[:5]
            desc += f". Topics: {', '.join(top_keywords)}"
        
        return desc[:200]  # Limit length
    
    def _short_hash(self, text: str) -> str:
        """Generate a short hash for uniqueness."""
        return hashlib.md5(text.encode()).hexdigest()[:4]


async def index_documentation_source(
    source_id: str,
    base_url: str,
    max_tools: int = 50
) -> list[GeneratedTool]:
    """
    Index a documentation source and generate tools.
    
    Args:
        source_id: Identifier for the source
        base_url: Documentation base URL
        max_tools: Maximum number of tools to generate
        
    Returns:
        List of generated tools
    """
    generator = ToolGenerator(max_tools_per_source=max_tools)
    return await generator.generate_from_url(source_id, base_url)
