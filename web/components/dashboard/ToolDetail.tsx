'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { 
  ArrowLeft, 
  Globe, 
  Folder, 
  Play, 
  Pencil, 
  Trash2, 
  Code, 
  MousePointer2, 
  X,
  Clock,
  CheckCircle,
  XCircle,
  Loader2,
  Copy,
  Check,
  Braces,
  FileJson
} from 'lucide-react'
import { formatDate } from '@/lib/utils'

interface Tool {
  id: string
  toolId: string
  name: string
  description: string
  sources: string
  enabled: boolean
  createdAt: string
  updatedAt: string
}

interface Job {
  id: string
  type: string
  status: string
  progress: number
  createdAt: string
  startedAt: string | null
  completedAt: string | null
}

type LLMProvider = 'gemini' | 'openai' | 'local'

interface ProviderModalState {
  isOpen: boolean
  editor: 'vscode' | 'cursor' | null
}

// Generate VS Code deeplink
const getVSCodeInstallLink = (tool: Tool, provider: LLMProvider, apiKey: string, localUrl: string, insiders: boolean = false) => {
  const env: Record<string, string> = {
    LLM_PROVIDER: provider,
    TOOLS_CONFIG_PATH: "./tools.yaml"
  }
  
  if (provider === 'gemini') {
    env.GOOGLE_API_KEY = apiKey || "${input:google_api_key}"
  } else if (provider === 'openai') {
    env.OPENAI_API_KEY = apiKey || "${input:openai_api_key}"
  } else if (provider === 'local') {
    env.LOCAL_LLM_URL = localUrl || "${input:local_llm_url}"
  }

  const config = {
    name: `doc2mcp`,
    command: "doc2mcp",
    args: [],
    env
  }
  const scheme = insiders ? 'vscode-insiders' : 'vscode'
  return `${scheme}:mcp/install?${encodeURIComponent(JSON.stringify(config))}`
}

// Generate Cursor deeplink
const getCursorInstallLink = (tool: Tool, provider: LLMProvider, apiKey: string, localUrl: string) => {
  const env: Record<string, string> = {
    LLM_PROVIDER: provider,
    TOOLS_CONFIG_PATH: "./tools.yaml"
  }
  
  if (provider === 'gemini') {
    env.GOOGLE_API_KEY = apiKey || "${GOOGLE_API_KEY}"
  } else if (provider === 'openai') {
    env.OPENAI_API_KEY = apiKey || "${OPENAI_API_KEY}"
  } else if (provider === 'local') {
    env.LOCAL_LLM_URL = localUrl || "${LOCAL_LLM_URL}"
  }

  const config = {
    command: "doc2mcp",
    args: [],
    env
  }
  const base64Config = btoa(JSON.stringify(config))
  return `cursor://anysphere.cursor-deeplink/mcp/install?name=doc2mcp&config=${base64Config}`
}

export function ToolDetail({ tool, jobs }: { tool: Tool; jobs: Job[] }) {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(false)
  const [copied, setCopied] = useState<string | null>(null)
  const [providerModal, setProviderModal] = useState<ProviderModalState>({
    isOpen: false,
    editor: null
  })
  const [selectedProvider, setSelectedProvider] = useState<LLMProvider>('gemini')
  const [apiKey, setApiKey] = useState('')
  const [localUrl, setLocalUrl] = useState('http://localhost:11434')

  const sources = JSON.parse(tool.sources)
  const webSources = sources.filter((s: any) => s.type === 'web')
  const localSources = sources.filter((s: any) => s.type === 'local')

  const openProviderModal = (editor: 'vscode' | 'cursor') => {
    setProviderModal({ isOpen: true, editor })
    setSelectedProvider('gemini')
    setApiKey('')
    setLocalUrl('http://localhost:11434')
  }

  const closeProviderModal = () => {
    setProviderModal({ isOpen: false, editor: null })
  }

  const handleInstall = () => {
    if (!providerModal.editor) return
    
    let link: string
    if (providerModal.editor === 'vscode') {
      link = getVSCodeInstallLink(tool, selectedProvider, apiKey, localUrl)
    } else {
      link = getCursorInstallLink(tool, selectedProvider, apiKey, localUrl)
    }
    
    window.location.href = link
    closeProviderModal()
  }

  const handleToggle = async (enabled: boolean) => {
    setIsLoading(true)
    try {
      const res = await fetch(`/api/tools/${tool.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled }),
      })
      
      if (res.ok) {
        router.refresh()
      }
    } catch (error) {
      console.error('Failed to toggle tool:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this tool?')) return
    
    setIsLoading(true)
    try {
      const res = await fetch(`/api/tools/${tool.id}`, {
        method: 'DELETE',
      })
      
      if (res.ok) {
        router.push('/dashboard/tools')
      }
    } catch (error) {
      console.error('Failed to delete tool:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleIndex = async () => {
    setIsLoading(true)
    try {
      const webSource = webSources[0]
      
      if (!webSource) {
        alert('No web source found for this tool')
        return
      }

      const res = await fetch('/api/jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'index',
          toolId: tool.toolId,
          url: webSource.url,
        }),
      })
      
      if (res.ok) {
        router.push('/dashboard/jobs')
      }
    } catch (error) {
      console.error('Failed to start indexing:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleCopy = async (text: string, id: string) => {
    await navigator.clipboard.writeText(text)
    setCopied(id)
    setTimeout(() => setCopied(null), 2000)
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'running':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
      default:
        return <Clock className="h-4 w-4 text-muted-foreground" />
    }
  }

  // Generate the MCP tool definition that gets exposed
  const mcpToolDefinition = {
    name: "search_docs",
    description: "Search documentation for a specific tool",
    inputSchema: {
      type: "object",
      properties: {
        tool_name: {
          type: "string",
          description: `The tool to search. Available: "${tool.toolId}"`,
        },
        query: {
          type: "string",
          description: "Search query describing what information you need",
        },
      },
      required: ["tool_name", "query"],
    },
  }

  return (
    <>
      {/* Provider Selection Modal */}
      {providerModal.isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/50" onClick={closeProviderModal} />
          <div className="relative bg-background border rounded-lg shadow-xl w-full max-w-md mx-4 p-6">
            <button
              onClick={closeProviderModal}
              className="absolute top-4 right-4 text-muted-foreground hover:text-foreground"
            >
              <X className="h-5 w-5" />
            </button>
            
            <h2 className="text-lg font-semibold mb-1">
              Add to {providerModal.editor === 'vscode' ? 'VS Code' : 'Cursor'}
            </h2>
            <p className="text-sm text-muted-foreground mb-4">
              Select your LLM provider for Doc2MCP
            </p>

            {/* Provider Selection */}
            <div className="space-y-3 mb-4">
              <Label className="text-sm font-medium">LLM Provider</Label>
              <div className="grid grid-cols-3 gap-2">
                {(['gemini', 'openai', 'local'] as const).map((provider) => (
                  <button
                    key={provider}
                    onClick={() => setSelectedProvider(provider)}
                    className={`px-3 py-2 rounded-md text-sm font-medium border transition-colors ${
                      selectedProvider === provider
                        ? 'bg-primary text-primary-foreground border-primary'
                        : 'bg-background hover:bg-muted border-border'
                    }`}
                  >
                    {provider === 'gemini' ? 'Gemini' : provider === 'openai' ? 'OpenAI' : 'Local'}
                  </button>
                ))}
              </div>
            </div>

            {/* API Key / URL Input */}
            <div className="space-y-2 mb-6">
              {selectedProvider === 'gemini' && (
                <>
                  <Label htmlFor="api-key" className="text-sm font-medium">
                    Google API Key <span className="text-muted-foreground">(optional)</span>
                  </Label>
                  <Input
                    id="api-key"
                    type="password"
                    placeholder="Leave empty to prompt in VS Code"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                  />
                </>
              )}
              {selectedProvider === 'openai' && (
                <>
                  <Label htmlFor="api-key" className="text-sm font-medium">
                    OpenAI API Key <span className="text-muted-foreground">(optional)</span>
                  </Label>
                  <Input
                    id="api-key"
                    type="password"
                    placeholder="Leave empty to prompt in VS Code"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                  />
                </>
              )}
              {selectedProvider === 'local' && (
                <>
                  <Label htmlFor="local-url" className="text-sm font-medium">
                    Local LLM URL
                  </Label>
                  <Input
                    id="local-url"
                    type="text"
                    placeholder="http://localhost:11434"
                    value={localUrl}
                    onChange={(e) => setLocalUrl(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    Ollama default: http://localhost:11434
                  </p>
                </>
              )}
            </div>

            {/* Actions */}
            <div className="flex gap-2">
              <Button variant="outline" onClick={closeProviderModal} className="flex-1">
                Cancel
              </Button>
              <Button onClick={handleInstall} className="flex-1">
                Install
              </Button>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Link href="/dashboard/tools">
            <Button variant="ghost" size="sm" className="gap-2">
              <ArrowLeft className="h-4 w-4" />
              Back
            </Button>
          </Link>
        </div>

        {/* Tool Overview Card */}
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="flex items-center gap-3 text-2xl">
                  {tool.name}
                  {!tool.enabled && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground">
                      Disabled
                    </span>
                  )}
                </CardTitle>
                <CardDescription className="mt-2 text-base">
                  {tool.description}
                </CardDescription>
              </div>
              <Switch
                checked={tool.enabled}
                onCheckedChange={handleToggle}
                disabled={isLoading}
              />
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-6 text-sm text-muted-foreground">
              <div className="flex items-center gap-1.5">
                <span className="font-medium text-foreground">Tool ID:</span>
                <code className="bg-muted px-2 py-0.5 rounded">{tool.toolId}</code>
              </div>
              <span>•</span>
              <span>Created {formatDate(tool.createdAt)}</span>
              <span>•</span>
              <span>Updated {formatDate(tool.updatedAt)}</span>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-3 pt-2">
              <Button
                onClick={() => openProviderModal('vscode')}
                className="gap-2"
              >
                <Code className="h-4 w-4" />
                Add to VS Code
              </Button>
              <Button
                variant="secondary"
                onClick={() => openProviderModal('cursor')}
                className="gap-2"
              >
                <MousePointer2 className="h-4 w-4" />
                Add to Cursor
              </Button>
              <Button
                variant="outline"
                onClick={handleIndex}
                disabled={isLoading || !tool.enabled}
                className="gap-2"
              >
                <Play className="h-4 w-4" />
                Index Now
              </Button>
              <div className="flex-1" />
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push(`/dashboard/tools/${tool.id}/edit`)}
                disabled={isLoading}
              >
                <Pencil className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleDelete}
                disabled={isLoading}
                className="text-destructive hover:text-destructive"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Sources Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Globe className="h-5 w-5" />
              Documentation Sources
            </CardTitle>
            <CardDescription>
              URLs and paths that are indexed for this tool
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {webSources.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium flex items-center gap-2">
                  <Globe className="h-4 w-4" />
                  Web Sources ({webSources.length})
                </h4>
                <div className="space-y-2">
                  {webSources.map((source: any, idx: number) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3 bg-muted/50 rounded-lg"
                    >
                      <code className="text-sm">{source.url}</code>
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline text-sm"
                      >
                        Open ↗
                      </a>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {localSources.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium flex items-center gap-2">
                  <Folder className="h-4 w-4" />
                  Local Sources ({localSources.length})
                </h4>
                <div className="space-y-2">
                  {localSources.map((source: any, idx: number) => (
                    <div
                      key={idx}
                      className="p-3 bg-muted/50 rounded-lg"
                    >
                      <code className="text-sm">{source.path}</code>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* MCP Tool Definition Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Braces className="h-5 w-5" />
              MCP Tool Definition
            </CardTitle>
            <CardDescription>
              This is how your tool appears to AI agents via the MCP protocol
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 bg-muted/50 rounded-lg space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="font-medium">search_docs</h4>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleCopy(JSON.stringify(mcpToolDefinition, null, 2), 'mcp-def')}
                >
                  {copied === 'mcp-def' ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                </Button>
              </div>
              <p className="text-sm text-muted-foreground">
                Search the <code className="bg-muted px-1 rounded">{tool.name}</code> documentation
              </p>
              <div className="text-sm">
                <p className="font-medium mb-1">Example usage:</p>
                <pre className="bg-muted p-3 rounded text-xs overflow-x-auto">
{`search_docs(
  tool_name="${tool.toolId}",
  query="How do I get started with ${tool.name}?"
)`}
                </pre>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium">Full Schema (JSON)</h4>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleCopy(JSON.stringify(mcpToolDefinition, null, 2), 'schema')}
                >
                  {copied === 'schema' ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                </Button>
              </div>
              <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-xs">
                <code>{JSON.stringify(mcpToolDefinition, null, 2)}</code>
              </pre>
            </div>
          </CardContent>
        </Card>

        {/* Recent Jobs Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Recent Indexing Jobs
            </CardTitle>
            <CardDescription>
              History of indexing operations for this tool
            </CardDescription>
          </CardHeader>
          <CardContent>
            {jobs.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Clock className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>No indexing jobs yet</p>
                <p className="text-sm">Click "Index Now" to start indexing this tool's documentation</p>
              </div>
            ) : (
              <div className="space-y-2">
                {jobs.map((job) => (
                  <div
                    key={job.id}
                    className="flex items-center justify-between p-3 bg-muted/50 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      {getStatusIcon(job.status)}
                      <div>
                        <p className="text-sm font-medium capitalize">{job.type}</p>
                        <p className="text-xs text-muted-foreground">
                          {formatDate(job.createdAt)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      {job.status === 'running' && (
                        <div className="flex items-center gap-2">
                          <div className="w-24 h-2 bg-muted rounded-full overflow-hidden">
                            <div
                              className="h-full bg-primary transition-all"
                              style={{ width: `${job.progress}%` }}
                            />
                          </div>
                          <span className="text-xs text-muted-foreground w-8">
                            {job.progress}%
                          </span>
                        </div>
                      )}
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        job.status === 'completed' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                        job.status === 'failed' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                        job.status === 'running' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' :
                        'bg-muted text-muted-foreground'
                      }`}>
                        {job.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  )
}
