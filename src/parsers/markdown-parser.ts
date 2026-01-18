/**
 * Markdown documentation parser
 */

import { marked } from 'marked';
import { APIDocumentation, APIEndpoint, APIParameter } from '../types/index.js';

export class MarkdownParser {
  /**
   * Parses Markdown documentation
   */
  async parse(content: string, sourceUrl: string): Promise<APIDocumentation> {
    const tokens = marked.lexer(content);
    const endpoints: APIEndpoint[] = [];

    let title = 'API Documentation';
    let description = '';

    // Extract title from first heading
    const firstHeading = tokens.find((t) => t.type === 'heading' && t.depth === 1);
    if (firstHeading && 'text' in firstHeading) {
      title = firstHeading.text;
    }

    // Extract description from first paragraph
    const firstParagraph = tokens.find((t) => t.type === 'paragraph');
    if (firstParagraph && 'text' in firstParagraph) {
      description = firstParagraph.text;
    }

    const methodPattern = /\b(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD)\b/gi;
    const pathPattern = /`([^`]*\/[^`]+)`|(\S*\/\S+)/g;

    // Parse tokens to find endpoints
    for (let i = 0; i < tokens.length; i++) {
      const token = tokens[i];

      if (token.type === 'heading' && 'text' in token) {
        const headingText = token.text;
        const methods = headingText.match(methodPattern);
        const pathMatches = [...headingText.matchAll(pathPattern)];

        if (methods && pathMatches.length > 0) {
          const method = methods[0];
          const path = pathMatches[0][1] || pathMatches[0][2];

          // Get description from following paragraph
          let endpointDescription = headingText;
          if (i + 1 < tokens.length && tokens[i + 1].type === 'paragraph') {
            const nextToken = tokens[i + 1];
            if ('text' in nextToken) {
              endpointDescription = nextToken.text;
            }
          }

          // Extract parameters
          const parameters = this.extractParameters(tokens, i);

          endpoints.push({
            path,
            method: method.toUpperCase(),
            description: endpointDescription,
            parameters,
            responses: [
              {
                statusCode: 200,
                description: 'Successful response',
              },
            ],
          });
        }
      }

      // Also check code blocks for endpoint definitions
      if (token.type === 'code') {
        const codeText = 'text' in token ? token.text : '';
        const methods = codeText.match(methodPattern);
        const pathMatches = [...codeText.matchAll(pathPattern)];

        if (methods && pathMatches.length > 0) {
          const method = methods[0];
          const path = pathMatches[0][1] || pathMatches[0][2];

          endpoints.push({
            path,
            method: method.toUpperCase(),
            description: `${method} ${path}`,
            parameters: [],
            responses: [
              {
                statusCode: 200,
                description: 'Successful response',
              },
            ],
          });
        }
      }
    }

    return {
      title,
      description,
      endpoints,
      sourceUrl,
      sourceType: 'markdown',
    };
  }

  private extractParameters(tokens: any[], startIndex: number): APIParameter[] {
    const parameters: APIParameter[] = [];

    // Look ahead for lists or tables that might contain parameters
    for (let i = startIndex + 1; i < Math.min(startIndex + 10, tokens.length); i++) {
      const token = tokens[i];

      // Stop at next heading
      if (token.type === 'heading') break;

      // Check for parameter lists
      if (token.type === 'list' && 'items' in token) {
        for (const item of token.items) {
          if ('text' in item) {
            const text = item.text;
            // Look for patterns like "name (type): description" or "name - description"
            const paramMatch = text.match(/`?([a-zA-Z0-9_]+)`?\s*(?:\(([^)]+)\))?\s*[:-]\s*(.+)/);
            if (paramMatch) {
              const [, name, type, desc] = paramMatch;
              parameters.push({
                name,
                in: 'query',
                description: desc.trim(),
                required: text.toLowerCase().includes('required'),
                type: type || 'string',
              });
            }
          }
        }
      }

      // Check for parameter tables
      if (token.type === 'table' && 'rows' in token) {
        for (const row of token.rows) {
          if (row.length >= 2) {
            const nameCell = row[0];
            const descCell = row[1];
            const name = 'text' in nameCell ? nameCell.text : '';
            const desc = 'text' in descCell ? descCell.text : '';

            if (name) {
              parameters.push({
                name: name.replace(/`/g, ''),
                in: 'query',
                description: desc,
                required: desc.toLowerCase().includes('required'),
                type: 'string',
              });
            }
          }
        }
      }
    }

    return parameters;
  }
}
