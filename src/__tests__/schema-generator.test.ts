/**
 * Tests for schema generator
 */

import { describe, it, expect } from 'vitest';
import { SchemaGenerator } from '../generators/schema-generator.js';

describe('SchemaGenerator', () => {
  const generator = new SchemaGenerator();

  it('should generate schema for simple parameters', () => {
    const params = [
      {
        name: 'userId',
        in: 'path' as const,
        required: true,
        type: 'string',
        description: 'User ID',
      },
      {
        name: 'limit',
        in: 'query' as const,
        required: false,
        type: 'number',
        description: 'Page limit',
      },
    ];

    const schema = generator.generateInputSchema(params);
    const jsonSchema = generator.zodToJsonSchema(schema);

    expect(jsonSchema.type).toBe('object');
    expect(jsonSchema.properties.userId.type).toBe('string');
    expect(jsonSchema.properties.limit.type).toBe('number');
    expect(jsonSchema.required).toContain('userId');
    expect(jsonSchema.required).not.toContain('limit');
  });

  it('should handle empty parameters', () => {
    const schema = generator.generateInputSchema([]);
    const jsonSchema = generator.zodToJsonSchema(schema);

    expect(jsonSchema.type).toBe('object');
    expect(jsonSchema.properties).toEqual({});
  });

  it('should convert schema objects to Zod', () => {
    const params = [
      {
        name: 'body',
        in: 'body' as const,
        required: true,
        type: 'object',
        schema: {
          type: 'object',
          properties: {
            name: { type: 'string' },
            age: { type: 'integer', minimum: 0 },
            active: { type: 'boolean' },
          },
          required: ['name'],
        },
      },
    ];

    const schema = generator.generateInputSchema(params);
    const jsonSchema = generator.zodToJsonSchema(schema);

    expect(jsonSchema.properties.body.type).toBe('object');
    expect(jsonSchema.properties.body.properties.name.type).toBe('string');
    expect(jsonSchema.properties.body.properties.age.type).toBe('number');
    expect(jsonSchema.properties.body.properties.active.type).toBe('boolean');
    expect(jsonSchema.properties.body.required).toContain('name');
  });

  it('should handle arrays', () => {
    const params = [
      {
        name: 'tags',
        in: 'query' as const,
        required: false,
        type: 'array',
        schema: {
          type: 'array',
          items: { type: 'string' },
        },
      },
    ];

    const schema = generator.generateInputSchema(params);
    const jsonSchema = generator.zodToJsonSchema(schema);

    expect(jsonSchema.properties.tags.type).toBe('array');
    expect(jsonSchema.properties.tags.items.type).toBe('string');
  });

  it('should handle enums', () => {
    const params = [
      {
        name: 'status',
        in: 'query' as const,
        required: true,
        type: 'string',
        schema: {
          type: 'string',
          enum: ['active', 'inactive', 'pending'],
        },
      },
    ];

    const schema = generator.generateInputSchema(params);
    const jsonSchema = generator.zodToJsonSchema(schema);

    expect(jsonSchema.properties.status.enum).toEqual(['active', 'inactive', 'pending']);
  });
});
