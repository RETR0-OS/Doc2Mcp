import { currentUser } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { ToolForm } from '@/components/dashboard/ToolForm'

export default async function NewToolPage() {
  const user = await currentUser()
  if (!user) redirect('/')

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Add Documentation Tool</h1>
        <p className="text-muted-foreground mt-1">
          Configure a new documentation source for AI search
        </p>
      </div>

      <ToolForm />
    </div>
  )
}
