#!/usr/bin/env python3
"""
Doc2MCP - Agentic MCP server that intelligently converts any documentation to callable tools using Gemini LLM
"""
import os
import json
import sys
import asyncio
from typing import Any, Sequence
from pathlib import Path

import httpx
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from doc_scraper import DocScraper
from agentic_parser import AgenticParser


class Doc2MCPServer:
    """Agentic MCP Server with Gemini-powered documentation parsing and Phoenix tracing"""
    
    def __init__(self, gemini_api_key: str):
        self.server = Server("doc2mcp")
        self.gemini_api_key = gemini_api_key
        self.scraper = DocScraper(gemini_api_key)
        self.parser = AgenticParser(gemini_api_key)
        self.tools = []
        self.doc_analysis = {}
        self.tracer = None
        
        # Initialize tracing
        self._setup_tracing()
        
    def _setup_tracing(self):
        """Setup OpenTelemetry tracing for Phoenix"""
        print("[MCP] 🔧 Setting up OpenTelemetry tracing...", file=sys.stderr)
        
        resource = Resource(attributes={
            "service.name": "doc2mcp",
            "service.version": "1.0.0"
        })
        
        provider = TracerProvider(resource=resource)
        
        # OTLP exporter for Phoenix
        phoenix_endpoint = "http://localhost:6006/v1/traces"
        print(f"[MCP] 🔗 Configuring Phoenix endpoint: {phoenix_endpoint}", file=sys.stderr)
        otlp_exporter = OTLPSpanExporter(
            endpoint=phoenix_endpoint
        )
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        
        # Console exporter for debugging
        console_exporter = ConsoleSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(console_exporter))
        
        trace.set_tracer_provider(provider)
        self.tracer = trace.get_tracer(__name__)
        
        print("[MCP] ✅ OpenTelemetry tracing initialized", file=sys.stderr)
        print("[MCP] 📊 Traces will be sent to Phoenix at http://localhost:6006", file=sys.stderr)
        
    async def initialize(self, doc_url: str):
        """Intelligently scrape and parse any documentation using Gemini"""
        with self.tracer.start_as_current_span("doc2mcp.initialize") as span:
            span.set_attribute("doc.url", doc_url)
            print(f"[MCP] 🚀 Starting initialization for: {doc_url}", file=sys.stderr)
            print(f"[TRACE] Span ID: {span.get_span_context().span_id}", file=sys.stderr)
            
            # Scrape documentation pages - more for comprehensive coverage
            print(f"[MCP] 📥 Beginning page discovery (max: 25 pages)...", file=sys.stderr)
            pages = await self.scraper.discover_related_pages(doc_url, max_pages=25)
            
            if not pages:
                print("[MCP] ⚠️  Warning: No pages scraped, attempting single page fallback", file=sys.stderr)
                span.add_event("fallback_to_single_page")
                page = await self.scraper.scrape_url(doc_url)
                pages = [page] if page.get('content') else []
            
            if not pages:
                span.set_attribute("error", True)
                print("[MCP] ❌ Failed to scrape any documentation pages", file=sys.stderr)
                raise Exception("Failed to scrape any documentation pages")
            
            span.set_attribute("pages.count", len(pages))
            print(f"[MCP] ✅ Successfully scraped {len(pages)} pages", file=sys.stderr)
            
            # Analyze documentation structure
            print(f"[MCP] 🔍 Analyzing documentation structure with Gemini...", file=sys.stderr)
            self.doc_analysis = await self.parser.analyze_documentation(pages)
            span.set_attribute("doc.type", self.doc_analysis.get('documentation_type', 'unknown'))
            span.set_attribute("doc.name", self.doc_analysis.get('api_name', 'unknown'))
            print(f"[MCP] 📊 Documentation Type: {self.doc_analysis.get('documentation_type', 'unknown')}", file=sys.stderr)
            print(f"[MCP] 📚 API Name: {self.doc_analysis.get('api_name', 'unknown')}", file=sys.stderr)
            
            # Generate tools from documentation
            print(f"[MCP] 🔧 Generating MCP tools from documentation...", file=sys.stderr)
            self.tools = await self.parser.create_tools_from_pages(pages, self.doc_analysis)
            span.set_attribute("tools.count", len(self.tools))
            
            print(f"[MCP] ✨ Successfully generated {len(self.tools)} tools", file=sys.stderr)
            span.add_event("initialization_complete", {
                "pages": len(pages),
                "tools": len(self.tools),
                "doc_type": self.doc_analysis.get('documentation_type', 'unknown')
            })
        
    async def list_tools_handler(self) -> list[Tool]:
        """List all available tools"""
        with self.tracer.start_as_current_span("doc2mcp.list_tools") as span:
            span.set_attribute("tools.total", len(self.tools))
            print(f"[MCP] 📋 Listing {len(self.tools)} available tools", file=sys.stderr)
            
            mcp_tools = []
            for i, tool_dict in enumerate(self.tools, 1):
                try:
                    mcp_tool = self._tool_dict_to_mcp_tool(tool_dict)
                    mcp_tools.append(mcp_tool)
                    print(f"[MCP]   {i}. {tool_dict.get('name', 'unknown')} - {tool_dict.get('method', 'N/A')}", file=sys.stderr)
                except Exception as e:
                    print(f"[ERROR] ❌ Failed to create tool #{i} ({tool_dict.get('name', 'unknown')}): {e}", file=sys.stderr)
                    span.add_event("tool_creation_failed", {"tool_name": tool_dict.get('name', 'unknown'), "error": str(e)})
            
            span.set_attribute("tools.created", len(mcp_tools))
            print(f"[MCP] ✅ Successfully created {len(mcp_tools)} MCP tools", file=sys.stderr)
            return mcp_tools
    
    def _tool_dict_to_mcp_tool(self, tool_dict: dict) -> Tool:
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
        
    async def call_tool_handler(self, name: str, arguments: Any) -> Sequence[TextContent]:
        """Execute a tool with Phoenix tracing and Gemini assistance"""
        
        with self.tracer.start_as_current_span(f"mcp.tool.{name}") as span:
            span.set_attribute("tool.name", name)
            span.set_attribute("tool.args", json.dumps(arguments))
            
            print(f"[MCP] 🔨 Tool invoked: {name}", file=sys.stderr)
            print(f"[MCP] 📝 Arguments: {json.dumps(arguments, indent=2)}", file=sys.stderr)
            print(f"[TRACE] 🔗 Span ID: {span.get_span_context().span_id}", file=sys.stderr)
            span.add_event("tool_invocation_started", {"tool": name, "args": json.dumps(arguments)})
            
            try:
                # Find matching tool
                print(f"[MCP] 🔍 Searching for tool definition: {name}", file=sys.stderr)
                tool = self._find_tool(name)
                if not tool:
                    print(f"[MCP] ❌ Tool not found: {name}", file=sys.stderr)
                    span.set_attribute("error", True)
                    span.set_attribute("error.type", "tool_not_found")
                    raise ValueError(f"Unknown tool: {name}")
                
                print(f"[MCP] ✅ Found tool: {tool.get('name')} (method: {tool.get('method', 'UNKNOWN')})", file=sys.stderr)
                span.set_attribute("tool.method", tool.get('method', 'UNKNOWN'))
                span.set_attribute("tool.path", tool.get('path', ''))
                span.set_attribute("tool.url", tool.get('url', ''))
                span.set_attribute("tool.url", tool.get('url', ''))
                
                # For REST APIs, try to execute the request
                if tool.get('method') in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    print(f"[MCP] 🌐 Executing REST API call: {tool.get('method')} {tool.get('path', '')}", file=sys.stderr)
                    span.add_event("executing_api_call")
                    result = await self._execute_api_call(tool, arguments, span)
                else:
                    # For library functions or unclear docs, use Gemini to generate response
                    print(f"[MCP] 🤖 Generating response with Gemini for: {tool.get('name')}", file=sys.stderr)
                    span.add_event("executing_with_gemini")
                    result = await self._execute_with_gemini(tool, arguments)
                
                print(f"[MCP] ✅ Tool execution successful: {name}", file=sys.stderr)
                print(f"[MCP] 📤 Result size: {len(json.dumps(result))} bytes", file=sys.stderr)
                span.add_event("tool_execution_complete", {"result_size": len(json.dumps(result))})
                span.set_attribute("success", True)
                
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
                    
            except Exception as e:
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                span.set_attribute("error.type", type(e).__name__)
                print(f"[ERROR] ❌ Tool execution failed for '{name}': {e}", file=sys.stderr)
                span.add_event("tool_execution_failed", {"error": str(e)})
                
                # Return error info instead of raising
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": str(e),
                        "tool": name,
                        "documentation_url": tool.get('url', '') if tool else ''
                    }, indent=2)
                )]
    
    def _find_tool(self, tool_name: str) -> dict:
        """Find tool by name"""
        for tool in self.tools:
            if tool.get('name', '').replace('-', '_').replace('.', '_') == tool_name:
                return tool
        return None
    
    async def _execute_api_call(self, tool: dict, arguments: Any, span) -> dict:
        """Execute an API call for REST endpoints"""
        method = tool['method']
        path = tool.get('path', '')
        base_url = self.doc_analysis.get('base_url', '')
        
        # Replace path parameters
        for key, value in arguments.items():
            path = path.replace(f"{{{key}}}", str(value))
            path = path.replace(f"{{{{{key}}}}}", str(value))
        
        # Build full URL
        if base_url:
            url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
        else:
            # No base URL, return documentation reference
            return {
                "message": "API endpoint identified but base URL not available",
                "method": method,
                "path": path,
                "parameters": arguments,
                "documentation": tool.get('url', ''),
                "description": tool.get('description', '')
            }
        
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
        """Use Gemini to provide information about the tool"""
        prompt = f"""Based on this documentation tool and user arguments, provide helpful information:

Tool: {tool.get('name')}
Description: {tool.get('description')}
Documentation URL: {tool.get('url')}
User Arguments: {json.dumps(arguments)}

Provide a helpful response about what this tool does and how to use it based on the documentation.
Be specific and reference the documentation URL for more details."""

        try:
            response = self.parser.client.models.generate_content(
                model=self.parser.model,
                contents=prompt
            )
            return {
                "response": response.text,
                "tool": tool.get('name'),
                "documentation_url": tool.get('url'),
                "note": "This response is generated from documentation analysis"
            }
        except Exception as e:
            return {
                "error": f"Could not generate response: {str(e)}",
                "documentation_url": tool.get('url'),
                "description": tool.get('description', '')
            }
        
    def setup_handlers(self):
        """Setup MCP handlers"""
        @self.server.list_tools()
        async def list_tools():
            return await self.list_tools_handler()
            
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any):
            return await self.call_tool_handler(name, arguments)
            
    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point"""
    # Print startup banner
    print("=" * 70, file=sys.stderr)
    print("🚀 Doc2MCP Agentic Server", file=sys.stderr)
    print("   Convert any documentation into callable MCP tools", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    
    # Get Gemini API key
    gemini_api_key = os.getenv("GEMINI_API_KEY", "AIzaSyCsPEUfryC5h-ISb3Zv9G9BzfjExSrtfF0")
    
    # Get documentation URL from environment
    doc_url = os.getenv("DOC_URLS")
    
    if not doc_url:
        print("[MCP] ❌ ERROR: DOC_URLS environment variable is required", file=sys.stderr)
        print("[MCP] 💡 Example: export DOC_URLS='https://api.example.com/docs'", file=sys.stderr)
        sys.exit(1)
    
    print(f"[MCP] 📖 Documentation URL: {doc_url}", file=sys.stderr)
    print(f"[MCP] 🤖 AI Model: Gemini 2.0 Flash", file=sys.stderr)
    print(f"[MCP] 📡 Observability: Phoenix (http://localhost:6006)", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    
    # Create and initialize server
    print("[MCP] 🔄 Initializing server...", file=sys.stderr)
    server = Doc2MCPServer(gemini_api_key)
    await server.initialize(doc_url)
    server.setup_handlers()
    
    print("=" * 70, file=sys.stderr)
    print("[MCP] ✅ Server ready! Listening for tool calls...", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    
    # Run server
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
