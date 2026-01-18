import { currentUser } from '@clerk/nextjs/server'
import { Sidebar } from '@/components/dashboard/Sidebar'

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const user = await currentUser()

  // Middleware handles the redirect, this is just a safety check
  if (!user) {
    return null
  }

  // Serialize only the needed user data for client component
  const userData = {
    firstName: user.firstName,
    email: user.emailAddresses[0]?.emailAddress ?? '',
  }

  return (
    <div className="min-h-screen flex">
      <Sidebar user={userData} />
      <main className="flex-1 ml-64">
        <div className="p-8">
          {children}
        </div>
      </main>
    </div>
  )
}
