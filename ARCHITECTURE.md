# Architecture

## Structure

```
doc2mcp/
├── agents/          # Search agents
│   └── doc_search.py    - Deep research agent using Gemini
├── fetchers/        # Content fetchers
│   ├── web.py          - Web scraping (Jina Reader)
│   └── local.py        - Local file reader
├── tracing/         # Observability
│   └── phoenix.py      - Phoenix tracing setup
├── cache.py         # Page caching
├── config.py        # YAML config loader
├── handlers.py      # MCP tool handlers
└── server.py        # MCP server entry point
```

## Flow

1. **Server** (`server.py`) starts and loads config from `tools.yaml`
2. **Agent** (`doc_search.py`) initializes with tool configs
3. User calls `search_docs` via MCP client
4. **Handler** (`handlers.py`) processes the request
5. **Agent** fetches docs using **Fetchers** (web/local)
6. **Cache** stores pages to avoid re-fetching
7. **Gemini** analyzes content and navigates docs
8. Response returned to user
9. **Phoenix** traces everything for debugging

## Key Components

### DocSearchAgent
- Iteratively explores documentation
- Uses Gemini for navigation decisions
- Caches pages with summaries
- Synthesizes final answer

### Fetchers
- **WebFetcher**: Uses Jina Reader for JS-rendered pages
- **LocalFetcher**: Reads local markdown/txt files

### Cache
- JSON file-based storage
- Stores page content and summaries
- Reduces API calls

## Configuration

`tools.yaml`:
```yaml
tools:
  tool_id:
    name: "Tool Name"
    description: "What it does"
    sources:
      - type: web
        url: "https://..."
      - type: local
        path: "./docs"
```
