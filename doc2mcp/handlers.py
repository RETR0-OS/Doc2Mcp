"""Tool handlers for MCP server."""

from mcp.types import TextContent

from doc2mcp.agents.doc_search import DocSearchAgent
from doc2mcp.indexer.registry import ToolRegistry


async def handle_search_docs(agent: DocSearchAgent, arguments: dict) -> list[TextContent]:
    """Handle search_docs tool call."""
    tool_name = arguments.get("tool_name", "")
    query = arguments.get("query", "")

    if not tool_name or not query:
        return [
            TextContent(
                type="text",
                text="Error: Both 'tool_name' and 'query' are required.",
            )
        ]

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


async def handle_list_tools(agent: DocSearchAgent, registry: ToolRegistry | None = None) -> list[TextContent]:
    """Handle list_available_tools tool call."""
    tools = await agent.list_tools()
    
    # Debug: log what we got
    import logging
    logger = logging.getLogger("doc2mcp.handlers")
    logger.info(f"handle_list_tools: config tools={len(tools) if tools else 0}, registry={registry is not None}")
    if registry:
        logger.info(f"handle_list_tools: registry tools={len(registry.get_all_tools())}")

    if not tools and (not registry or not registry.get_all_tools()):
        return [
            TextContent(
                type="text",
                text="No tools configured. Add tools to tools.yaml to get started.",
            )
        ]

    lines = ["# Available Tools\n"]
    
    # List tools from config
    if tools:
        lines.append("## Configured Tools\n")
        for tool in tools:
            lines.append(f"- **{tool['id']}**: {tool['name']}")
            lines.append(f"  {tool['description']}\n")
    
    # List auto-generated tools from registry
    if registry:
        registry_tools = registry.get_all_tools()
        if registry_tools:
            # Group by source
            by_source: dict[str, list] = {}
            for tool in registry_tools:
                source = tool.parent_source
                if source not in by_source:
                    by_source[source] = []
                by_source[source].append(tool)
            
            lines.append("\n## Auto-Generated Documentation Tools\n")
            for source, source_tools in by_source.items():
                lines.append(f"\n### {source} ({len(source_tools)} tools)\n")
                for tool in source_tools[:10]:  # Show first 10 per source
                    lines.append(f"- **{tool.tool_id}**: {tool.name}")
                if len(source_tools) > 10:
                    lines.append(f"  ... and {len(source_tools) - 10} more")

    return [TextContent(type="text", text="\n".join(lines))]
