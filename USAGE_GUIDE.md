# Doc2MCP + Arize Phoenix Usage Guide

## What This System Does

**Doc2MCP** converts API documentation into tools that AI assistants can use.  
**Arize Phoenix** monitors and traces every API call for debugging and observability.

## The Complete Flow

```
API Docs → Doc2MCP → MCP Tools → AI Assistant (Claude/etc) → Makes API Calls → Traces in Arize
```

## Setup Guide

### 1. Configure Claude Desktop (Recommended)

Add Doc2MCP to Claude Desktop's MCP configuration:

**Location:** `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac)  
**Location:** `%APPDATA%\Claude\claude_desktop_config.json` (Windows)  
**Location:** `~/.config/Claude/claude_desktop_config.json` (Linux)

```json
{
  "mcpServers": {
    "doc2mcp": {
      "command": "node",
      "args": ["/home/ash/projects/Doc2Mcp/dist/index.js"],
      "env": {
        "DOC_URLS": "https://petstore.swagger.io/v2/swagger.json",
        "TRACING_ENABLED": "true",
        "ARIZE_ENDPOINT": "http://localhost:6006/v1/traces",
        "ARIZE_API_KEY": "ak-92a1ec6b-6449-4d7c-a1bd-d3ba63f544ce-GIznNgyZIP1GLzx7BDrCPus16sWjV1VK"
      }
    }
  }
}
```

### 2. Restart Claude Desktop

After saving the config, restart Claude Desktop completely.

### 3. Verify Tools Are Available

In Claude Desktop, you should see the MCP tools available. Try asking:

```
"What tools do you have available?"
```

You should see tools like:
- getPetById
- addPet
- updatePet
- etc.

### 4. Use the Tools

Now ask Claude to use them:

```
"Can you get pet with ID 10 from the petstore?"
```

Claude will call the `getPetById` tool, which will:
1. Make an API request to the Petstore API
2. Send trace data to Arize Phoenix
3. Return the result to Claude

### 5. Monitor in Arize Phoenix

Open http://localhost:6006 in your browser to see:
- All API calls Claude made
- Request/response data
- Timing information
- Success/failure status
- Full trace lineage

## Real-World Example

### Add Your Own API

1. Edit `.env`:
```bash
DOC_URLS=https://your-api.com/openapi.json,https://another-api.com/swagger.yaml
```

2. Rebuild:
```bash
npm run build
```

3. Restart Claude Desktop

4. Now Claude can call YOUR APIs!

### Example Conversation

**You:** "I need to manage users in my system. Can you show me what's available?"

**Claude:** *Lists the user management tools from your API*

**You:** "Create a new user named John Doe with email john@example.com"

**Claude:** *Calls your createUser tool with those parameters*

**You:** *Opens Arize Phoenix to see the exact API call, timing, and response*

## Use Cases

### 1. **API Testing with AI**
Ask Claude to test your API endpoints and monitor results in Arize.

### 2. **API Documentation Assistant**
Claude can explore and use your APIs based on the documentation.

### 3. **Automated API Workflows**
Chain multiple API calls through Claude, track everything in Arize.

### 4. **Debugging API Issues**
When Claude makes API calls, see full traces in Arize to debug problems.

## Without Claude Desktop

If you don't have Claude Desktop, you can:

### Option A: Use the Test Client
```bash
node test-client.js
```

This simulates an MCP client calling your tools.

### Option B: Build Your Own MCP Client
```javascript
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
// See test-client.js for example
```

### Option C: Use Other MCP Clients
- Continue.dev
- Other MCP-compatible tools

## Viewing Traces in Arize

1. Open http://localhost:6006
2. Click "Traces" in the sidebar
3. You'll see:
   - `parse.documentation` - When Doc2MCP loaded the API docs
   - `tool.getPetById` - When a tool was called
   - Click any trace to see details

### Trace Details Include:
- Tool name
- Source API URL
- Endpoint path and method
- Input arguments
- HTTP status code
- Execution time
- Success/failure status

## Troubleshooting

### Claude Desktop doesn't show tools
- Check the config file path is correct
- Restart Claude Desktop completely
- Check logs: `tail -f ~/Library/Logs/Claude/mcp*.log` (Mac)

### Arize Phoenix not showing traces
- Verify Arize is running: `docker ps | grep phoenix`
- Check endpoint in .env: `ARIZE_ENDPOINT=http://localhost:6006/v1/traces`
- Check server logs for "Tracing initialized"

### API calls failing
- Check the API documentation URL is accessible
- Verify the API endpoint is correct in traces
- Look at error details in Arize Phoenix

## What's Next?

1. **Add your own APIs** - Replace the Petstore API with your actual APIs
2. **Use with Claude** - Have natural conversations that trigger API calls
3. **Monitor in Arize** - Track all API interactions, debug issues
4. **Build workflows** - Chain multiple API calls together through Claude

## Key Files

- `.env` - Configuration (API URLs, Arize endpoint)
- `dist/index.js` - The Doc2MCP server
- `test-client.js` - Test tool calls without Claude
- `src/parsers/` - Parses different API doc formats
- `src/generators/` - Generates MCP tools from APIs
- `src/observability/` - Sends traces to Arize

