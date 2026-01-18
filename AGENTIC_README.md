# Doc2MCP - Agentic Documentation to MCP Tools

🤖 **Intelligently convert ANY documentation into callable MCP tools using Gemini AI**

## Overview

Doc2MCP is an **agentic MCP server** that uses Google's Gemini 2.0 Flash to intelligently scrape, analyze, and convert any API documentation (not just OpenAPI/Swagger) into functional MCP tools. No hard-coded parsers - the AI figures it out!

## Key Features

✨ **Agentic Intelligence**
- Uses Gemini LLM to understand documentation structure
- Automatically discovers related pages
- Extracts API endpoints and functions intelligently
- Generates meaningful tool names and descriptions

🌐 **Universal Documentation Support**
- REST APIs (any format, not just OpenAPI)
- GraphQL APIs
- Library documentation
- Framework documentation
- Any web-based documentation

📊 **Smart Context Management**
- Chunks large documentation to avoid context overflow
- Discovers and analyzes multiple related pages
- Intelligently extracts only relevant information

🔍 **Arize Phoenix Observability**
- Full OpenTelemetry tracing
- Track tool execution
- Monitor API calls and LLM interactions

## How It Works

```
1. 📡 Scrape → BeautifulSoup fetches documentation pages
2. 🔍 Discover → Intelligently finds related documentation pages
3. 🧠 Analyze → Gemini understands API structure and purpose
4. 🔧 Extract → AI identifies endpoints, functions, parameters
5. 🛠️ Generate → Creates MCP tools with proper schemas
6. ⚡ Execute → Tools can make real API calls or provide info
```

## Installation

```bash
# Clone the repository
cd /home/ash/projects/Doc2Mcp

# Install dependencies
pip install -r requirements.txt

# Set your Gemini API key
export GEMINI_API_KEY="your-api-key-here"

# Set documentation URL
export DOC_URLS="https://api.example.com/docs"

# Run the server
python3 src/python/server.py
```

## Configuration

### VS Code MCP Settings

Add to `~/.config/Code/User/mcp.json`:

```json
{
  "servers": {
    "doc2mcp": {
      "command": "python3",
      "args": ["/home/ash/projects/Doc2Mcp/src/python/server.py"],
      "env": {
        "DOC_URLS": "https://api.example.com/docs",
        "GEMINI_API_KEY": "your-gemini-api-key"
      },
      "type": "stdio"
    }
  }
}
```

### Environment Variables

- `DOC_URLS` (required): URL of the documentation to scrape
- `GEMINI_API_KEY` (optional): Your Gemini API key (default embedded)

## Examples

### JSONPlaceholder API
```bash
export DOC_URLS="https://jsonplaceholder.typicode.com/"
python3 src/python/server.py
```

Generated tools:
- `get_posts` - Retrieves all posts
- `get_post_by_id` - Get specific post
- `create_post` - Create new post
- `update_post` - Update existing post
- And more!

### Stripe API Documentation
```bash
export DOC_URLS="https://docs.stripe.com/api"
python3 src/python/server.py
```

### Any Framework Docs
```bash
export DOC_URLS="https://babylonjs.com/docs"
python3 src/python/server.py
```

## Architecture

### Components

1. **doc_scraper.py** - Web scraping with BeautifulSoup
   - Fetches HTML content
   - Cleans and extracts text
   - Discovers related pages
   - Chunks content for LLM processing

2. **agentic_parser.py** - Gemini-powered analysis
   - Analyzes documentation structure
   - Identifies API type (REST, GraphQL, library, etc.)
   - Extracts endpoints and functions
   - Generates tool schemas

3. **server.py** - MCP server implementation
   - Tool registration and management
   - Tool execution (API calls or info retrieval)
   - OpenTelemetry tracing
   - Error handling

### Tool Execution Flow

```python
# For REST APIs with base URL
1. Parse parameters
2. Build API request
3. Execute HTTP call
4. Return response

# For documentation-only (no executable API)
1. Use Gemini to provide information
2. Reference documentation URL
3. Return helpful guidance
```

## Advanced Usage

### Custom Documentation Scraping

```python
from doc_scraper import DocScraper

scraper = DocScraper(gemini_api_key)
pages = await scraper.discover_related_pages("https://api.example.com", max_pages=20)
```

### Intelligent Parsing

```python
from agentic_parser import AgenticParser

parser = AgenticParser(gemini_api_key)
analysis = await parser.analyze_documentation(pages)
tools = await parser.create_tools_from_pages(pages, analysis)
```

## Advantages Over Hard-Coded Parsers

| Hard-Coded OpenAPI Parser | Agentic AI Parser |
|--------------------------|-------------------|
| ❌ Only works with OpenAPI/Swagger | ✅ Works with ANY documentation |
| ❌ Breaks if spec format changes | ✅ Adapts to any format |
| ❌ Manual schema mapping | ✅ AI understands context |
| ❌ Limited to REST APIs | ✅ Supports GraphQL, libraries, etc. |
| ❌ Requires perfect spec | ✅ Works with incomplete docs |

## Limitations & Future Work

### Current Limitations
- Requires well-structured HTML documentation
- API execution needs base URL in docs
- Rate limited by Gemini API quota
- Best with English documentation

### Planned Features
- [ ] Multi-language documentation support
- [ ] GraphQL introspection
- [ ] WebSocket API support
- [ ] Automatic authentication handling
- [ ] Code example extraction
- [ ] Vector database for large docs
- [ ] Caching layer for repeated queries

## Troubleshooting

### No tools generated
- Check if documentation URL is accessible
- Verify GEMINI_API_KEY is valid
- Increase max_pages for more coverage
- Check logs for scraping errors

### API calls failing
- Verify base_url is correct in docs
- Check authentication requirements
- Review tool parameters

### Rate limiting
- Reduce max_pages parameter
- Implement caching (coming soon)
- Use exponential backoff

## Contributing

This is an experimental agentic system! Contributions welcome:

1. Test with different documentation types
2. Improve scraping heuristics
3. Enhance LLM prompts
4. Add support for new doc formats
5. Improve error handling

## License

MIT License - See LICENSE file

## Credits

- Built with [MCP SDK](https://github.com/modelcontextprotocol/python-sdk)
- Powered by [Google Gemini 2.0 Flash](https://ai.google.dev/)
- Observability with [Arize Phoenix](https://phoenix.arize.com/)

---

**Note**: This is an intelligent agent that adapts to documentation. Results may vary based on documentation quality and structure. Always verify generated tools before production use!
