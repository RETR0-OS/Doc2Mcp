"""Tool execution handlers for Doc2MCP"""
import json
import sys
from typing import Any, Dict, List, Sequence
import httpx
from mcp.types import Tool, TextContent


class ToolExecutor:
    """Handles tool creation and execution"""
    
    def __init__(self, parser, doc_analysis: Dict[str, Any], tracer):
        self.parser = parser
        self.doc_analysis = doc_analysis
        self.tracer = tracer
        self.tools = []
        
    def set_tools(self, tools: List[Dict[str, Any]]):
        """Set the available tools"""
        self.tools = tools
        
    def to_mcp_tool(self, tool_dict: dict) -> Tool:
        """Convert tool dictionary to MCP Tool"""
        name = tool_dict.get('name', 'unknown_tool')
        
        # Ensure valid tool name
        name = name.replace('-', '_').replace('.', '_').replace('/', '_')
        if not name or not name[0].isalpha():
            name = f"tool_{name}"
        
        description = tool_dict.get('description', '')
        if tool_dict.get('method'):
            description = f"[{tool_dict['method']}] {description}"
        if tool_dict.get('returns'):
            description += f"\nReturns: {tool_dict['returns']}"
        
        return Tool(
            name=name,
            description=description or "Documentation tool",
            inputSchema=tool_dict.get('input_schema', {'type': 'object', 'properties': {}})
        )
        
    def list_tools(self) -> list[Tool]:
        """Convert all tools to MCP format"""
        mcp_tools = []
        for i, tool_dict in enumerate(self.tools, 1):
            try:
                mcp_tool = self.to_mcp_tool(tool_dict)
                mcp_tools.append(mcp_tool)
                print(f"[TOOL]   {i}. {tool_dict.get('name', 'unknown')} - {tool_dict.get('method', 'N/A')}", file=sys.stderr)
            except Exception as e:
                print(f"[ERROR] ❌ Failed to create tool #{i}: {e}", file=sys.stderr)
        
        print(f"[TOOL] ✅ Created {len(mcp_tools)} MCP tools", file=sys.stderr)
        return mcp_tools
    
    def find_tool(self, tool_name: str) -> dict:
        """Find tool by name"""
        for tool in self.tools:
            if tool.get('name', '').replace('-', '_').replace('.', '_') == tool_name:
                return tool
        return None
    
    async def execute_tool(self, name: str, arguments: Any) -> Sequence[TextContent]:
        """Execute a tool with tracing"""
        with self.tracer.start_as_current_span(f"mcp.tool.{name}") as span:
            span.set_attribute("tool.name", name)
            span.set_attribute("tool.args", json.dumps(arguments))
            
            print(f"[TOOL] 🔨 Executing: {name}", file=sys.stderr)
            print(f"[TOOL] 📝 Arguments: {json.dumps(arguments, indent=2)}", file=sys.stderr)
            
            try:
                tool = self.find_tool(name)
                if not tool:
                    print(f"[TOOL] ❌ Tool not found: {name}", file=sys.stderr)
                    raise ValueError(f"Unknown tool: {name}")
                
                print(f"[TOOL] ✅ Found: {tool.get('name')} ({tool.get('method', 'UNKNOWN')})", file=sys.stderr)
                span.set_attribute("tool.method", tool.get('method', 'UNKNOWN'))
                
                # Execute based on method type
                if tool.get('method') in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    result = await self._execute_api_call(tool, arguments, span)
                else:
                    result = await self._execute_with_gemini(tool, arguments)
                
                print(f"[TOOL] ✅ Success: {len(json.dumps(result))} bytes", file=sys.stderr)
                span.set_attribute("success", True)
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
                    
            except Exception as e:
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                print(f"[ERROR] ❌ Execution failed: {e}", file=sys.stderr)
                
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": str(e),
                        "tool": name,
                        "documentation_url": tool.get('url', '') if tool else ''
                    }, indent=2)
                )]
    
    async def _execute_api_call(self, tool: dict, arguments: Any, span) -> dict:
        """Execute REST API call"""
        method = tool['method']
        path = tool.get('path', '')
        base_url = self.doc_analysis.get('base_url', '')
        
        # Replace path parameters
        for key, value in arguments.items():
            path = path.replace(f"{{{key}}}", str(value))
            path = path.replace(f"{{{{{key}}}}}", str(value))
        
        # Build URL
        if not base_url:
            return {
                "message": "API endpoint identified but base URL not available",
                "method": method,
                "path": path,
                "parameters": arguments,
                "documentation": tool.get('url', ''),
                "description": tool.get('description', '')
            }
        
        url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
        span.set_attribute("http.url", url)
        span.set_attribute("http.method", method)
        
        # Execute request
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                if method == "GET":
                    params = {k: v for k, v in arguments.items() if f"{{{k}}}" not in tool.get('path', '')}
                    response = await client.get(url, params=params)
                elif method in ["POST", "PUT", "PATCH"]:
                    body = {k: v for k, v in arguments.items() if f"{{{k}}}" not in tool.get('path', '')}
                    response = await client.request(method, url, json=body)
                else:
                    response = await client.request(method, url)
                
                span.set_attribute("http.status_code", response.status_code)
                
                try:
                    data = response.json()
                except:
                    data = response.text
                
                return {
                    "status": response.status_code,
                    "data": data,
                    "url": url,
                    "method": method
                }
                    
            except Exception as e:
                return {
                    "error": str(e),
                    "url": url,
                    "method": method,
                    "documentation": tool.get('url', '')
                }
    
    async def _execute_with_gemini(self, tool: dict, arguments: Any) -> dict:
        """Use Gemini for non-API tools"""
        prompt = f"""Based on this documentation tool and user arguments, provide helpful information:

Tool: {tool.get('name')}
Description: {tool.get('description')}
Documentation URL: {tool.get('url')}
User Arguments: {json.dumps(arguments)}

Provide a helpful response about what this tool does and how to use it."""

        try:
            response = self.parser.client.models.generate_content(
                model=self.parser.model,
                contents=prompt
            )
            return {
                "response": response.text,
                "tool": tool.get('name'),
                "documentation_url": tool.get('url'),
                "note": "Generated from documentation analysis"
            }
        except Exception as e:
            return {
                "error": f"Could not generate response: {str(e)}",
                "documentation_url": tool.get('url'),
                "description": tool.get('description', '')
            }
