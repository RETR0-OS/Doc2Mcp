# Doc2MCP

🤖 An **agentic MCP server** that intelligently converts ANY documentation into callable tools using Google Gemini AI. No hard-coded parsers - the AI figures it out!

## Features

- 🧠 **AI-Powered**: Uses Gemini 2.0 Flash to intelligently understand documentation
- 🌐 **Universal**: Works with REST APIs, GraphQL, libraries, frameworks - any web documentation
- 🔄 **Auto-Discovery**: Intelligently finds and scrapes related documentation pages
- 🛠️ **Smart Tools**: Generates meaningful MCP tools with proper schemas automatically
- 📊 **Arize Phoenix Observability**: Full OpenTelemetry tracing with tool execution tracking
- ⚡ **Production Ready**: Error handling, logging, and full tracing support

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set your API key and documentation URL
export GEMINI_API_KEY="your-gemini-api-key"
export DOC_URLS="https://jsonplaceholder.typicode.com/"

# Run the server
python3 src/python/server.py
```

## How It Works

1. **Scrape** 📡 - Fetches documentation pages using BeautifulSoup
2. **Discover** 🔍 - Finds related documentation pages automatically
3. **Analyze** 🧠 - Gemini understands API structure and purpose
4. **Extract** 🔧 - AI identifies endpoints, functions, and parameters
5. **Generate** 🛠️ - Creates MCP tools with proper input schemas
6. **Execute** ⚡ - Tools make real API calls or provide documentation info

## Examples

### JSONPlaceholder API
Successfully generated 14 tools including:
- `get_posts` - Retrieve all posts
- `get_post_by_id` - Get specific post
- `create_post` - Create new post
- `update_post` - Update post
- And more!

### Any Documentation
Works with:
- REST APIs (any format)
- GraphQL APIs
- JavaScript libraries (React, Vue, etc.)
- Python frameworks (FastAPI, Flask, etc.)
- Any web-based API documentation

## VS Code Integration

Add to your MCP client configuration (e.g., Claude Desktop or VS Code):

```json
{
  "mcpServers": {
    "doc2mcp": {
      "command": "python3",
      "args": ["/path/to/doc2mcp/src/python/server.py"],
      "env": {
        "DOC_URLS": "https://petstore.swagger.io/v2/swagger.json"
      }
    }
  }
}
```

### Configuration

The server uses environment variables for configuration:

- `DOC_URLS`: Comma-separated list of OpenAPI/Swagger spec URLs
- Phoenix endpoint is automatically set to `http://localhost:6006/v1/traces`

## Supported Documentation Formats

### OpenAPI 3.0

```yaml
openapi: 3.0.0
info:
  title: Sample API
  version: 1.0.0
servers:
  - url: https://api.example.com
paths:
  /users:
    get:
      summary: List users
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
      responses:
        '200':
          description: Success
```

### Swagger 2.0

```yaml
swagger: '2.0'
info:
  title: Sample API
  version: 1.0.0
host: api.example.com
schemes:
  - https
paths:
  /users:
    get:
      summary: List users
      parameters:
        - name: limit
          in: query
          type: integer
```

## Observability with Arize Phoenix

Doc2MCP integrates with Arize Phoenix for comprehensive observability:

### Tracing Features

- **Tool Execution Spans**: Every tool call creates a span with full context
- **Tool Metadata**: Tracks tool name, arguments, and execution details
- **Error Tracking**: Automatic error recording and exception tracking
- **Performance Metrics**: Request duration and HTTP status codes

### Span Attributes

Each tool execution includes:

- `tool.name`: MCP tool name
- `tool.args`: Input arguments (JSON)
- `http.url`: Full API request URL
- `http.method`: HTTP method (GET, POST, etc.)
- `http.status_code`: Response status code
- Error information (if any)

### Running Arize Phoenix

```bash
# Using Docker
docker run -p 6006:6006 -p 4317:4317 arizephoenix/phoenix:latest

# Visit the UI
open http://localhost:6006
```

The server automatically sends traces to `http://localhost:6006/v1/traces`.

## Tool Generation

Doc2MCP automatically generates tools from OpenAPI operations:

### Schema Conversion

- OpenAPI parameters → MCP input schema properties
- Path parameters: required string fields
- Query parameters: optional fields with appropriate types
- Request body: structured as nested objects

### Tool Metadata

Each tool includes:
- Name (from operationId or auto-generated)
- Description (from operation summary/description)
- Input schema (converted from OpenAPI parameters)
- Handler function (executes HTTP request)

### Example Tool

For an endpoint `GET /pet/{petId}`:

```json
{
  "name": "getUsers",
  "description": "Retrieves user information",
  "inputSchema": {
    "type": "object",
    "properties": {
      "userId": { "type": "string", "description": "User ID" }
    },
    "required": ["userId"]
  }
}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DOC_URLS` | Comma-separated documentation URLs | `[]` |
| `TRACING_ENABLED` | Enable OpenTelemetry tracing | `true` |
| `ARIZE_ENDPOINT` | Arize Phoenix endpoint URL | `http://localhost:6006/v1/traces` |
| `ARIZE_API_KEY` | Arize API key (if required) | - |

## Error Handling

Doc2MCP includes comprehensive error handling:

- **Network Errors**: Timeouts, connection failures when fetching specs
- **Parsing Errors**: Invalid OpenAPI/Swagger formats
- **API Errors**: HTTP errors from target APIs
- **Validation Errors**: Missing required parameters

All errors are:
- Logged to stderr
- Tracked in OpenTelemetry spans with error attributes
- Returned as structured error responses to the MCP client

## Project Structure

```
doc2mcp/
├── src/
│   └── python/
│       ├── openapi_parser.py  # OpenAPI/Swagger parser
│       └── server.py           # MCP server with tracing
├── requirements.txt            # Python dependencies
├── .env                       # Environment configuration
└── README.md
```

## Development

### Requirements

- Python 3.8+
- pip

### Setup
npm run lint
```

### Formatting

```bash
npm run format
```

### Testing

```bash
npm test
```

## Deployment Options

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python src/python/server.py
```

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/python ./src/python
ENV DOC_URLS="https://petstore.swagger.io/v2/swagger.json"
CMD ["python", "src/python/server.py"]
```

### systemd Service

```ini
[Unit]
Description=Doc2MCP Server
After=network.target

[Service]
Type=simple
User=doc2mcp
WorkingDirectory=/opt/doc2mcp
ExecStart=/usr/bin/python3 /opt/doc2mcp/src/python/server.py
Environment="DOC_URLS=https://api.example.com/openapi.json"
Restart=always

[Install]
WantedBy=multi-user.target
```

## Examples

### Petstore API

```bash
export DOC_URLS="https://petstore.swagger.io/v2/swagger.json"
python src/python/server.py
```

Generated tools:
- `getPetById` - Find pet by ID
- `addPet` - Add a new pet to the store
- `updatePet` - Update an existing pet
- `deletePet` - Deletes a pet
- `getInventory` - Returns pet inventories by status
- `getUserByName` - Get user by username
- And more...

### Multiple OpenAPI Specs

```bash
export DOC_URLS="https://api1.example.com/openapi.json,https://api2.example.com/swagger.json"
python src/python/server.py
```

## Limitations

- Currently supports OpenAPI/Swagger specifications only
- Authentication/authorization must be handled by the API itself
- Large specifications may increase server startup time
- Request bodies are currently basic object conversions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with different OpenAPI specifications
5. Submit a pull request

## License

MIT

## Support

For issues and feature requests, please use the GitHub issue tracker.

## Acknowledgments

- Built with [MCP SDK (Python)](https://github.com/modelcontextprotocol/python-sdk)
- Observability by [Arize Phoenix](https://phoenix.arize.com/)
- OpenTelemetry for tracing
- Schema validation with [Zod](https://zod.dev/)
- OpenAPI parsing with [yaml](https://www.npmjs.com/package/yaml)
- HTML parsing with [cheerio](https://cheerio.js.org/)
- Markdown parsing with [marked](https://marked.js.org/)