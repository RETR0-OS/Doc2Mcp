'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Activity, CheckCircle2, XCircle, Clock, Loader2, Eye, Trash2, RefreshCw } from 'lucide-react'
import { formatDate } from '@/lib/utils'

interface Job {
  id: string
  type: string
  status: string
  input: string
  output: string | null
  progress: number
  logs: string
  error: string | null
  startedAt: string | null
  completedAt: string | null
  createdAt: string
}

export function JobsList({ jobs: initialJobs }: { jobs: Job[] }) {
  const [jobs, setJobs] = useState(initialJobs)
  const [selectedJob, setSelectedJob] = useState<Job | null>(null)
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [deletingIds, setDeletingIds] = useState<Set<string>>(new Set())
  const [isRefreshing, setIsRefreshing] = useState(false)

  useEffect(() => {
    // Poll for job updates
    const interval = setInterval(async () => {
      try {
        const res = await fetch('/api/jobs')
        if (res.ok) {
          const updated = await res.json()
          setJobs(updated)
        }
      } catch (error) {
        console.error('Failed to fetch jobs:', error)
      }
    }, 3000)

    return () => clearInterval(interval)
  }, [])

  const refreshJobs = async () => {
    setIsRefreshing(true)
    try {
      const res = await fetch('/api/jobs')
      if (res.ok) {
        const updated = await res.json()
        setJobs(updated)
      }
    } catch (error) {
      console.error('Failed to refresh jobs:', error)
    } finally {
      setIsRefreshing(false)
    }
  }

  const deleteJob = async (jobId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    
    if (!confirm('Are you sure you want to delete this job?')) {
      return
    }

    setDeletingIds(prev => new Set(prev).add(jobId))
    
    try {
      const res = await fetch(`/api/jobs/${jobId}`, {
        method: 'DELETE',
      })
      
      if (res.ok) {
        setJobs(prev => prev.filter(job => job.id !== jobId))
        if (selectedJob?.id === jobId) {
          setSelectedJob(null)
          ws?.close()
          setWs(null)
        }
      } else {
        const data = await res.json()
        alert(data.error || 'Failed to delete job')
      }
    } catch (error) {
      console.error('Failed to delete job:', error)
      alert('Failed to delete job')
    } finally {
      setDeletingIds(prev => {
        const next = new Set(prev)
        next.delete(jobId)
        return next
      })
    }
  }

  const deleteAllCompleted = async () => {
    const completedJobs = jobs.filter(j => j.status === 'completed' || j.status === 'failed')
    if (completedJobs.length === 0) {
      alert('No completed or failed jobs to delete')
      return
    }
    
    if (!confirm(`Delete ${completedJobs.length} completed/failed job(s)?`)) {
      return
    }

    for (const job of completedJobs) {
      try {
        await fetch(`/api/jobs/${job.id}`, { method: 'DELETE' })
      } catch (error) {
        console.error('Failed to delete job:', job.id, error)
      }
    }
    
    await refreshJobs()
  }

  const connectWebSocket = (jobId: string) => {
    const wsUrl = `ws://localhost:8000/ws/jobs/${jobId}`
    const websocket = new WebSocket(wsUrl)

    websocket.onopen = () => {
      console.log('WebSocket connected for job:', jobId)
    }

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.type === 'log') {
        // Update job in list
        setJobs(prev => prev.map(job => 
          job.id === jobId 
            ? { ...job, progress: data.progress, status: data.status }
            : job
        ))
      }
    }

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    websocket.onclose = () => {
      console.log('WebSocket closed')
    }

    setWs(websocket)
  }

  const handleViewDetails = (job: Job) => {
    setSelectedJob(job)
    if (job.status === 'running') {
      connectWebSocket(job.id)
    }
  }

  if (jobs.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-16">
          <Activity className="h-16 w-16 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No jobs yet</h3>
          <p className="text-muted-foreground text-center">
            Start indexing documentation to see job activity here
          </p>
        </CardContent>
      </Card>
    )
  }

  const runningCount = jobs.filter(j => j.status === 'running').length
  const completedCount = jobs.filter(j => j.status === 'completed').length
  const failedCount = jobs.filter(j => j.status === 'failed').length

  return (
    <>
      {/* Stats and Actions Bar */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4 text-sm">
          <span className="flex items-center gap-1.5">
            <Loader2 className="h-4 w-4 text-primary" />
            <span className="text-muted-foreground">{runningCount} running</span>
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="h-4 w-4 text-green-500" />
            <span className="text-muted-foreground">{completedCount} completed</span>
          </span>
          <span className="flex items-center gap-1.5">
            <XCircle className="h-4 w-4 text-red-500" />
            <span className="text-muted-foreground">{failedCount} failed</span>
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={refreshJobs}
            disabled={isRefreshing}
            className="gap-1.5"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          {(completedCount > 0 || failedCount > 0) && (
            <Button
              variant="outline"
              size="sm"
              onClick={deleteAllCompleted}
              className="gap-1.5 text-red-600 hover:text-red-700 hover:bg-red-50"
            >
              <Trash2 className="h-3.5 w-3.5" />
              Clear Done
            </Button>
          )}
        </div>
      </div>

      <div className="space-y-3">
        {jobs.map((job) => {
          const input = JSON.parse(job.input)
          
          return (
            <Card key={job.id} className="hover:border-primary/50 transition-colors">
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-3">
                      <StatusIcon status={job.status} />
                      <div>
                        <p className="font-medium capitalize">{job.type} Job</p>
                        <p className="text-sm text-muted-foreground">
                          {job.type === 'index' ? input.url : `Query: ${input.query}`}
                        </p>
                      </div>
                    </div>

                    {job.status === 'running' && (
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Progress</span>
                          <span className="font-medium">{job.progress}%</span>
                        </div>
                        <div className="h-2 bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary transition-all duration-300"
                            style={{ width: `${job.progress}%` }}
                          />
                        </div>
                      </div>
                    )}

                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>Created {formatDate(job.createdAt)}</span>
                      {job.completedAt && (
                        <>
                          <span>•</span>
                          <span>Completed {formatDate(job.completedAt)}</span>
                        </>
                      )}
                    </div>
                  </div>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleViewDetails(job)}
                    className="gap-1.5"
                  >
                    <Eye className="h-3.5 w-3.5" />
                    Details
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => deleteJob(job.id, e)}
                    disabled={deletingIds.has(job.id) || job.status === 'running'}
                    className="gap-1.5 text-red-600 hover:text-red-700 hover:bg-red-50"
                    title={job.status === 'running' ? 'Cannot delete running job' : 'Delete job'}
                  >
                    {deletingIds.has(job.id) ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Trash2 className="h-3.5 w-3.5" />
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {selectedJob && (
        <JobDetailsModal
          job={selectedJob}
          onClose={() => {
            setSelectedJob(null)
            ws?.close()
            setWs(null)
          }}
        />
      )}
    </>
  )
}

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case 'completed':
      return <CheckCircle2 className="h-5 w-5 text-green-500" />
    case 'failed':
      return <XCircle className="h-5 w-5 text-red-500" />
    case 'running':
      return <Loader2 className="h-5 w-5 text-primary animate-spin" />
    default:
      return <Clock className="h-5 w-5 text-muted-foreground" />
  }
}

function JobDetailsModal({ job, onClose }: { job: Job; onClose: () => void }) {
  const logs = JSON.parse(job.logs)
  const output = job.output ? JSON.parse(job.output) : null

  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <Card className="max-w-3xl w-full max-h-[80vh] overflow-hidden flex flex-col">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Job Details</CardTitle>
            <Button variant="ghost" size="sm" onClick={onClose}>
              Close
            </Button>
          </div>
        </CardHeader>
        <CardContent className="flex-1 overflow-y-auto space-y-4">
          <div>
            <h4 className="font-semibold mb-2">Status</h4>
            <div className="flex items-center gap-2">
              <StatusIcon status={job.status} />
              <span className="capitalize">{job.status}</span>
              {job.status === 'running' && <span className="text-muted-foreground">({job.progress}%)</span>}
            </div>
          </div>

          <div>
            <h4 className="font-semibold mb-2">Logs</h4>
            <div className="bg-muted rounded-lg p-4 font-mono text-sm space-y-1 max-h-64 overflow-y-auto">
              {logs.map((log: string, i: number) => (
                <div key={i} className="text-muted-foreground">
                  {log}
                </div>
              ))}
            </div>
          </div>

          {output && (
            <div>
              <h4 className="font-semibold mb-2">Result</h4>
              <pre className="bg-muted rounded-lg p-4 text-sm overflow-x-auto">
                {JSON.stringify(output, null, 2)}
              </pre>
            </div>
          )}

          {job.error && (
            <div>
              <h4 className="font-semibold mb-2 text-red-500">Error</h4>
              <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-sm text-red-500">
                {job.error}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
