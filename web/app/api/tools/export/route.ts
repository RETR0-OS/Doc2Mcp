import { NextResponse } from 'next/server'
import { prisma } from '@/lib/db'

/**
 * Public endpoint for MCP server to fetch all enabled tools.
 * No authentication required - this is an internal API for service-to-service communication.
 * 
 * Optional query params:
 * - userId: Filter tools by user ID (for multi-tenant setups)
 */
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const userId = searchParams.get('userId')

    // Build query - get all enabled tools, optionally filtered by user
    const where: { enabled: boolean; userId?: string } = { enabled: true }
    if (userId) {
      // Find internal user ID from clerk ID
      const user = await prisma.user.findUnique({
        where: { clerkId: userId },
      })
      if (user) {
        where.userId = user.id
      }
    }

    const tools = await prisma.tool.findMany({
      where,
      select: {
        toolId: true,
        name: true,
        description: true,
        sources: true,
        enabled: true,
      },
    })

    // Transform to the format expected by doc2mcp config
    const toolsConfig: Record<string, {
      name: string
      description: string
      sources: Array<{ type: string; url?: string; path?: string; patterns?: string[] }>
    }> = {}

    for (const tool of tools) {
      try {
        const sources = JSON.parse(tool.sources)
        toolsConfig[tool.toolId] = {
          name: tool.name,
          description: tool.description,
          sources: sources,
        }
      } catch (e) {
        console.error(`Failed to parse sources for tool ${tool.toolId}:`, e)
      }
    }

    return NextResponse.json({
      tools: toolsConfig,
      settings: {
        max_content_length: 50000,
        cache_ttl: 3600,
      },
    })
  } catch (error) {
    console.error('Error exporting tools:', error)
    return NextResponse.json({ error: 'Failed to export tools' }, { status: 500 })
  }
}
