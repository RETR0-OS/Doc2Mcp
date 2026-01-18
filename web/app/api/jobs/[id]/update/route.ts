import { prisma } from '@/lib/db'
import { NextResponse } from 'next/server'

// Internal endpoint for FastAPI to update job status
// No auth required - only accessible from internal network
export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const body = await request.json()
    
    console.log(`[Job Update] Updating job ${id}:`, body)
    
    const { status, progress, logs, result, error } = body
    
    // Check if job exists first
    const existingJob = await prisma.job.findUnique({
      where: { id }
    })
    
    if (!existingJob) {
      console.error(`[Job Update] Job ${id} not found`)
      return NextResponse.json(
        { error: 'Job not found' },
        { status: 404 }
      )
    }
    
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
    
    console.log(`[Job Update] Job ${id} updated successfully`)
    return NextResponse.json({ success: true, job })
  } catch (error) {
    console.error('Failed to update job:', error)
    return NextResponse.json(
      { error: 'Failed to update job', details: String(error) },
      { status: 500 }
    )
  }
}
