"""Doc2MCP - MCP server for tool documentation search.

This server exposes tools for AI agents to search documentation
for various tools and APIs.
"""

import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from doc2mcp.agents.doc_search import DocSearchAgent
from doc2mcp.config import load_config
from doc2mcp.tracing.phoenix import init_tracing

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("doc2mcp")

# Create MCP server instance
server = Server("doc2mcp")

# Global agent instance (initialized on startup)
_agent: DocSearchAgent | None = None


def get_agent() -> DocSearchAgent:
    """Get the doc search agent instance."""
    if _agent is None:
        raise RuntimeError("Agent not initialized")
    return _agent


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="search_docs",
            description=(
                "Search documentation for a specific tool or API. "
                "Returns relevant documentation content based on your query."
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
        ),
        Tool(
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
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls from MCP clients."""
    agent = get_agent()

    if name == "search_docs":
        tool_name = arguments.get("tool_name", "")
        query = arguments.get("query", "")

        if not tool_name or not query:
            return [
                TextContent(
                    type="text",
                    text="Error: Both 'tool_name' and 'query' are required.",
                )
            ]

        logger.info(f"Searching docs for '{tool_name}': {query}")
        result = await agent.search(tool_name=tool_name, query=query)

        if result.get("error"):
            error_msg = result["error"]
            if result.get("available_tools"):
                error_msg += f"\nAvailable tools: {', '.join(result['available_tools'])}"
            return [TextContent(type="text", text=f"Error: {error_msg}")]

        # Format response
        tool_info = result.get("tool", {})
        sources = result.get("sources", [])
        content = result.get("content", "No content found.")
        pages_explored = result.get("pages_explored", 0)

        response_text = f"""# Documentation: {tool_info.get('name', tool_name)}

{tool_info.get('description', '')}

## Relevant Documentation

{content}

---
**Sources:** {', '.join(sources)}
**Pages explored:** {pages_explored}
"""
        return [TextContent(type="text", text=response_text)]

    elif name == "list_available_tools":
        tools = await agent.list_tools()

        if not tools:
            return [
                TextContent(
                    type="text",
                    text="No tools configured. Add tools to tools.yaml to get started.",
                )
            ]

        lines = ["# Available Tools\n"]
        for tool in tools:
            lines.append(f"- **{tool['id']}**: {tool['name']}")
            lines.append(f"  {tool['description']}\n")

        return [TextContent(type="text", text="\n".join(lines))]

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def run_server() -> None:
    """Run the MCP server."""
    global _agent

    # Initialize tracing
    logger.info("Initializing Arize Phoenix tracing...")
    init_tracing("doc2mcp")

    # Load configuration
    config_path = os.environ.get("TOOLS_CONFIG_PATH")
    if config_path:
        logger.info(f"Loading config from: {config_path}")
    else:
        # Look for tools.yaml in current dir or package dir
        default_paths = [
            Path("./tools.yaml"),
            Path(__file__).parent.parent / "tools.yaml",
        ]
        for path in default_paths:
            if path.exists():
                config_path = str(path)
                break

    config = load_config(config_path)
    logger.info(f"Loaded {len(config.tools)} tools from config")

    # Initialize agent
    _agent = DocSearchAgent(config)
    logger.info("Doc search agent initialized")

    # Run the stdio server
    logger.info("Starting Doc2MCP server...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )

    # Cleanup
    await _agent.close()


def main() -> None:
    """Entry point for the server."""
    # Load environment variables from .env files
    # Try .env.local first, then .env
    env_local = Path(".env.local")
    env_file = Path(".env")

    if env_local.exists():
        load_dotenv(env_local)
    elif env_file.exists():
        load_dotenv(env_file)

    asyncio.run(run_server())


if __name__ == "__main__":
    main()
