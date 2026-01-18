import { currentUser } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { prisma } from '@/lib/db'
import { ToolsList } from '@/components/dashboard/ToolsList'
import { Button } from '@/components/ui/button'
import { Plus } from 'lucide-react'
import Link from 'next/link'

export default async function ToolsPage() {
  const user = await currentUser()
  if (!user) redirect('/')

  // Get user from database
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

  // Get user's tools
  const tools = await prisma.tool.findMany({
    where: { userId: dbUser.id },
    orderBy: { createdAt: 'desc' },
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Documentation Tools</h1>
          <p className="text-muted-foreground mt-1">
            Manage your documentation sources for AI search
          </p>
        </div>
        <Link href="/dashboard/tools/new">
          <Button className="gap-2">
            <Plus className="h-4 w-4" />
            Add Tool
          </Button>
        </Link>
      </div>

      <ToolsList tools={tools} userId={dbUser.id} />
    </div>
  )
}
