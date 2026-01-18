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
from doc2mcp.config import load_config
from doc2mcp.handlers import handle_list_tools, handle_search_docs
from doc2mcp.tracing.phoenix import init_tracing

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("doc2mcp")

server = Server("doc2mcp")
_agent: DocSearchAgent | None = None


def get_agent() -> DocSearchAgent:
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
        logger.info(f"Searching docs for '{arguments.get('tool_name')}': {arguments.get('query')}")
        return await handle_search_docs(agent, arguments)
    elif name == "list_available_tools":
        return await handle_list_tools(agent)
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def run_server() -> None:
    """Run the MCP server."""
    global _agent

    init_tracing("doc2mcp")

    # Find config file
    config_path = os.environ.get("TOOLS_CONFIG_PATH")
    if not config_path:
        for path in [Path("./tools.yaml"), Path(__file__).parent.parent / "tools.yaml"]:
            if path.exists():
                config_path = str(path)
                break

    config = load_config(config_path)
    logger.info(f"Loaded {len(config.tools)} tools")

    _agent = DocSearchAgent(config)

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
