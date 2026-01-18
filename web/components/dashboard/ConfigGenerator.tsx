'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Check, Copy, FileJson, Download, Zap, Terminal, FolderOpen, ExternalLink } from 'lucide-react'

interface Tool {
  toolId: string
  name: string
  description: string
  sources: string
}

export function ConfigGenerator({ tools, userEmail }: { tools: Tool[]; userEmail: string }) {
  const [copied, setCopied] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'vscode' | 'claude' | 'cursor'>('vscode')

  // Generate MCP config for different clients
  const generateConfig = (client: 'vscode' | 'claude' | 'cursor') => {
    const baseConfig = {
      command: "doc2mcp",
      args: [],
      env: {
        GOOGLE_API_KEY: "${GOOGLE_API_KEY}",
        TOOLS_CONFIG_PATH: "./tools.yaml"
      }
    }

    if (client === 'vscode') {
      return {
        servers: {
          "doc2mcp": baseConfig
        }
      }
    } else if (client === 'cursor') {
      return {
        mcpServers: {
          "doc2mcp": baseConfig
        }
      }
    } else {
      return {
        mcpServers: {
          "doc2mcp": baseConfig
        }
      }
    }
  }

  const toolsYaml = generateToolsYaml(tools)
  const config = generateConfig(activeTab)

  const handleCopy = async (text: string, id: string) => {
    await navigator.clipboard.writeText(text)
    setCopied(id)
    setTimeout(() => setCopied(null), 2000)
  }

  const downloadFile = (content: string, filename: string, type: string = 'application/json') => {
    const blob = new Blob([content], { type })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const downloadMcpJson = () => {
    downloadFile(JSON.stringify(config, null, 2), 'mcp.json')
  }

  const downloadToolsYaml = () => {
    downloadFile(toolsYaml, 'tools.yaml', 'text/yaml')
  }

  const downloadSetupScript = () => {
    const isWindows = navigator.userAgent.includes('Windows')
    
    if (isWindows) {
      const script = `@echo off
REM Doc2MCP Setup Script for Windows
REM Run this in your project directory

echo Setting up Doc2MCP...

REM Install doc2mcp
pip install doc2mcp

REM Create tools.yaml
echo Creating tools.yaml...
(
${toolsYaml.split('\n').map(line => `echo ${line.replace(/"/g, '\\"')}`).join('\n')}
) > tools.yaml

REM Create .vscode directory if it doesn't exist  
if not exist ".vscode" mkdir .vscode

REM Create MCP config
echo Creating .vscode/mcp.json...
echo ${JSON.stringify(config).replace(/"/g, '\\"')} > .vscode\\mcp.json

echo.
echo Setup complete! 
echo.
echo Next steps:
echo 1. Set your GOOGLE_API_KEY environment variable
echo 2. Reload VS Code (Ctrl+Shift+P then "Developer: Reload Window")
echo 3. Start using @doc2mcp in Copilot Chat!
pause
`
      downloadFile(script, 'setup-doc2mcp.bat', 'text/plain')
    } else {
      const script = `#!/bin/bash
# Doc2MCP Setup Script
# Run this in your project directory

set -e

echo "🚀 Setting up Doc2MCP..."

# Install doc2mcp
echo "📦 Installing doc2mcp..."
pip install doc2mcp

# Create tools.yaml
echo "📝 Creating tools.yaml..."
cat > tools.yaml << 'TOOLSEOF'
${toolsYaml}
TOOLSEOF

# Create .vscode directory if it doesn't exist
mkdir -p .vscode

# Create MCP config for VS Code workspace
echo "⚙️ Creating .vscode/mcp.json..."
cat > .vscode/mcp.json << 'MCPEOF'
${JSON.stringify(config, null, 2)}
MCPEOF

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Set your GOOGLE_API_KEY: export GOOGLE_API_KEY='your-key'"
echo "2. Reload VS Code (Cmd/Ctrl+Shift+P → 'Developer: Reload Window')"
echo "3. Start using @doc2mcp in Copilot Chat!"
`
      downloadFile(script, 'setup-doc2mcp.sh', 'text/plain')
    }
  }

  const openVSCodeSettings = () => {
    // VS Code URI to open settings
    window.open('vscode://settings/github.copilot.chat.mcp.enabled', '_blank')
  }

  const getConfigPath = () => {
    switch (activeTab) {
      case 'vscode':
        return {
          global: '~/.config/Code/User/globalStorage/github.copilot-chat/mcp.json',
          workspace: '.vscode/mcp.json (recommended)',
          windows: '%APPDATA%\\Code\\User\\globalStorage\\github.copilot-chat\\mcp.json'
        }
      case 'cursor':
        return {
          global: '~/.cursor/mcp.json',
          workspace: '.cursor/mcp.json',
          windows: '%USERPROFILE%\\.cursor\\mcp.json'
        }
      case 'claude':
        return {
          global: '~/Library/Application Support/Claude/claude_desktop_config.json',
          workspace: 'N/A - Claude uses global config only',
          windows: '%APPDATA%\\Claude\\claude_desktop_config.json'
        }
    }
  }

  const paths = getConfigPath()

  return (
    <div className="space-y-6">
      {/* Quick Setup Card */}
      <Card className="border-primary/50 bg-gradient-to-br from-primary/5 to-primary/10">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-primary" />
            Quick Setup
          </CardTitle>
          <CardDescription>
            One-click setup options - choose your preferred method
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <Button 
              onClick={downloadSetupScript}
              className="h-auto py-4 flex-col gap-2"
            >
              <Terminal className="h-5 w-5" />
              <span>Download Setup Script</span>
              <span className="text-xs opacity-75">Run in your project folder</span>
            </Button>
            
            <Button 
              variant="secondary"
              onClick={() => {
                downloadMcpJson()
                downloadToolsYaml()
              }}
              className="h-auto py-4 flex-col gap-2"
            >
              <Download className="h-5 w-5" />
              <span>Download Config Files</span>
              <span className="text-xs opacity-75">mcp.json + tools.yaml</span>
            </Button>

            <Button 
              variant="outline"
              onClick={openVSCodeSettings}
              className="h-auto py-4 flex-col gap-2"
            >
              <ExternalLink className="h-5 w-5" />
              <span>Open VS Code Settings</span>
              <span className="text-xs opacity-75">Configure manually</span>
            </Button>
          </div>

          <div className="bg-background/50 rounded-lg p-4 text-sm">
            <p className="font-medium mb-2">🎯 Recommended: Use the Setup Script</p>
            <ol className="list-decimal list-inside space-y-1 text-muted-foreground">
              <li>Download the setup script</li>
              <li>Run it in your project folder: <code className="bg-muted px-1 rounded">./setup-doc2mcp.sh</code></li>
              <li>Set your API key: <code className="bg-muted px-1 rounded">export GOOGLE_API_KEY="..."</code></li>
              <li>Reload VS Code and start using it!</li>
            </ol>
          </div>
        </CardContent>
      </Card>

      {/* Client Selector */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileJson className="h-5 w-5" />
            MCP Configuration
          </CardTitle>
          <CardDescription>
            Select your AI client to get the correct config format
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Tab Selector */}
          <div className="flex gap-2 p-1 bg-muted rounded-lg w-fit">
            {(['vscode', 'cursor', 'claude'] as const).map((client) => (
              <button
                key={client}
                onClick={() => setActiveTab(client)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === client 
                    ? 'bg-background shadow text-foreground' 
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                {client === 'vscode' ? 'VS Code' : client === 'cursor' ? 'Cursor' : 'Claude Desktop'}
              </button>
            ))}
          </div>

          {/* Config Paths */}
          <div className="bg-muted rounded-lg p-4 text-sm font-mono space-y-2">
            <p><span className="text-muted-foreground"># Workspace config (recommended):</span></p>
            <p className="text-primary">{paths.workspace}</p>
            <p className="mt-2"><span className="text-muted-foreground"># Global config (Linux/macOS):</span></p>
            <p>{paths.global}</p>
            <p className="mt-2"><span className="text-muted-foreground"># Global config (Windows):</span></p>
            <p>{paths.windows}</p>
          </div>

          {/* JSON Config */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm font-medium">
                {activeTab === 'vscode' ? 'mcp.json' : activeTab === 'cursor' ? 'mcp.json' : 'claude_desktop_config.json'}
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={downloadMcpJson}
                  className="gap-1.5"
                >
                  <Download className="h-3.5 w-3.5" />
                  Download
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleCopy(JSON.stringify(config, null, 2), 'config')}
                  className="gap-1.5"
                >
                  {copied === 'config' ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                  {copied === 'config' ? 'Copied!' : 'Copy'}
                </Button>
              </div>
            </div>
            <pre className="bg-card border border-border rounded-lg p-4 text-sm overflow-x-auto">
              {JSON.stringify(config, null, 2)}
            </pre>
          </div>
        </CardContent>
      </Card>

      {/* Tools YAML */}
      <Card>
        <CardHeader>
          <CardTitle>Tools Configuration</CardTitle>
          <CardDescription>
            Your documentation tools - place tools.yaml in your project root
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium">tools.yaml</p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={downloadToolsYaml}
                className="gap-1.5"
              >
                <Download className="h-3.5 w-3.5" />
                Download
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleCopy(toolsYaml, 'yaml')}
                className="gap-1.5"
              >
                {copied === 'yaml' ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                {copied === 'yaml' ? 'Copied!' : 'Copy'}
              </Button>
            </div>
          </div>
          <pre className="bg-card border border-border rounded-lg p-4 text-sm overflow-x-auto max-h-96">
            {toolsYaml}
          </pre>
        </CardContent>
      </Card>

      {tools.length === 0 && (
        <Card className="border-yellow-500/50 bg-yellow-500/5">
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">
              ⚠️ You haven't created any tools yet. Add some tools first to generate a complete configuration.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Manual Setup Instructions */}
      <Card>
        <CardHeader>
          <CardTitle>Manual Setup Instructions</CardTitle>
          <CardDescription>
            Step-by-step guide if you prefer manual setup
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="font-medium mb-2">1. Install Doc2MCP</p>
            <div className="flex gap-2">
              <pre className="bg-muted rounded-lg p-3 text-sm font-mono flex-1">
                pip install doc2mcp
              </pre>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => handleCopy('pip install doc2mcp', 'install')}
              >
                {copied === 'install' ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              </Button>
            </div>
          </div>

          <div>
            <p className="font-medium mb-2">2. Create config files</p>
            <p className="text-sm text-muted-foreground">
              Download or copy the files above into your project:
            </p>
            <ul className="text-sm text-muted-foreground list-disc list-inside mt-1">
              <li><code className="bg-muted px-1 rounded">.vscode/mcp.json</code> - MCP server config</li>
              <li><code className="bg-muted px-1 rounded">tools.yaml</code> - Your documentation tools</li>
            </ul>
          </div>

          <div>
            <p className="font-medium mb-2">3. Set up environment</p>
            <div className="flex gap-2">
              <pre className="bg-muted rounded-lg p-3 text-sm font-mono flex-1">
                export GOOGLE_API_KEY="your-api-key"
              </pre>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => handleCopy('export GOOGLE_API_KEY="your-api-key"', 'env')}
              >
                {copied === 'env' ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              </Button>
            </div>
          </div>

          <div>
            <p className="font-medium mb-2">4. Reload VS Code</p>
            <p className="text-sm text-muted-foreground">
              Press <kbd className="px-2 py-0.5 bg-muted rounded border text-xs">Ctrl+Shift+P</kbd> (or <kbd className="px-2 py-0.5 bg-muted rounded border text-xs">Cmd+Shift+P</kbd> on Mac) 
              and run "Developer: Reload Window"
            </p>
          </div>

          <div>
            <p className="font-medium mb-2">5. Start using it!</p>
            <p className="text-sm text-muted-foreground">
              Open GitHub Copilot Chat and try:
            </p>
            <pre className="bg-muted rounded-lg p-3 text-sm font-mono mt-2">
              @doc2mcp search for authentication in Next.js docs
            </pre>
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
