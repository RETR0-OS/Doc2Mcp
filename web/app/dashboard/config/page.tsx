import { currentUser } from '@clerk/nextjs'
import { redirect } from 'next/navigation'
import { prisma } from '@/lib/db'
import { ConfigGenerator } from '@/components/dashboard/ConfigGenerator'

export default async function ConfigPage() {
  const user = await currentUser()
  if (!user) redirect('/')

  let dbUser = await prisma.user.findUnique({
    where: { clerkId: user.id },
    include: {
      tools: {
        where: { enabled: true },
        orderBy: { createdAt: 'asc' },
      },
    },
  })

  if (!dbUser) {
    dbUser = await prisma.user.create({
      data: {
        clerkId: user.id,
        email: user.emailAddresses[0].emailAddress,
      },
      include: { tools: true },
    })
  }

  return (
    <div className="max-w-4xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold">VS Code MCP Configuration</h1>
        <p className="text-muted-foreground mt-1">
          Copy this configuration to use Doc2MCP in VS Code with GitHub Copilot
        </p>
      </div>

      <ConfigGenerator tools={dbUser.tools} userEmail={dbUser.email} />
    </div>
  )
}
