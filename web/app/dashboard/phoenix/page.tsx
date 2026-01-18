import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ExternalLink } from 'lucide-react'

export default function PhoenixPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Phoenix Observability</h1>
          <p className="text-muted-foreground mt-1">
            Monitor LLM calls, traces, and performance metrics
          </p>
        </div>
        <Button asChild>
          <a href="http://localhost:6006" target="_blank" rel="noopener noreferrer" className="gap-2">
            Open Phoenix
            <ExternalLink className="h-4 w-4" />
          </a>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Phoenix Dashboard</CardTitle>
          <CardDescription>
            View detailed traces of all documentation searches and agent decisions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <iframe
            src="http://localhost:6006"
            className="w-full h-[800px] rounded-lg border border-border"
            title="Phoenix Dashboard"
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>What Phoenix Shows</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold">
              1
            </div>
            <div>
              <p className="font-medium">LLM Calls</p>
              <p className="text-sm text-muted-foreground">
                Every Gemini API call with input/output tokens, latency, and cost
              </p>
            </div>
          </div>

          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold">
              2
            </div>
            <div>
              <p className="font-medium">Navigation Decisions</p>
              <p className="text-sm text-muted-foreground">
                See which pages the agent explored and why it chose specific links
              </p>
            </div>
          </div>

          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold">
              3
            </div>
            <div>
              <p className="font-medium">Document Retrievals</p>
              <p className="text-sm text-muted-foreground">
                Track which documentation pages were fetched and cached
              </p>
            </div>
          </div>

          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold">
              4
            </div>
            <div>
              <p className="font-medium">Performance Metrics</p>
              <p className="text-sm text-muted-foreground">
                Analyze latency, token usage, and identify optimization opportunities
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
