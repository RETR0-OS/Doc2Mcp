import { auth } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'
import { prisma } from '@/lib/db'

// GET single job
export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const { userId } = auth()
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const user = await prisma.user.findUnique({
      where: { clerkId: userId },
    })

    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    const job = await prisma.job.findFirst({
      where: {
        id: params.id,
        userId: user.id,
      },
    })

    if (!job) {
      return NextResponse.json({ error: 'Job not found' }, { status: 404 })
    }

    return NextResponse.json(job)
  } catch (error) {
    console.error('Error fetching job:', error)
    return NextResponse.json({ error: 'Failed to fetch job' }, { status: 500 })
  }
}

// DELETE job
export async function DELETE(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const { userId } = auth()
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const user = await prisma.user.findUnique({
      where: { clerkId: userId },
    })

    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    // Check job exists and belongs to user
    const job = await prisma.job.findFirst({
      where: {
        id: params.id,
        userId: user.id,
      },
    })

    if (!job) {
      return NextResponse.json({ error: 'Job not found' }, { status: 404 })
    }

    // Delete the job
    await prisma.job.delete({
      where: { id: params.id },
    })

    return NextResponse.json({ success: true, message: 'Job deleted' })
  } catch (error) {
    console.error('Error deleting job:', error)
    return NextResponse.json({ error: 'Failed to delete job' }, { status: 500 })
  }
}
