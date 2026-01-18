import { prisma } from '@/lib/db'
import { NextResponse } from 'next/server'

// Internal endpoint for FastAPI to update job status
// No auth required - only accessible from internal network
export async function POST(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params
    const body = await request.json()
    
    const { status, progress, logs, result, error } = body
    
    // Build update data
    const updateData: any = {}
    
    if (status !== undefined) {
      updateData.status = status
    }
    
    if (progress !== undefined) {
      updateData.progress = progress
    }
    
    if (logs !== undefined) {
      // Logs come as array, store as JSON string
      updateData.logs = JSON.stringify(logs)
    }
    
    if (result !== undefined) {
      updateData.result = JSON.stringify(result)
    }
    
    if (error !== undefined) {
      updateData.error = error
    }
    
    // Update completed/failed timestamps
    if (status === 'completed' || status === 'failed') {
      updateData.completedAt = new Date()
    }
    
    const job = await prisma.job.update({
      where: { id },
      data: updateData
    })
    
    return NextResponse.json({ success: true, job })
  } catch (error) {
    console.error('Failed to update job:', error)
    return NextResponse.json(
      { error: 'Failed to update job' },
      { status: 500 }
    )
  }
}
