# Doc2MCP

An MCP (Model Context Protocol) server that automatically converts API documentation URLs into callable tools with Arize Phoenix observability. Built with TypeScript, the MCP SDK, OpenTelemetry tracing, and Zod schema validation.

## Features

- 🔄 **Multi-Format Support**: Parses OpenAPI/Swagger, HTML, and Markdown documentation
- 🛠️ **Automatic Tool Generation**: Creates callable MCP tools from API endpoints
- 📊 **Arize Observability**: Full OpenTelemetry tracing with documentation lineage
- ✅ **Schema Validation**: Generates Zod schemas for runtime type safety
- 🎯 **Type-Safe**: Complete TypeScript implementation with strict typing
- ⚡ **Production Ready**: Error handling, logging, and deployment configurations

## Architecture

Doc2MCP follows a 5-phase implementation:

1. **Documentation Parsing**: Supports OpenAPI/Swagger (JSON/YAML), HTML, and Markdown
2. **Tool Generation**: Generates Zod schemas and creates callable tools
3. **Arize Integration**: OpenTelemetry tracing with source lineage tracking
4. **MCP Server**: MCP SDK-based server with stdio transport
5. **Testing & Deployment**: Comprehensive tests and deployment options

## Installation

```bash
npm install
npm run build
```

## Usage

### Running the Server

```bash
# Set documentation URLs
export DOC_URLS="https://api.example.com/openapi.json,https://docs.example.com/api"

# Optional: Configure Arize Phoenix tracing
export TRACING_ENABLED=true
export ARIZE_ENDPOINT="http://localhost:6006/v1/traces"
export ARIZE_API_KEY="your-api-key"

# Start the server
npm start
```

### Using with MCP Clients

Add to your MCP client configuration (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "doc2mcp": {
      "command": "node",
      "args": ["/path/to/doc2mcp/dist/index.js"],
      "env": {
        "DOC_URLS": "https://petstore.swagger.io/v2/swagger.json",
        "TRACING_ENABLED": "true"
      }
    }
  }
}
```

### Development Mode

```bash
npm run dev
```

## Supported Documentation Formats

### OpenAPI/Swagger

Supports OpenAPI 3.0+ and Swagger 2.0 specifications in JSON or YAML format:

```yaml
openapi: 3.0.0
info:
  title: Sample API
  version: 1.0.0
paths:
  /users:
    get:
      summary: List users
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
```

### HTML Documentation

Extracts API endpoints from HTML documentation:

```html
<h2>GET /api/users</h2>
<p>Retrieves a list of users</p>
<code>GET /api/users?limit=10</code>
```

### Markdown Documentation

Parses API endpoints from Markdown files:

```markdown
## GET /api/users

Retrieves a list of users.

Parameters:
- `limit` (number): Maximum number of users to return
```

## Observability

Doc2MCP integrates with Arize Phoenix for comprehensive observability:

### Tracing Features

- **Tool Execution Spans**: Every tool call creates a span with full context
- **Documentation Lineage**: Tracks which documentation generated each tool
- **Error Tracking**: Automatic error recording and exception tracking
- **Performance Metrics**: Request duration and success rates

### Span Attributes

Each tool execution includes:

- `tool.name`: Generated tool name
- `tool.source_url`: Original documentation URL
- `tool.source_type`: Documentation format (openapi/html/markdown)
- `tool.endpoint.path`: API endpoint path
- `tool.endpoint.method`: HTTP method
- `tool.args`: Input arguments
- `tool.success`: Execution status
- `http.status_code`: Response status code

### Running Arize Phoenix

```bash
# Using Docker
docker run -p 6006:6006 arizephoenix/phoenix:latest

# Or install locally
pip install arize-phoenix
phoenix serve
```

Visit http://localhost:6006 to view traces.

## Tool Generation

Doc2MCP automatically generates tools with:

### Zod Schema Validation

```typescript
// Generated schema for a user endpoint
z.object({
  userId: z.string().describe('User ID'),
  limit: z.number().optional().describe('Results per page'),
})
```

### Tool Metadata

Each tool includes:
- Name (auto-generated or from operationId)
- Description (from documentation)
- Input schema (JSON Schema from Zod)
- Handler function (executes API call)
- Metadata (source, endpoint, generation time)

### Example Tool

For an endpoint `GET /users/{userId}`:

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

- **Network Errors**: Timeouts, connection failures
- **Parsing Errors**: Invalid documentation formats
- **Validation Errors**: Schema validation failures
- **API Errors**: HTTP errors from target APIs

All errors are:
- Logged to stderr
- Tracked in OpenTelemetry spans
- Returned as structured error responses

## Project Structure

```
doc2mcp/
├── src/
│   ├── parsers/           # Documentation parsers
│   │   ├── openapi-parser.ts
│   │   ├── html-parser.ts
│   │   ├── markdown-parser.ts
│   │   └── index.ts
│   ├── generators/        # Tool and schema generators
│   │   ├── schema-generator.ts
│   │   └── tool-generator.ts
│   ├── observability/     # OpenTelemetry integration
│   │   └── tracing.ts
│   ├── server/           # MCP server implementation
│   │   └── index.ts
│   ├── types/            # TypeScript type definitions
│   │   └── index.ts
│   ├── utils/            # Utility functions
│   │   └── helpers.ts
│   └── index.ts          # Main entry point
├── dist/                 # Compiled JavaScript
├── package.json
├── tsconfig.json
└── README.md
```

## Development

### Building

```bash
npm run build
```

### Linting

```bash
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

## Deployment

### Prerequisites

Before deploying, ensure you have:
- Node.js 18.0.0 or higher
- Built the project: `npm run build`
- Configured environment variables (see `.env.example`)

For comprehensive deployment guides including Docker Compose, Kubernetes, monitoring, and security best practices, see [DEPLOYMENT.md](./DEPLOYMENT.md).

### Quick Deployment Options

#### Docker

```bash
# Build the project first
npm run build

# Create Dockerfile (see DEPLOYMENT.md for production-ready version)
docker build -t doc2mcp:latest .
docker run -e DOC_URLS="https://api.example.com/openapi.json" \
           -e TRACING_ENABLED=true \
           doc2mcp:latest
```

#### systemd Service

```bash
# 1. Build and copy files
npm run build
sudo mkdir -p /opt/doc2mcp
sudo cp -r dist package*.json /opt/doc2mcp/

# 2. Install dependencies
cd /opt/doc2mcp && sudo npm ci --production

# 3. Create service file at /etc/systemd/system/doc2mcp.service
# (See DEPLOYMENT.md for complete service configuration with non-root user)

# 4. Start service
sudo systemctl enable doc2mcp
sudo systemctl start doc2mcp
```

#### PM2

```bash
# Install PM2 globally
npm install -g pm2

# Start with environment variables
pm2 start dist/index.js --name doc2mcp \
  --env DOC_URLS="https://api.example.com/openapi.json"

# Save PM2 configuration
pm2 save
pm2 startup
```

### Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
# Edit .env with your settings
```

Required variables:
- `DOC_URLS`: Comma-separated documentation URLs

Optional variables:
- `TRACING_ENABLED`: Enable Arize Phoenix tracing (default: true)
- `ARIZE_ENDPOINT`: Phoenix endpoint URL
- `ARIZE_API_KEY`: API key for authentication

### Deployment Troubleshooting

**Server won't start:**
- Verify Node.js version: `node --version` (must be ≥18)
- Check build output: `ls -la dist/`
- Review logs for errors

**Tools not generated:**
- Verify DOC_URLS are accessible
- Check documentation format is supported
- Enable tracing to debug parsing issues

**Tracing not working:**
- Ensure Arize Phoenix is running: `docker run -p 6006:6006 arizephoenix/phoenix:latest`
- Verify ARIZE_ENDPOINT is correct
- Check network connectivity to endpoint

For more details, see [DEPLOYMENT.md](./DEPLOYMENT.md).

## Examples

### Petstore API

```bash
export DOC_URLS="https://petstore.swagger.io/v2/swagger.json"
npm start
```

Generated tools:
- `getPetById` - Find pet by ID
- `addPet` - Add a new pet
- `updatePet` - Update an existing pet
- `deletePet` - Deletes a pet

### GitHub API

```bash
export DOC_URLS="https://api.github.com/openapi.json"
npm start
```

### Multiple APIs

```bash
export DOC_URLS="https://api1.example.com/openapi.json,https://api2.example.com/docs"
npm start
```

## Limitations

- HTML/Markdown parsing is heuristic-based and may not capture all endpoints
- Authentication/authorization must be handled by the API itself or via headers
- Large documentation files may take time to parse
- Some complex OpenAPI features (allOf, oneOf, etc.) use simplified schemas

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

MIT

## Support

For issues and feature requests, please use the GitHub issue tracker.

## Acknowledgments

- Built with [MCP SDK](https://github.com/modelcontextprotocol/sdk)
- Observability by [Arize Phoenix](https://phoenix.arize.com/)
- Schema validation with [Zod](https://zod.dev/)
- OpenAPI parsing with [yaml](https://www.npmjs.com/package/yaml)
- HTML parsing with [cheerio](https://cheerio.js.org/)
- Markdown parsing with [marked](https://marked.js.org/)