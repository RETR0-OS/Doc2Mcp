import { currentUser } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { prisma } from '@/lib/db'
import { JobsList } from '@/components/dashboard/JobsList'

export default async function JobsPage() {
  const user = await currentUser()
  if (!user) redirect('/')

  let dbUser = await prisma.user.findUnique({
    where: { clerkId: user.id },
  })

  if (!dbUser) {
    dbUser = await prisma.user.create({
      data: {
        clerkId: user.id,
        email: user.emailAddresses[0].emailAddress,
      },
    })
  }

  const jobs = await prisma.job.findMany({
    where: { userId: dbUser.id },
    orderBy: { createdAt: 'desc' },
    take: 50,
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Background Jobs</h1>
        <p className="text-muted-foreground mt-1">
          Monitor indexing and search operations in real-time
        </p>
      </div>

      <JobsList jobs={jobs} />
    </div>
  )
}
