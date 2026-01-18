#!/usr/bin/env python3
"""
Doc2MCP - Agentic MCP server that converts any documentation to callable tools using Gemini AI
"""
import sys
import asyncio
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from tracing import TracingManager
from doc_scraper import DocScraper
from agentic_parser import AgenticParser
from tool_executor import ToolExecutor


class Doc2MCPServer:
    """Agentic MCP Server with Gemini-powered documentation parsing"""
    
    def __init__(self, config: Config):
        self.config = config
        self.server = Server("doc2mcp")
        
        # Initialize components
        self.tracing = TracingManager(config.phoenix_endpoint)
        self.tracer = self.tracing.setup()
        
        self.scraper = DocScraper(config.gemini_api_key)
        self.parser = AgenticParser(config.gemini_api_key)
        self.executor = None
        self.doc_analysis = {}
        
    async def initialize(self, doc_url: str):
        """Scrape and parse documentation using Gemini"""
        with self.tracer.start_as_current_span("doc2mcp.initialize") as span:
            span.set_attribute("doc.url", doc_url)
            print(f"[MCP] 🚀 Initializing: {doc_url}", file=sys.stderr)
            
            # Scrape pages
            print(f"[MCP] 📥 Discovering pages (max: {self.config.max_pages})...", file=sys.stderr)
            pages = await self.scraper.discover_related_pages(doc_url, max_pages=self.config.max_pages)
            
            if not pages:
                print("[MCP] ⚠️  Attempting single page fallback", file=sys.stderr)
                page = await self.scraper.scrape_url(doc_url)
                pages = [page] if page.get('content') else []
            
            if not pages:
                raise Exception("Failed to scrape any documentation pages")
            
            print(f"[MCP] ✅ Scraped {len(pages)} pages", file=sys.stderr)
            span.set_attribute("pages.count", len(pages))
            
            # Analyze documentation
            print(f"[MCP] 🔍 Analyzing with Gemini...", file=sys.stderr)
            self.doc_analysis = await self.parser.analyze_documentation(pages)
            span.set_attribute("doc.type", self.doc_analysis.get('documentation_type', 'unknown'))
            span.set_attribute("doc.name", self.doc_analysis.get('api_name', 'unknown'))
            
            # Generate tools
            print(f"[MCP] 🔧 Generating tools...", file=sys.stderr)
            tools = await self.parser.create_tools_from_pages(pages, self.doc_analysis)
            
            # Initialize executor
            self.executor = ToolExecutor(self.parser, self.doc_analysis, self.tracer)
            self.executor.set_tools(tools)
            
            print(f"[MCP] ✨ Generated {len(tools)} tools", file=sys.stderr)
            span.set_attribute("tools.count", len(tools))
        
    def setup_handlers(self):
        """Setup MCP request handlers"""
        @self.server.list_tools()
        async def list_tools():
            return self.executor.list_tools()
            
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any):
            return await self.executor.execute_tool(name, arguments)
            
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
    print("=" * 70, file=sys.stderr)
    print("🚀 Doc2MCP Agentic Server", file=sys.stderr)
    print("   Convert any documentation into callable MCP tools", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    
    # Load configuration
    config = Config()
    
    if not config.validate():
        print("[MCP] ❌ ERROR: DOC_URLS environment variable is required", file=sys.stderr)
        print("[MCP] 💡 Example: export DOC_URLS='https://api.example.com/docs'", file=sys.stderr)
        sys.exit(1)
    
    print(f"[MCP] 📖 Documentation URL: {config.doc_urls}", file=sys.stderr)
    print(f"[MCP] 🤖 AI Model: {config.gemini_model}", file=sys.stderr)
    print(f"[MCP] 📡 Observability: Phoenix ({config.phoenix_endpoint})", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    
    # Create and initialize server
    print("[MCP] 🔄 Initializing server...", file=sys.stderr)
    server = Doc2MCPServer(config)
    await server.initialize(config.doc_urls)
    server.setup_handlers()
    
    print("=" * 70, file=sys.stderr)
    print("[MCP] ✅ Server ready! Listening for tool calls...", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    
    # Run server
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
