'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Pencil, Trash2, Globe, Folder, Play, Code, MousePointer2, X, ChevronRight } from 'lucide-react'
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

type LLMProvider = 'gemini' | 'openai' | 'local'

interface ProviderModalState {
  isOpen: boolean
  tool: Tool | null
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
    name: `doc2mcp-${tool.toolId}`,
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
  return `cursor://anysphere.cursor-deeplink/mcp/install?name=doc2mcp-${tool.toolId}&config=${base64Config}`
}

export function ToolsList({ tools, userId }: { tools: Tool[]; userId: string }) {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState<string | null>(null)
  const [providerModal, setProviderModal] = useState<ProviderModalState>({
    isOpen: false,
    tool: null,
    editor: null
  })
  const [selectedProvider, setSelectedProvider] = useState<LLMProvider>('gemini')
  const [apiKey, setApiKey] = useState('')
  const [localUrl, setLocalUrl] = useState('http://localhost:11434')

  const openProviderModal = (tool: Tool, editor: 'vscode' | 'cursor') => {
    setProviderModal({ isOpen: true, tool, editor })
    setSelectedProvider('gemini')
    setApiKey('')
    setLocalUrl('http://localhost:11434')
  }

  const closeProviderModal = () => {
    setProviderModal({ isOpen: false, tool: null, editor: null })
  }

  const handleInstall = () => {
    if (!providerModal.tool || !providerModal.editor) return
    
    let link: string
    if (providerModal.editor === 'vscode') {
      link = getVSCodeInstallLink(providerModal.tool, selectedProvider, apiKey, localUrl)
    } else {
      link = getCursorInstallLink(providerModal.tool, selectedProvider, apiKey, localUrl)
    }
    
    window.location.href = link
    closeProviderModal()
  }

  const handleToggle = async (toolId: string, enabled: boolean) => {
    setIsLoading(toolId)
    try {
      const res = await fetch(`/api/tools/${toolId}`, {
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
      setIsLoading(null)
    }
  }

  const handleDelete = async (toolId: string) => {
    if (!confirm('Are you sure you want to delete this tool?')) return
    
    setIsLoading(toolId)
    try {
      const res = await fetch(`/api/tools/${toolId}`, {
        method: 'DELETE',
      })
      
      if (res.ok) {
        router.refresh()
      }
    } catch (error) {
      console.error('Failed to delete tool:', error)
    } finally {
      setIsLoading(null)
    }
  }

  const handleIndex = async (tool: Tool) => {
    setIsLoading(tool.id)
    try {
      const sources = JSON.parse(tool.sources)
      const webSource = sources.find((s: any) => s.type === 'web')
      
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
      setIsLoading(null)
    }
  }

  if (tools.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-16">
          <Globe className="h-16 w-16 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No tools yet</h3>
          <p className="text-muted-foreground text-center mb-6">
            Add your first documentation tool to get started
          </p>
          <Button onClick={() => router.push('/dashboard/tools/new')}>
            Add Tool
          </Button>
        </CardContent>
      </Card>
    )
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
              Select your LLM provider for {providerModal.tool?.name}
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

      {/* Tools List */}
      <div className="grid gap-4">
        {tools.map((tool) => {
          const sources = JSON.parse(tool.sources)
          const webSources = sources.filter((s: any) => s.type === 'web').length
          const localSources = sources.filter((s: any) => s.type === 'local').length
          
          return (
            <Card key={tool.id} className="hover:border-primary/50 transition-colors">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <Link href={`/dashboard/tools/${tool.id}`} className="flex-1 group">
                    <CardTitle className="flex items-center gap-2 group-hover:text-primary transition-colors">
                      {tool.name}
                      {!tool.enabled && (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground">
                          Disabled
                        </span>
                      )}
                      <ChevronRight className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </CardTitle>
                    <CardDescription className="mt-1">{tool.description}</CardDescription>
                  </Link>
                  
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={tool.enabled}
                      onCheckedChange={(enabled) => handleToggle(tool.id, enabled)}
                      disabled={isLoading === tool.id}
                    />
                  </div>
                </div>
              </CardHeader>
              
              <CardContent>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    {webSources > 0 && (
                      <div className="flex items-center gap-1.5">
                        <Globe className="h-4 w-4" />
                        <span>{webSources} web source{webSources !== 1 ? 's' : ''}</span>
                      </div>
                    )}
                    {localSources > 0 && (
                      <div className="flex items-center gap-1.5">
                        <Folder className="h-4 w-4" />
                        <span>{localSources} local source{localSources !== 1 ? 's' : ''}</span>
                      </div>
                    )}
                    <span>•</span>
                    <span>ID: {tool.toolId}</span>
                    <span>•</span>
                    <span>Added {formatDate(tool.createdAt)}</span>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    {/* Editor deeplink buttons */}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => openProviderModal(tool, 'vscode')}
                      title="Add to VS Code"
                      className="h-8 w-8 p-0"
                    >
                      <Code className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => openProviderModal(tool, 'cursor')}
                      title="Add to Cursor"
                      className="h-8 w-8 p-0"
                    >
                      <MousePointer2 className="h-4 w-4" />
                    </Button>
                    <div className="w-px h-4 bg-border" />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleIndex(tool)}
                      disabled={isLoading === tool.id || !tool.enabled}
                      className="gap-1.5"
                    >
                      <Play className="h-3.5 w-3.5" />
                      Index
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => router.push(`/dashboard/tools/${tool.id}/edit`)}
                      disabled={isLoading === tool.id}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(tool.id)}
                      disabled={isLoading === tool.id}
                      className="text-destructive hover:text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </>
  )
}
