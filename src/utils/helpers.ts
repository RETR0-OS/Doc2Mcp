/**
 * Utility functions for Doc2MCP
 */

import axios from 'axios';

/**
 * Fetches content from a URL
 */
export async function fetchUrl(url: string): Promise<string> {
  try {
    const response = await axios.get(url, {
      headers: {
        'User-Agent': 'Doc2MCP/1.0.0',
      },
      timeout: 30000,
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(`Failed to fetch URL ${url}: ${error.message}`);
    }
    throw error;
  }
}

/**
 * Determines the documentation type from URL or content
 */
export function detectDocumentationType(
  url: string,
  content: string
): 'openapi' | 'html' | 'markdown' {
  // Check URL patterns
  if (
    url.includes('swagger') ||
    url.includes('openapi') ||
    url.endsWith('.json') ||
    url.endsWith('.yaml') ||
    url.endsWith('.yml')
  ) {
    return 'openapi';
  }

  // Check content
  if (content.trim().startsWith('{') || content.trim().startsWith('openapi:')) {
    return 'openapi';
  }

  if (content.includes('<html') || content.includes('<!DOCTYPE html')) {
    return 'html';
  }

  return 'markdown';
}

/**
 * Sanitizes a name to be a valid JavaScript identifier
 */
export function sanitizeName(name: string): string {
  return name
    .replace(/[^a-zA-Z0-9_]/g, '_')
    .replace(/^[0-9]/, '_$&')
    .replace(/_+/g, '_');
}

/**
 * Converts HTTP method and path to a tool name
 */
export function generateToolName(method: string, path: string): string {
  const parts = path.split('/').filter((p) => p && !p.startsWith('{'));
  const methodLower = method.toLowerCase();
  const pathPart = parts.map((p) => p.charAt(0).toUpperCase() + p.slice(1)).join('');
  return sanitizeName(`${methodLower}${pathPart}`);
}

/**
 * Safely parses JSON with error handling
 */
export function safeJsonParse(content: string): any {
  try {
    return JSON.parse(content);
  } catch (error) {
    throw new Error(`Invalid JSON: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}
