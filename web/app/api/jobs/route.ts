import { auth } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'
import { prisma } from '@/lib/db'

const API_URL = process.env.API_URL || 'http://localhost:8000'

export async function GET() {
  try {
    const { userId } = auth()
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const user = await prisma.user.findUnique({
      where: { clerkId: userId },
      include: {
        jobs: {
          orderBy: { createdAt: 'desc' },
          take: 50,
        },
      },
    })

    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    return NextResponse.json(user.jobs)
  } catch (error) {
    console.error('Error fetching jobs:', error)
    return NextResponse.json({ error: 'Failed to fetch jobs' }, { status: 500 })
  }
}

export async function POST(request: Request) {
  try {
    const { userId } = auth()
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const body = await request.json()
    const { type, toolId, query, url } = body

    // Get or create user
    let user = await prisma.user.findUnique({
      where: { clerkId: userId },
    })

    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    // Get tool
    const tool = await prisma.tool.findFirst({
      where: {
        userId: user.id,
        toolId: toolId,
      },
    })

    if (!tool) {
      return NextResponse.json({ error: 'Tool not found' }, { status: 404 })
    }

    // Create job in database
    const job = await prisma.job.create({
      data: {
        userId: user.id,
        type,
        status: 'pending',
        input: JSON.stringify({ toolId, query, url }),
      },
    })

    // Start job in FastAPI backend
    const endpoint = type === 'index' ? '/index' : '/search'
    const payload = type === 'index'
      ? { job_id: job.id, user_id: user.id, tool_id: toolId, url }
      : { 
          job_id: job.id, 
          user_id: user.id, 
          tool_id: toolId,
          tool_name: tool.name,
          tool_description: tool.description,
          query 
        }

    try {
      const res = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!res.ok) {
        throw new Error('Failed to start job in backend')
      }

      // Update job status
      await prisma.job.update({
        where: { id: job.id },
        data: {
          status: 'running',
          startedAt: new Date(),
        },
      })
    } catch (error) {
      // Mark job as failed
      await prisma.job.update({
        where: { id: job.id },
        data: {
          status: 'failed',
          error: 'Failed to start job in backend',
        },
      })
      throw error
    }

    return NextResponse.json(job, { status: 201 })
  } catch (error) {
    console.error('Error creating job:', error)
    return NextResponse.json({ error: 'Failed to create job' }, { status: 500 })
  }
}
