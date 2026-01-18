'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Check, Copy, FileJson } from 'lucide-react'

interface Tool {
  toolId: string
  name: string
  description: string
  sources: string
}

export function ConfigGenerator({ tools, userEmail }: { tools: Tool[]; userEmail: string }) {
  const [copied, setCopied] = useState(false)

  const config = {
    mcpServers: {
      "doc2mcp": {
        command: "doc2mcp",
        args: [],
        env: {
          GOOGLE_API_KEY: "your-google-api-key-here",
          TOOLS_CONFIG_PATH: "./tools.yaml"
        }
      }
    }
  }

  const toolsYaml = generateToolsYaml(tools)

  const handleCopy = async (text: string) => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileJson className="h-5 w-5" />
            MCP Server Configuration
          </CardTitle>
          <CardDescription>
            Add this to your VS Code settings or Claude Desktop config
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm font-medium">Configuration File Location</p>
            </div>
            <div className="bg-muted rounded-lg p-4 font-mono text-sm space-y-1">
              <p><span className="text-muted-foreground"># VS Code (Linux):</span></p>
              <p>~/.config/Code/User/globalStorage/github.copilot-chat/mcp.json</p>
              <p className="mt-2"><span className="text-muted-foreground"># Claude Desktop (macOS):</span></p>
              <p>~/Library/Application Support/Claude/claude_desktop_config.json</p>
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm font-medium">MCP Server Config (JSON)</p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleCopy(JSON.stringify(config, null, 2))}
                className="gap-1.5"
              >
                {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                {copied ? 'Copied!' : 'Copy'}
              </Button>
            </div>
            <pre className="bg-card border border-border rounded-lg p-4 text-sm overflow-x-auto">
              {JSON.stringify(config, null, 2)}
            </pre>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Tools Configuration (tools.yaml)</CardTitle>
          <CardDescription>
            Create this file in your project root with your enabled tools
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium">tools.yaml</p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleCopy(toolsYaml)}
              className="gap-1.5"
            >
              {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
              {copied ? 'Copied!' : 'Copy'}
            </Button>
          </div>
          <pre className="bg-card border border-border rounded-lg p-4 text-sm overflow-x-auto max-h-96">
            {toolsYaml}
          </pre>
        </CardContent>
      </Card>

      {tools.length === 0 && (
        <Card className="border-primary/50 bg-primary/5">
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">
              ⚠️ You haven't created any tools yet. Add some tools first to generate a complete configuration.
            </p>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Setup Instructions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="font-medium mb-2">1. Install Doc2MCP</p>
            <pre className="bg-muted rounded-lg p-3 text-sm font-mono">
              pip install -e git+https://github.com/RETR0-OS/Doc2Mcp.git#egg=doc2mcp
            </pre>
          </div>

          <div>
            <p className="font-medium mb-2">2. Create tools.yaml</p>
            <p className="text-sm text-muted-foreground">
              Copy the tools.yaml content above and save it in your project directory.
            </p>
          </div>

          <div>
            <p className="font-medium mb-2">3. Set up environment</p>
            <pre className="bg-muted rounded-lg p-3 text-sm font-mono">
              export GOOGLE_API_KEY="your-key-here"
            </pre>
          </div>

          <div>
            <p className="font-medium mb-2">4. Add MCP config</p>
            <p className="text-sm text-muted-foreground">
              Copy the JSON config above to your MCP configuration file.
            </p>
          </div>

          <div>
            <p className="font-medium mb-2">5. Reload VS Code</p>
            <p className="text-sm text-muted-foreground">
              Restart VS Code or reload the window (Cmd/Ctrl+Shift+P → "Developer: Reload Window")
            </p>
          </div>

          <div>
            <p className="font-medium mb-2">6. Test it!</p>
            <p className="text-sm text-muted-foreground">
              Open GitHub Copilot Chat and try: <code className="text-primary">@doc2mcp search [tool-id] for [your query]</code>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function generateToolsYaml(tools: Tool[]): string {
  if (tools.length === 0) {
    return `# tools.yaml
# No tools configured yet - add some tools in the dashboard!

tools: {}

settings:
  max_content_length: 50000
  cache_ttl: 3600
  request_timeout: 30
`
  }

  let yaml = `# tools.yaml - Generated from Doc2MCP Platform
# Auto-generated configuration for your documentation tools

tools:\n`

  tools.forEach(tool => {
    const sources = JSON.parse(tool.sources)
    
    yaml += `  ${tool.toolId}:\n`
    yaml += `    name: "${tool.name}"\n`
    yaml += `    description: "${tool.description}"\n`
    yaml += `    sources:\n`
    
    sources.forEach((source: any) => {
      if (source.type === 'web') {
        yaml += `      - type: web\n`
        yaml += `        url: "${source.url}"\n`
      } else if (source.type === 'local') {
        yaml += `      - type: local\n`
        yaml += `        path: "${source.path}"\n`
        if (source.patterns) {
          yaml += `        patterns:\n`
          source.patterns.forEach((pattern: string) => {
            yaml += `          - "${pattern}"\n`
          })
        }
      }
    })
    yaml += '\n'
  })

  yaml += `settings:
  max_content_length: 50000
  cache_ttl: 3600
  request_timeout: 30
`

  return yaml
}
