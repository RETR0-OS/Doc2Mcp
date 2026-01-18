import { currentUser } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { prisma } from '@/lib/db'
import { ToolDetail } from '@/components/dashboard/ToolDetail'

export default async function ToolDetailPage({
  params,
}: {
  params: { id: string }
}) {
  const user = await currentUser()
  if (!user) redirect('/')

  // Get user from database
  const dbUser = await prisma.user.findUnique({
    where: { clerkId: user.id },
  })

  if (!dbUser) {
    redirect('/dashboard/tools')
  }

  // Get the tool
  const tool = await prisma.tool.findFirst({
    where: {
      id: params.id,
      userId: dbUser.id,
    },
  })

  if (!tool) {
    notFound()
  }

  // Get related jobs for this tool
  const jobs = await prisma.job.findMany({
    where: {
      userId: dbUser.id,
      input: {
        contains: tool.toolId,
      },
    },
    orderBy: { createdAt: 'desc' },
    take: 10,
  })

  // Serialize dates
  const serializedTool = {
    ...tool,
    createdAt: tool.createdAt.toISOString(),
    updatedAt: tool.updatedAt.toISOString(),
  }

  const serializedJobs = jobs.map(job => ({
    ...job,
    createdAt: job.createdAt.toISOString(),
    startedAt: job.startedAt?.toISOString() || null,
    completedAt: job.completedAt?.toISOString() || null,
  }))

  return (
    <ToolDetail 
      tool={serializedTool} 
      jobs={serializedJobs}
    />
  )
}
