'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Check, Copy, FileJson, Download, Terminal } from 'lucide-react'

interface Tool {
  toolId: string
  name: string
  description: string
  sources: string
}

// Generate tools.yaml content
function generateToolsYaml(tools: Tool[]): string {
  if (tools.length === 0) {
    return `# Doc2MCP Tools Configuration
# Add your documentation tools here

tools:
  - name: example
    description: Example documentation tool
    sources:
      - type: web
        url: https://docs.example.com
`
  }

  const toolsConfig = tools.map(tool => {
    const sources = tool.sources.split('\n').filter(s => s.trim())
    const sourcesYaml = sources.map(url => `      - type: web\n        url: ${url.trim()}`).join('\n')
    return `  - name: ${tool.name}
    description: ${tool.description}
${sourcesYaml}`
  }).join('\n\n')

  return `# Doc2MCP Tools Configuration
# Generated from your dashboard tools

tools:
${toolsConfig}
`
}

export function ConfigGenerator({ tools, userEmail }: { tools: Tool[]; userEmail: string }) {
  const [copied, setCopied] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'vscode' | 'cursor'>('vscode')

  // Generate full MCP config for different clients
  const generateConfig = (client: 'vscode' | 'cursor') => {
    const baseConfig = {
      command: "doc2mcp",
      args: [],
      env: {
        LLM_PROVIDER: "${LLM_PROVIDER}",
        GOOGLE_API_KEY: "${GOOGLE_API_KEY}",
        OPENAI_API_KEY: "${OPENAI_API_KEY}",
        LOCAL_LLM_URL: "${LOCAL_LLM_URL}",
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
    }
  }

  const paths = getConfigPath()

  return (
    <div className="space-y-6">
      {/* Manual Setup Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Terminal className="h-5 w-5" />
            Setup Guide
          </CardTitle>
          <CardDescription>
            Step-by-step installation for Doc2MCP
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Step 1: Install */}
          <div className="flex items-start gap-4 p-4 bg-muted/50 rounded-lg">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground font-bold text-sm shrink-0">
              1
            </div>
            <div className="flex-1 space-y-2">
              <p className="font-medium">Install Doc2MCP</p>
              <div className="flex gap-2">
                <code className="flex-1 bg-muted px-3 py-2 rounded text-sm font-mono">
                  pip install doc2mcp
                </code>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleCopy('pip install doc2mcp', 'pip')}
                >
                  {copied === 'pip' ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                </Button>
              </div>
            </div>
          </div>

          {/* Step 2: Download files */}
          <div className="flex items-start gap-4 p-4 bg-muted/50 rounded-lg">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground font-bold text-sm shrink-0">
              2
            </div>
            <div className="flex-1 space-y-3">
              <p className="font-medium">Download config files</p>
              <div className="flex gap-2 flex-wrap">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => downloadFile(JSON.stringify(config, null, 2), 'mcp.json')}
                  className="gap-2"
                >
                  <FileJson className="h-4 w-4" />
                  mcp.json
                  <Download className="h-3 w-3" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => downloadFile(toolsYaml, 'tools.yaml', 'text/yaml')}
                  className="gap-2"
                >
                  <FileJson className="h-4 w-4" />
                  tools.yaml
                  <Download className="h-3 w-3" />
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Place <code className="bg-muted px-1 rounded">mcp.json</code> in <code className="bg-muted px-1 rounded">.vscode/</code> or <code className="bg-muted px-1 rounded">.cursor/</code> and <code className="bg-muted px-1 rounded">tools.yaml</code> in project root
              </p>
            </div>
          </div>

          {/* Step 3: Set env vars */}
          <div className="flex items-start gap-4 p-4 bg-muted/50 rounded-lg">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground font-bold text-sm shrink-0">
              3
            </div>
            <div className="flex-1 space-y-2">
              <p className="font-medium">Set Environment Variables</p>
              <div className="text-sm text-muted-foreground space-y-1">
                <p>Set <code className="bg-muted px-1 rounded">LLM_PROVIDER</code> to one of: <code className="bg-muted px-1 rounded">gemini</code>, <code className="bg-muted px-1 rounded">openai</code>, or <code className="bg-muted px-1 rounded">local</code></p>
                <p>Then set the corresponding API key or URL:</p>
                <ul className="list-disc list-inside ml-2 space-y-0.5">
                  <li><code className="bg-muted px-1 rounded">GOOGLE_API_KEY</code> for Gemini</li>
                  <li><code className="bg-muted px-1 rounded">OPENAI_API_KEY</code> for OpenAI</li>
                  <li><code className="bg-muted px-1 rounded">LOCAL_LLM_URL</code> for local LLM (e.g., Ollama)</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Step 4: Restart */}
          <div className="flex items-start gap-4 p-4 bg-muted/50 rounded-lg">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground font-bold text-sm shrink-0">
              4
            </div>
            <div className="flex-1 space-y-2">
              <p className="font-medium">Restart your editor</p>
              <p className="text-sm text-muted-foreground">
                Restart VS Code or Cursor to activate the MCP server
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Config Preview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileJson className="h-5 w-5" />
            Configuration Preview
          </CardTitle>
          <CardDescription>
            Preview and copy configurations for different editors
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Tab selector */}
          <div className="flex gap-2 p-1 bg-muted rounded-lg w-fit">
            {(['vscode', 'cursor'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === tab
                    ? 'bg-background text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                {tab === 'vscode' ? 'VS Code' : 'Cursor'}
              </button>
            ))}
          </div>

          {/* Config paths */}
          <div className="p-4 bg-muted/50 rounded-lg space-y-2 text-sm">
            <p className="font-medium">Config file locations:</p>
            <div className="grid gap-1 text-muted-foreground">
              <p><span className="font-medium text-foreground">Workspace:</span> {paths.workspace}</p>
              <p><span className="font-medium text-foreground">Linux/Mac:</span> {paths.global}</p>
              <p><span className="font-medium text-foreground">Windows:</span> {paths.windows}</p>
            </div>
          </div>

          {/* MCP Config */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium">mcp.json</h3>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => handleCopy(JSON.stringify(config, null, 2), 'config')}
              >
                {copied === 'config' ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              </Button>
            </div>
            <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-sm">
              <code>{JSON.stringify(config, null, 2)}</code>
            </pre>
          </div>

          {/* Tools YAML */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium">tools.yaml</h3>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => handleCopy(toolsYaml, 'yaml')}
              >
                {copied === 'yaml' ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              </Button>
            </div>
            <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-sm max-h-64">
              <code>{toolsYaml}</code>
            </pre>
          </div>
        </CardContent>
      </Card>

      {/* Terminal Commands */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Terminal className="h-5 w-5" />
            CLI Commands
          </CardTitle>
          <CardDescription>
            Useful commands for managing Doc2MCP
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {[
            { label: 'Install Doc2MCP', cmd: 'pip install doc2mcp' },
            { label: 'Run server', cmd: 'doc2mcp serve' },
            { label: 'Set provider (Gemini)', cmd: 'export LLM_PROVIDER=gemini' },
            { label: 'Set provider (OpenAI)', cmd: 'export LLM_PROVIDER=openai' },
            { label: 'Set provider (Local)', cmd: 'export LLM_PROVIDER=local' },
            { label: 'Set Gemini API key', cmd: 'export GOOGLE_API_KEY="your-key-here"' },
            { label: 'Set OpenAI API key', cmd: 'export OPENAI_API_KEY="your-key-here"' },
            { label: 'Set Local LLM URL', cmd: 'export LOCAL_LLM_URL="http://localhost:11434"' },
          ].map((item, idx) => (
            <div key={idx} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
              <div>
                <p className="text-xs text-muted-foreground">{item.label}</p>
                <code className="text-sm font-mono">{item.cmd}</code>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleCopy(item.cmd, `cmd-${idx}`)}
              >
                {copied === `cmd-${idx}` ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              </Button>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
