'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Plus, X, Globe, Folder } from 'lucide-react'

interface Source {
  type: 'web' | 'local'
  url?: string
  path?: string
  patterns?: string[]
}

export function ToolForm({ initialData }: { initialData?: any }) {
  const router = useRouter()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formData, setFormData] = useState({
    toolId: initialData?.toolId || '',
    name: initialData?.name || '',
    description: initialData?.description || '',
    sources: initialData?.sources ? JSON.parse(initialData.sources) : [{ type: 'web', url: '' }] as Source[],
  })

  const addSource = (type: 'web' | 'local') => {
    const newSource: Source = type === 'web' 
      ? { type: 'web', url: '' }
      : { type: 'local', path: '', patterns: ['*.md', '*.txt'] }
    
    setFormData({
      ...formData,
      sources: [...formData.sources, newSource],
    })
  }

  const removeSource = (index: number) => {
    setFormData({
      ...formData,
      sources: formData.sources.filter((_: any, i: number) => i !== index),
    })
  }

  const updateSource = (index: number, field: string, value: any) => {
    const newSources = [...formData.sources]
    newSources[index] = { ...newSources[index], [field]: value }
    setFormData({ ...formData, sources: newSources })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      const url = initialData ? `/api/tools/${initialData.id}` : '/api/tools'
      const method = initialData ? 'PUT' : 'POST'

      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      })

      if (res.ok) {
        router.push('/dashboard/tools')
        router.refresh()
      } else {
        const error = await res.json()
        alert(error.error || 'Failed to save tool')
      }
    } catch (error) {
      console.error('Failed to save tool:', error)
      alert('Failed to save tool')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Basic Information</CardTitle>
          <CardDescription>
            Give your documentation tool a unique ID and descriptive name
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="toolId">Tool ID</Label>
            <Input
              id="toolId"
              value={formData.toolId}
              onChange={(e) => setFormData({ ...formData, toolId: e.target.value })}
              placeholder="e.g., anthropic, openai, my-docs"
              required
              disabled={!!initialData}
            />
            <p className="text-sm text-muted-foreground">
              Unique identifier used in MCP config (lowercase, dashes allowed)
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="name">Display Name</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Anthropic Claude API"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Brief description of this documentation"
              rows={3}
              required
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Documentation Sources</CardTitle>
          <CardDescription>
            Add web URLs or local file paths to index
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {formData.sources.map((source: Source, index: number) => (
            <div key={index} className="p-4 border border-border rounded-lg space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {source.type === 'web' ? (
                    <Globe className="h-4 w-4 text-primary" />
                  ) : (
                    <Folder className="h-4 w-4 text-primary" />
                  )}
                  <span className="font-medium capitalize">{source.type} Source</span>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removeSource(index)}
                  disabled={formData.sources.length === 1}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>

              {source.type === 'web' ? (
                <Input
                  value={source.url || ''}
                  onChange={(e) => updateSource(index, 'url', e.target.value)}
                  placeholder="https://docs.example.com"
                  required
                />
              ) : (
                <>
                  <Input
                    value={source.path || ''}
                    onChange={(e) => updateSource(index, 'path', e.target.value)}
                    placeholder="/path/to/docs"
                    required
                  />
                  <Input
                    value={source.patterns?.join(', ') || ''}
                    onChange={(e) => updateSource(index, 'patterns', e.target.value.split(',').map(p => p.trim()))}
                    placeholder="*.md, *.txt"
                  />
                </>
              )}
            </div>
          ))}

          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => addSource('web')}
              className="flex-1 gap-2"
            >
              <Globe className="h-4 w-4" />
              Add Web Source
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => addSource('local')}
              className="flex-1 gap-2"
            >
              <Folder className="h-4 w-4" />
              Add Local Source
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="flex gap-3">
        <Button type="submit" disabled={isSubmitting} className="flex-1">
          {isSubmitting ? 'Saving...' : initialData ? 'Update Tool' : 'Create Tool'}
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={() => router.back()}
          disabled={isSubmitting}
        >
          Cancel
        </Button>
      </div>
    </form>
  )
}
