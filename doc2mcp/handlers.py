"""Tool handlers for MCP server."""

from mcp.types import TextContent

from doc2mcp.agents.doc_search import DocSearchAgent


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


async def handle_list_tools(agent: DocSearchAgent) -> list[TextContent]:
    """Handle list_available_tools tool call."""
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
