# Testing Doc2MCP

## ✅ Configuration Complete

Your Doc2MCP server is now configured in VS Code at:
`~/.config/Code/User/mcp.json`

## 🚀 Commands to Test

### 1. Test the server directly (standalone mode):

```bash
cd /home/ash/projects/Doc2Mcp
GOOGLE_API_KEY="your-key-here" python3 -m doc2mcp.server
```

This will start the server in stdio mode. Press Ctrl+C to stop.

### 2. Test with the MCP Inspector (recommended):

```bash
# Install npx if needed
npm install -g npx

# Run MCP Inspector
npx @modelcontextprotocol/inspector python3 -m doc2mcp.server
```

Then:
- Open the URL shown in your browser
- Click "Connect"
- Try the available tools: `search_docs` and `list_available_tools`

### 3. Use in VS Code with GitHub Copilot Chat:

1. **Reload VS Code** (Cmd/Ctrl+Shift+P → "Developer: Reload Window")

2. VS Code will prompt you for:
   - GOOGLE_API_KEY (enter your Gemini API key)

3. **Open Copilot Chat** and ask:
   ```
   @doc2mcp list available tools
   ```

4. **Search documentation**:
   ```
   @doc2mcp search anthropic docs for how to use the messages API
   ```

   or

   ```
   @doc2mcp search babylon docs for creating a basic scene
   ```

## 🔍 Example Queries

Once connected, try these:

```
@doc2mcp What tools do you have available?
```

```
@doc2mcp Search the Anthropic docs for streaming responses
```

```
@doc2mcp Search BabylonJS docs for how to create a camera
```

## 🐛 Troubleshooting

### Check if server starts:
```bash
cd /home/ash/projects/Doc2Mcp
GOOGLE_API_KEY="test" python3 -m doc2mcp.server < /dev/null
```

Should show logging output without errors.

### Check available tools in your config:
```bash
cat /home/ash/projects/Doc2Mcp/tools.yaml
```

### View VS Code MCP config:
```bash
cat ~/.config/Code/User/mcp.json
```

## 📝 Notes

- The server uses Gemini 2.0 Flash for intelligent doc search
- It will cache fetched pages to avoid re-fetching
- Phoenix tracing is enabled by default for debugging
- Configure more tools by editing `tools.yaml`
