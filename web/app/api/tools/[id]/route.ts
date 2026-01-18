import { auth } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'
import { prisma } from '@/lib/db'

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const { userId } = await auth()
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const user = await prisma.user.findUnique({
      where: { clerkId: userId },
    })

    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    const tool = await prisma.tool.findFirst({
      where: {
        id,
        userId: user.id,
      },
    })

    if (!tool) {
      return NextResponse.json({ error: 'Tool not found' }, { status: 404 })
    }

    return NextResponse.json(tool)
  } catch (error) {
    console.error('Error fetching tool:', error)
    return NextResponse.json({ error: 'Failed to fetch tool' }, { status: 500 })
  }
}

export async function PUT(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const { userId } = await auth()
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const user = await prisma.user.findUnique({
      where: { clerkId: userId },
    })

    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    const body = await request.json()
    const { name, description, sources } = body

    const tool = await prisma.tool.updateMany({
      where: {
        id,
        userId: user.id,
      },
      data: {
        name,
        description,
        sources: JSON.stringify(sources),
      },
    })

    if (tool.count === 0) {
      return NextResponse.json({ error: 'Tool not found' }, { status: 404 })
    }

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Error updating tool:', error)
    return NextResponse.json({ error: 'Failed to update tool' }, { status: 500 })
  }
}

export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const { userId } = await auth()
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const user = await prisma.user.findUnique({
      where: { clerkId: userId },
    })

    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    const body = await request.json()
    const { enabled } = body

    const tool = await prisma.tool.updateMany({
      where: {
        id,
        userId: user.id,
      },
      data: { enabled },
    })

    if (tool.count === 0) {
      return NextResponse.json({ error: 'Tool not found' }, { status: 404 })
    }

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Error updating tool:', error)
    return NextResponse.json({ error: 'Failed to update tool' }, { status: 500 })
  }
}

export async function DELETE(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const { userId } = await auth()
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const user = await prisma.user.findUnique({
      where: { clerkId: userId },
    })

    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    const tool = await prisma.tool.deleteMany({
      where: {
        id,
        userId: user.id,
      },
    })

    if (tool.count === 0) {
      return NextResponse.json({ error: 'Tool not found' }, { status: 404 })
    }

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Error deleting tool:', error)
    return NextResponse.json({ error: 'Failed to delete tool' }, { status: 500 })
  }
}
