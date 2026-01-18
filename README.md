# Doc2MCP

An MCP (Model Context Protocol) server that provides tool documentation to AI agents via intelligent search.

When an agent needs documentation for a tool, it calls Doc2MCP with a search query and tool name. The server fetches documentation from configured sources (web or local files) and uses a background Gemini 2.5 Flash agent to extract the most relevant content.

## Features

- **MCP Server**: Standard MCP interface for easy integration with Claude, VS Code, and other MCP clients
- **Multi-source Documentation**: Supports web scraping and local file sources
- **Intelligent Search**: Uses Gemini 2.5 Flash to extract relevant documentation based on your query
- **Arize Phoenix Integration**: Full LLM tracing for observability and debugging
- **YAML Configuration**: Simple configuration file to register tools and their doc sources

## Quick Start

```bash
pip install doc2mcp
```

Or install from source:

```bash
git clone https://github.com/yourusername/doc2mcp.git
cd doc2mcp
pip install -e .
```

## Configuration

### 1. Set up environment variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required:
- `GOOGLE_API_KEY`: Your Google API key for Gemini

Optional (for cloud Phoenix):
- `PHOENIX_API_KEY`: Arize Phoenix API key
- `PHOENIX_COLLECTOR_ENDPOINT`: Phoenix endpoint URL

### 2. Configure tools

Edit `tools.yaml` to register tools and their documentation sources:

```yaml
tools:
  anthropic:
    name: "Anthropic Claude API"
    description: "Claude AI assistant API documentation"
    sources:
      - type: web
        url: "https://docs.anthropic.com/en/api"
        selectors:
          content: "main, article"
          exclude: "nav, footer"

  my_internal_tool:
    name: "My Internal Tool"
    description: "Internal tool documentation"
    sources:
      - type: local
        path: "./docs/my_tool"
        patterns:
          - "*.md"
          - "**/*.txt"

settings:
  max_content_length: 50000
  cache_ttl: 3600
  request_timeout: 30
```

## Usage

### Running the server

```bash
# Run directly
doc2mcp

# Or with Python
python -m doc2mcp.server
```

### Configuring MCP clients

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "doc2mcp": {
      "command": "doc2mcp",
      "env": {
        "GOOGLE_API_KEY": "your-key-here"
      }
    }
  }
}
```

Or for VS Code, add to your settings:

```json
{
  "mcp.servers": {
    "doc2mcp": {
      "command": "doc2mcp"
    }
  }
}
```

### Available Tools

The MCP server exposes two tools:

#### `search_docs`

Search documentation for a specific tool.

```json
{
  "tool_name": "anthropic",
  "query": "How do I use the messages API with streaming?"
}
```

#### `list_available_tools`

List all tools with available documentation.

```json
{}
```

## Observability with Arize Phoenix

Doc2MCP integrates with Arize Phoenix for full LLM tracing. This lets you:

- See exactly which documentation sources were used
- Track token usage and latency
- Debug unexpected responses
- Audit the search agent's reasoning

### Local Phoenix

By default, Doc2MCP starts a local Phoenix instance. Access the UI at `http://localhost:6006` after starting the server.

### Cloud Phoenix

To use Arize's hosted Phoenix:

1. Get an API key from [Arize](https://arize.com)
2. Set environment variables:
   ```bash
   export PHOENIX_API_KEY=your-key
   export PHOENIX_COLLECTOR_ENDPOINT=https://app.phoenix.arize.com
   ```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
ruff format .

# Lint
ruff check .

# Type check
mypy doc2mcp
```

## License

MIT License - see [LICENSE](LICENSE) for details.
