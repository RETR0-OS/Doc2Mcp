'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Pencil, Trash2, Globe, Folder, Play, ChevronRight } from 'lucide-react'
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

export function ToolsList({ tools, userId }: { tools: Tool[]; userId: string }) {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState<string | null>(null)

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
