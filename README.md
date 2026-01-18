# Doc2MCP

MCP server that provides intelligent documentation search to AI agents using Gemini.

## Install

```bash
pip install -e .
```

## Setup

1. Create `.env` with your API key:
```bash
GOOGLE_API_KEY=your-key-here
```

2. Configure tools in `tools.yaml`:
```yaml
tools:
  anthropic:
    name: "Anthropic Claude API"
    description: "Claude API documentation"
    sources:
      - type: web
        url: "https://docs.anthropic.com/en/api"
```

## Usage

Start server:
```bash
doc2mcp
```

Add to Claude Desktop config:
```json
{
  "mcpServers": {
    "doc2mcp": {
      "command": "doc2mcp",
      "env": {"GOOGLE_API_KEY": "your-key"}
    }
  }
}
```

## License

MIT
