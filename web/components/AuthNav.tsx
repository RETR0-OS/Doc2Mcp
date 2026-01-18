'use client'

import Link from 'next/link'
import { useAuth, SignInButton, SignUpButton, UserButton } from '@clerk/nextjs'
import { Button } from '@/components/ui/button'
import { ArrowRight } from 'lucide-react'

export function AuthNav() {
  const { isSignedIn, isLoaded } = useAuth()

  // Show nothing while loading to prevent flash
  if (!isLoaded) {
    return <div className="w-32 h-10" />
  }

  // If signed in, show dashboard link
  if (isSignedIn) {
    return (
      <div className="flex items-center gap-4">
        <Link href="/dashboard">
          <Button variant="ghost">Dashboard</Button>
        </Link>
        <UserButton afterSignOutUrl="/" />
      </div>
    )
  }

  // Signed out - show auth buttons
  return (
    <div className="flex items-center gap-4">
      <SignInButton mode="modal">
        <Button variant="ghost">Sign In</Button>
      </SignInButton>
      <SignUpButton mode="modal">
        <Button>Get Started</Button>
      </SignUpButton>
    </div>
  )
}

export function HeroAuthButtons() {
  const { isSignedIn, isLoaded } = useAuth()

  // Show nothing while loading
  if (!isLoaded) {
    return <div className="h-12 w-40" />
  }

  // If signed in, show dashboard button
  if (isSignedIn) {
    return (
      <Link href="/dashboard">
        <Button size="lg" className="gap-2">
          Go to Dashboard <ArrowRight className="h-4 w-4" />
        </Button>
      </Link>
    )
  }

  // Signed out - show signup button
  return (
    <SignUpButton mode="modal">
      <Button size="lg" className="gap-2">
        Start Building <ArrowRight className="h-4 w-4" />
      </Button>
    </SignUpButton>
  )
}

export function CTAAuthButtons() {
  const { isSignedIn, isLoaded } = useAuth()

  // Show nothing while loading
  if (!isLoaded) {
    return <div className="h-12 w-40" />
  }

  // If signed in, show dashboard button
  if (isSignedIn) {
    return (
      <Link href="/dashboard">
        <Button size="lg" className="gap-2">
          Go to Dashboard <ArrowRight className="h-4 w-4" />
        </Button>
      </Link>
    )
  }

  // Signed out - show signup button
  return (
    <SignUpButton mode="modal">
      <Button size="lg" className="gap-2">
        Get Started Free <ArrowRight className="h-4 w-4" />
      </Button>
    </SignUpButton>
  )
}
