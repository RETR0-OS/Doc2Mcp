import { auth } from '@clerk/nextjs'
import { NextResponse } from 'next/server'
import { prisma } from '@/lib/db'

export async function GET() {
  try {
    const { userId } = auth()
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const user = await prisma.user.findUnique({
      where: { clerkId: userId },
      include: { tools: { orderBy: { createdAt: 'desc' } } },
    })

    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    return NextResponse.json(user.tools)
  } catch (error) {
    console.error('Error fetching tools:', error)
    return NextResponse.json({ error: 'Failed to fetch tools' }, { status: 500 })
  }
}

export async function POST(request: Request) {
  try {
    const { userId } = auth()
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const body = await request.json()
    const { toolId, name, description, sources } = body

    // Validate required fields
    if (!toolId || !name || !description || !sources) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 })
    }

    // Get or create user
    let user = await prisma.user.findUnique({
      where: { clerkId: userId },
    })

    if (!user) {
      const clerkUser = auth()
      user = await prisma.user.create({
        data: {
          clerkId: userId,
          email: clerkUser.sessionClaims?.email as string || '',
        },
      })
    }

    // Check if tool ID already exists for this user
    const existing = await prisma.tool.findFirst({
      where: {
        userId: user.id,
        toolId: toolId,
      },
    })

    if (existing) {
      return NextResponse.json({ error: 'Tool ID already exists' }, { status: 400 })
    }

    // Create tool
    const tool = await prisma.tool.create({
      data: {
        userId: user.id,
        toolId,
        name,
        description,
        sources: JSON.stringify(sources),
      },
    })

    return NextResponse.json(tool, { status: 201 })
  } catch (error) {
    console.error('Error creating tool:', error)
    return NextResponse.json({ error: 'Failed to create tool' }, { status: 500 })
  }
}
