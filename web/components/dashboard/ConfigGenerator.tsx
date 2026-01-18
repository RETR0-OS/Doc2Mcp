'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Check, Copy, FileJson, Download, Zap, Sparkles, CheckCircle2 } from 'lucide-react'

interface Tool {
  toolId: string
  name: string
  description: string
  sources: string
}

export function ConfigGenerator({ tools, userEmail }: { tools: Tool[]; userEmail: string }) {
  const [copied, setCopied] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'vscode' | 'claude' | 'cursor'>('vscode')
  const [installStatus, setInstallStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle')
  const [statusMessage, setStatusMessage] = useState('')

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

  // One-click install using File System Access API
  const quickInstall = async () => {
    setInstallStatus('saving')
    
    try {
      // Check if File System Access API is supported
      if (!('showSaveFilePicker' in window)) {
        throw new Error('Your browser does not support direct file saving. Please use Chrome or Edge.')
      }

      // First, save mcp.json
      setStatusMessage('Select location for mcp.json (save to .vscode/ folder)...')
      
      const mcpHandle = await (window as any).showSaveFilePicker({
        suggestedName: 'mcp.json',
        types: [{
          description: 'JSON Files',
          accept: { 'application/json': ['.json'] }
        }]
      })
      
      const mcpWritable = await mcpHandle.createWritable()
      await mcpWritable.write(JSON.stringify(config, null, 2))
      await mcpWritable.close()

      // Then save tools.yaml
      setStatusMessage('Now select location for tools.yaml (save to project root)...')
      
      const yamlHandle = await (window as any).showSaveFilePicker({
        suggestedName: 'tools.yaml',
        types: [{
          description: 'YAML Files',
          accept: { 'text/yaml': ['.yaml', '.yml'] }
        }]
      })
      
      const yamlWritable = await yamlHandle.createWritable()
      await yamlWritable.write(toolsYaml)
      await yamlWritable.close()

      setInstallStatus('success')
      setStatusMessage('✅ Both files saved! Now run: pip install doc2mcp')

    } catch (err: any) {
      if (err.name === 'AbortError') {
        setInstallStatus('idle')
        setStatusMessage('')
      } else {
        setInstallStatus('error')
        setStatusMessage(err.message)
      }
    }
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
      {/* One-Click Install Card */}
      <Card className="border-primary bg-gradient-to-br from-primary/10 to-primary/5 shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl">
            <Sparkles className="h-6 w-6 text-primary" />
            One-Click Install
          </CardTitle>
          <CardDescription className="text-base">
            Add Doc2MCP to VS Code instantly - saves files directly to your project
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button 
            onClick={quickInstall}
            disabled={installStatus === 'saving'}
            size="lg"
            className="w-full h-14 text-lg gap-3"
          >
            {installStatus === 'saving' ? (
              <>
                <div className="h-5 w-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Saving...
              </>
            ) : installStatus === 'success' ? (
              <>
                <CheckCircle2 className="h-5 w-5" />
                Installed!
              </>
            ) : (
              <>
                <Zap className="h-5 w-5" />
                Add to VS Code
              </>
            )}
          </Button>

          {statusMessage && (
            <div className={`p-3 rounded-lg text-sm ${
              installStatus === 'success' 
                ? 'bg-green-500/10 text-green-600 dark:text-green-400 border border-green-500/20' 
                : installStatus === 'error'
                ? 'bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20'
                : 'bg-muted text-muted-foreground'
            }`}>
              {statusMessage}
            </div>
          )}

          <div className="text-sm text-muted-foreground space-y-2">
            <p className="font-medium">This will:</p>
            <ol className="list-decimal list-inside space-y-1 ml-2">
              <li>Save <code className="bg-muted px-1 rounded">mcp.json</code> → Choose your <code className="bg-muted px-1 rounded">.vscode/</code> folder</li>
              <li>Save <code className="bg-muted px-1 rounded">tools.yaml</code> → Choose your project root</li>
            </ol>
          </div>

          {installStatus === 'success' && (
            <div className="bg-primary/10 rounded-lg p-4 space-y-3">
              <p className="font-medium text-primary">🎉 Almost done! Just 2 more steps:</p>
              <div className="text-sm space-y-3">
                <div>
                  <p className="mb-1">1. Install the package:</p>
                  <div className="flex gap-2">
                    <code className="bg-background px-3 py-2 rounded flex-1 font-mono">pip install doc2mcp</code>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => handleCopy('pip install doc2mcp', 'pip')}
                    >
                      {copied === 'pip' ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>
                <div>
                  <p className="mb-1">2. Set your API key:</p>
                  <div className="flex gap-2">
                    <code className="bg-background px-3 py-2 rounded flex-1 font-mono text-xs">export GOOGLE_API_KEY="your-key"</code>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => handleCopy('export GOOGLE_API_KEY="your-key"', 'env')}
                    >
                      {copied === 'env' ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>
                <p className="text-muted-foreground">
                  Then reload VS Code: <kbd className="px-2 py-0.5 bg-muted rounded border text-xs">Cmd/Ctrl+Shift+P</kbd> → "Reload Window"
                </p>
              </div>
            </div>
          )}
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

      {/* Client Selector & Config Preview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileJson className="h-5 w-5" />
            Configuration Preview
          </CardTitle>
          <CardDescription>
            View and download configuration files for different AI clients
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
              <p className="text-sm font-medium">mcp.json</p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => downloadFile(JSON.stringify(config, null, 2), 'mcp.json')}
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

          {/* Tools YAML */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm font-medium">tools.yaml</p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => downloadFile(toolsYaml, 'tools.yaml', 'text/yaml')}
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
            <pre className="bg-card border border-border rounded-lg p-4 text-sm overflow-x-auto max-h-64">
              {toolsYaml}
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

  let yaml = `# tools.yaml - Generated from Doc2MCP Dashboard
# Your documentation search tools

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
