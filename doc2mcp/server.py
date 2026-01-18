"""Doc2MCP - MCP server for tool documentation search."""

import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from doc2mcp.agents.doc_search import DocSearchAgent
from doc2mcp.config import load_config_with_fallback
from doc2mcp.handlers import handle_list_tools, handle_search_docs
from doc2mcp.indexer.registry import get_registry
from doc2mcp.tracing.phoenix import init_tracing, trace_mcp_call

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("doc2mcp")

server = Server("doc2mcp")
_agent: DocSearchAgent | None = None
_registry = None


def get_agent() -> DocSearchAgent:
    if _agent is None:
        raise RuntimeError("Agent not initialized")
    return _agent


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools - includes auto-generated granular tools."""
    tools = []
    
    # Add the meta tools for discovery and fallback search
    tools.append(Tool(
        name="search_docs",
        description=(
            "Search documentation for a specific tool or API. "
            "Use this for general queries when you don't know the exact page. "
            "For faster results, use the specific documentation tools listed below."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "description": (
                        "The name/ID of the tool to search documentation for. "
                        "Use 'list_available_tools' to see available tools."
                    ),
                },
                "query": {
                    "type": "string",
                    "description": (
                        "Your search query describing what information you need. "
                        "Be specific about what you're looking for."
                    ),
                },
            },
            "required": ["tool_name", "query"],
        },
    ))
    
    tools.append(Tool(
        name="list_available_tools",
        description=(
            "List all tools that have documentation available. "
            "Use this to discover what tools you can search documentation for."
        ),
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ))
    
    # Add auto-generated granular tools from registry
    if _registry:
        for gen_tool in _registry.get_all_tools():
            tools.append(Tool(
                name=gen_tool.tool_id,
                description=gen_tool.description,
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ))
    
    return tools


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls from MCP clients."""
    logger.info(f"call_tool: name={name}, _agent={_agent is not None}, _registry={_registry is not None}")
    agent = get_agent()

    if name == "search_docs":
        logger.info(f"Searching docs for '{arguments.get('tool_name')}': {arguments.get('query')}")
        return await handle_search_docs(agent, arguments)
    elif name == "list_available_tools":
        return await handle_list_tools(agent, _registry)
    elif _registry and _registry.get_tool(name):
        # Handle auto-generated tool call
        logger.info(f"Fetching documentation: {name}")
        content = await _registry.get_tool_content(name)
        if content:
            tool = _registry.get_tool(name)
            return [TextContent(
                type="text",
                text=f"# {tool.name}\n\nSource: {tool.url}\n\n{content}"
            )]
        else:
            return [TextContent(type="text", text=f"Failed to fetch documentation for {name}")]
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def run_server() -> None:
    """Run the MCP server."""
    global _agent, _registry

    init_tracing("doc2mcp")

    # Load config from API (with fallback to YAML file)
    config = await load_config_with_fallback()
    logger.info(f"Loaded {len(config.tools)} tools from config")

    _agent = DocSearchAgent(config)
    
    # Initialize tool registry and auto-generate tools from sources
    cache_dir = os.environ.get("DOC2MCP_CACHE_DIR", "./.doc2mcp_cache")
    _registry = get_registry(cache_dir)
    
    # Auto-index sources from config if not already indexed
    existing_sources = _registry.list_sources()
    logger.info(f"Existing cached sources: {list(existing_sources.keys())}")
    
    for tool_id, tool_config in config.tools.items():
        if tool_id in existing_sources:
            logger.info(f"Skipping {tool_id} - already indexed with {existing_sources[tool_id]} tools")
            continue
            
        for source in tool_config.sources:
            if source.type == "web" and source.url:
                logger.info(f"Indexing new source {tool_id} from {source.url}")
                try:
                    await _registry.add_source(tool_id, source.url)
                except Exception as e:
                    logger.warning(f"Failed to index {tool_id}: {e}")
                break  # Only index first web source
    
    total_tools = len(_registry.get_all_tools())
    logger.info(f"Registry has {total_tools} granular tools")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

    await _agent.close()


def main() -> None:
    """Entry point for the server."""
    for env_path in [Path(".env.local"), Path(".env")]:
        if env_path.exists():
            load_dotenv(env_path)
            break

    asyncio.run(run_server())


if __name__ == "__main__":
    main()
