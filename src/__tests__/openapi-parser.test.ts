/**
 * Tests for OpenAPI parser
 */

import { describe, it, expect } from 'vitest';
import { OpenAPIParser } from '../parsers/openapi-parser.js';

describe('OpenAPIParser', () => {
  const parser = new OpenAPIParser();

  it('should parse OpenAPI 3.0 specification', async () => {
    const spec = JSON.stringify({
      openapi: '3.0.0',
      info: {
        title: 'Test API',
        version: '1.0.0',
      },
      servers: [{ url: 'https://api.example.com' }],
      paths: {
        '/users': {
          get: {
            summary: 'List users',
            operationId: 'listUsers',
            parameters: [
              {
                name: 'limit',
                in: 'query',
                schema: { type: 'integer' },
                required: false,
              },
            ],
            responses: {
              '200': {
                description: 'Success',
              },
            },
          },
          post: {
            summary: 'Create user',
            operationId: 'createUser',
            requestBody: {
              description: 'User to create',
              required: true,
              content: {
                'application/json': {
                  schema: {
                    type: 'object',
                    properties: {
                      name: { type: 'string' },
                      email: { type: 'string' },
                    },
                    required: ['name', 'email'],
                  },
                },
              },
            },
            responses: {
              '201': {
                description: 'Created',
              },
            },
          },
        },
      },
    });

    const result = await parser.parse(spec, 'https://api.example.com/openapi.json');

    expect(result.title).toBe('Test API');
    expect(result.version).toBe('1.0.0');
    expect(result.baseUrl).toBe('https://api.example.com');
    expect(result.endpoints).toHaveLength(2);

    // Test GET endpoint
    const getEndpoint = result.endpoints.find((e) => e.method === 'GET');
    expect(getEndpoint?.path).toBe('/users');
    expect(getEndpoint?.operationId).toBe('listUsers');
    expect(getEndpoint?.parameters).toHaveLength(1);
    expect(getEndpoint?.parameters[0].name).toBe('limit');

    // Test POST endpoint with request body
    const postEndpoint = result.endpoints.find((e) => e.method === 'POST');
    expect(postEndpoint?.path).toBe('/users');
    expect(postEndpoint?.operationId).toBe('createUser');
    expect(postEndpoint?.parameters).toHaveLength(1);
    expect(postEndpoint?.parameters[0].name).toBe('body');
    expect(postEndpoint?.parameters[0].in).toBe('body');
    expect(postEndpoint?.parameters[0].required).toBe(true);
    expect(postEndpoint?.parameters[0].schema?.type).toBe('object');
  });

  it('should parse Swagger 2.0 specification', async () => {
    const spec = JSON.stringify({
      swagger: '2.0',
      info: {
        title: 'Test API',
        version: '1.0.0',
      },
      host: 'api.example.com',
      basePath: '/v1',
      schemes: ['https'],
      paths: {
        '/users/{id}': {
          get: {
            summary: 'Get user',
            parameters: [
              {
                name: 'id',
                in: 'path',
                type: 'string',
                required: true,
              },
            ],
            responses: {
              '200': {
                description: 'Success',
              },
            },
          },
        },
      },
    });

    const result = await parser.parse(spec, 'https://api.example.com/swagger.json');

    expect(result.title).toBe('Test API');
    expect(result.baseUrl).toBe('https://api.example.com/v1');
    expect(result.endpoints).toHaveLength(1);
    expect(result.endpoints[0].path).toBe('/users/{id}');
    expect(result.endpoints[0].parameters[0].name).toBe('id');
    expect(result.endpoints[0].parameters[0].required).toBe(true);
  });

  it('should handle YAML format', async () => {
    const spec = `
openapi: 3.0.0
info:
  title: Test API
  version: 1.0.0
paths:
  /health:
    get:
      summary: Health check
      responses:
        '200':
          description: OK
`;

    const result = await parser.parse(spec, 'https://api.example.com/openapi.yaml');

    expect(result.title).toBe('Test API');
    expect(result.endpoints).toHaveLength(1);
    expect(result.endpoints[0].path).toBe('/health');
  });

  it('should throw error for invalid format', async () => {
    await expect(parser.parse('invalid', 'test.json')).rejects.toThrow();
  });
});
