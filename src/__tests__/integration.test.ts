/**
 * Integration test for Doc2MCP server
 */

import { describe, it, expect } from 'vitest';
import { DocumentationParser } from '../parsers/index.js';
import { ToolGenerator } from '../generators/tool-generator.js';

describe('Doc2MCP Integration', () => {
  it('should parse OpenAPI spec and generate tools', async () => {
    const openApiSpec = `{
      "openapi": "3.0.0",
      "info": {
        "title": "Test API",
        "version": "1.0.0"
      },
      "servers": [{ "url": "https://api.example.com" }],
      "paths": {
        "/users/{id}": {
          "get": {
            "summary": "Get user by ID",
            "operationId": "getUserById",
            "parameters": [
              {
                "name": "id",
                "in": "path",
                "required": true,
                "schema": { "type": "string" }
              }
            ],
            "responses": {
              "200": { "description": "Success" }
            }
          }
        }
      }
    }`;

    const parser = new DocumentationParser();
    const generator = new ToolGenerator();

    // Parse documentation
    const documentation = await parser.parseFromContent(openApiSpec, 'test.json');

    expect(documentation.title).toBe('Test API');
    expect(documentation.endpoints).toHaveLength(1);
    expect(documentation.endpoints[0].operationId).toBe('getUserById');

    // Generate tools
    const tools = generator.generateTools(documentation);

    expect(tools).toHaveLength(1);
    expect(tools[0].name).toBe('getUserById');
    expect(tools[0].description).toBe('Get user by ID');
    expect(tools[0].inputSchema.type).toBe('object');
    expect(tools[0].inputSchema.properties.id).toBeDefined();
    expect(tools[0].inputSchema.required).toContain('id');
  });

  it('should parse Markdown documentation and generate tools', async () => {
    const markdown = `
# API Documentation

## GET /api/users

Retrieves a list of users.

Parameters:
- limit (number): Maximum results to return
`;

    const parser = new DocumentationParser();
    const generator = new ToolGenerator();

    const documentation = await parser.parseFromContent(markdown, 'docs.md');

    expect(documentation.sourceType).toBe('markdown');
    expect(documentation.endpoints.length).toBeGreaterThan(0);

    const tools = generator.generateTools(documentation);
    expect(tools.length).toBeGreaterThan(0);
  });

  it('should parse HTML documentation and generate tools', async () => {
    const html = `
<!DOCTYPE html>
<html>
<head><title>API Documentation</title></head>
<body>
  <h1>API Reference</h1>
  <h2>GET /api/status</h2>
  <p>Returns the status of the API</p>
  <code>GET /api/status</code>
</body>
</html>
`;

    const parser = new DocumentationParser();
    const generator = new ToolGenerator();

    const documentation = await parser.parseFromContent(html, 'docs.html');

    expect(documentation.sourceType).toBe('html');
    expect(documentation.endpoints.length).toBeGreaterThan(0);

    const tools = generator.generateTools(documentation);
    expect(tools.length).toBeGreaterThan(0);
  });
});
