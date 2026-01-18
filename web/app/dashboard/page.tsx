import { currentUser } from '@clerk/nextjs/server'
import { prisma } from '@/lib/db'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Wrench, Activity, Database, TrendingUp } from 'lucide-react'

export default async function DashboardPage() {
  const user = await currentUser()
  if (!user) return null

  // Get user from database or create if doesn't exist
  let dbUser = await prisma.user.findUnique({
    where: { clerkId: user.id },
    include: {
      _count: {
        select: { tools: true, jobs: true },
      },
    },
  })

  if (!dbUser) {
    dbUser = await prisma.user.create({
      data: {
        clerkId: user.id,
        email: user.emailAddresses[0].emailAddress,
      },
      include: {
        _count: {
          select: { tools: true, jobs: true },
        },
      },
    })
  }

  // Get recent jobs
  const recentJobsRaw = await prisma.job.findMany({
    where: { userId: dbUser.id },
    orderBy: { createdAt: 'desc' },
    take: 5,
  })

  // Serialize dates to strings for client component compatibility
  const recentJobs = recentJobsRaw.map(job => ({
    ...job,
    createdAt: job.createdAt.toISOString(),
    startedAt: job.startedAt?.toISOString() ?? null,
    completedAt: job.completedAt?.toISOString() ?? null,
  }))

  const completedJobs = recentJobs.filter(j => j.status === 'completed').length
  const runningJobs = recentJobs.filter(j => j.status === 'running').length

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold mb-2">Welcome back{user.firstName ? `, ${user.firstName}` : ''}!</h1>
        <p className="text-muted-foreground">
          Here's what's happening with your documentation tools
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Tools"
          value={dbUser._count.tools}
          description="Documentation sources"
          icon={<Wrench className="h-5 w-5 text-primary" />}
        />
        <StatCard
          title="Total Jobs"
          value={dbUser._count.jobs}
          description="Indexing & searches"
          icon={<Activity className="h-5 w-5 text-primary" />}
        />
        <StatCard
          title="Running Jobs"
          value={runningJobs}
          description="Currently executing"
          icon={<TrendingUp className="h-5 w-5 text-primary" />}
        />
        <StatCard
          title="Completed"
          value={completedJobs}
          description="Last 5 jobs"
          icon={<Database className="h-5 w-5 text-primary" />}
        />
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Jobs</CardTitle>
          <CardDescription>Your latest indexing and search operations</CardDescription>
        </CardHeader>
        <CardContent>
          {recentJobs.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">
              No jobs yet. Start by adding a tool and indexing some documentation!
            </p>
          ) : (
            <div className="space-y-3">
              {recentJobs.map((job) => (
                <div key={job.id} className="flex items-center justify-between p-3 rounded-lg border border-border hover:bg-muted/50 transition-colors">
                  <div className="flex-1">
                    <p className="font-medium capitalize">{job.type}</p>
                    <p className="text-sm text-muted-foreground">
                      {new Date(job.createdAt).toLocaleString()}
                    </p>
                  </div>
                  <StatusBadge status={job.status} />
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function StatCard({ title, value, description, icon }: {
  title: string
  value: number
  description: string
  icon: React.ReactNode
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold">{value}</div>
        <p className="text-xs text-muted-foreground mt-1">{description}</p>
      </CardContent>
    </Card>
  )
}

function StatusBadge({ status }: { status: string }) {
  const colors = {
    pending: 'bg-secondary text-secondary-foreground',
    running: 'bg-primary text-white',
    completed: 'bg-green-500/20 text-green-500',
    failed: 'bg-red-500/20 text-red-500',
    cancelled: 'bg-muted text-muted-foreground',
  }

  return (
    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${colors[status as keyof typeof colors] || colors.pending}`}>
      {status}
    </span>
  )
}
