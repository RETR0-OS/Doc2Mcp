/**
 * Zod schema generator from API documentation
 */

import { z } from 'zod';
import { APIParameter } from '../types/index.js';

export class SchemaGenerator {
  /**
   * Generates a Zod schema from API parameters
   */
  generateInputSchema(parameters: APIParameter[]): z.ZodObject<any> {
    const shape: Record<string, z.ZodTypeAny> = {};

    for (const param of parameters) {
      const zodType = this.getZodTypeForParameter(param);

      if (param.required) {
        shape[param.name] = zodType;
      } else {
        shape[param.name] = zodType.optional();
      }
    }

    // If no parameters, return empty object schema
    if (Object.keys(shape).length === 0) {
      return z.object({});
    }

    return z.object(shape);
  }

  /**
   * Converts parameter type to Zod type
   */
  private getZodTypeForParameter(param: APIParameter): z.ZodTypeAny {
    const schema = param.schema;

    // Handle schema-based types (OpenAPI 3.0)
    if (schema) {
      return this.schemaToZod(schema);
    }

    // Handle simple types
    switch (param.type.toLowerCase()) {
      case 'string':
        return z.string().describe(param.description || '');
      case 'number':
      case 'integer':
        return z.number().describe(param.description || '');
      case 'boolean':
        return z.boolean().describe(param.description || '');
      case 'array':
        return z.array(z.any()).describe(param.description || '');
      case 'object':
        return z.record(z.any()).describe(param.description || '');
      default:
        return z.any().describe(param.description || '');
    }
  }

  /**
   * Converts JSON Schema to Zod schema
   */
  private schemaToZod(schema: any): z.ZodTypeAny {
    if (!schema || !schema.type) {
      return z.any();
    }

    const description = schema.description || '';

    switch (schema.type) {
      case 'string': {
        if (schema.enum && Array.isArray(schema.enum) && schema.enum.length > 0) {
          return z.enum(schema.enum as [string, ...string[]]).describe(description);
        }
        let stringSchema = z.string();
        if (schema.minLength) {
          stringSchema = stringSchema.min(schema.minLength);
        }
        if (schema.maxLength) {
          stringSchema = stringSchema.max(schema.maxLength);
        }
        if (schema.pattern) {
          stringSchema = stringSchema.regex(new RegExp(schema.pattern));
        }
        return stringSchema.describe(description);
      }

      case 'number':
      case 'integer': {
        let numberSchema = z.number();
        if (schema.minimum !== undefined) {
          numberSchema = numberSchema.min(schema.minimum);
        }
        if (schema.maximum !== undefined) {
          numberSchema = numberSchema.max(schema.maximum);
        }
        if (schema.type === 'integer') {
          numberSchema = numberSchema.int();
        }
        return numberSchema.describe(description);
      }

      case 'boolean':
        return z.boolean().describe(description);

      case 'array': {
        const itemSchema = schema.items ? this.schemaToZod(schema.items) : z.any();
        let arraySchema = z.array(itemSchema);
        if (schema.minItems) {
          arraySchema = arraySchema.min(schema.minItems);
        }
        if (schema.maxItems) {
          arraySchema = arraySchema.max(schema.maxItems);
        }
        return arraySchema.describe(description);
      }

      case 'object':
        if (schema.properties) {
          const shape: Record<string, z.ZodTypeAny> = {};
          for (const [key, value] of Object.entries(schema.properties)) {
            const propSchema = this.schemaToZod(value);
            if (schema.required && schema.required.includes(key)) {
              shape[key] = propSchema;
            } else {
              shape[key] = propSchema.optional();
            }
          }
          return z.object(shape).describe(description);
        }
        return z.record(z.any()).describe(description);

      default:
        return z.any().describe(description);
    }
  }

  /**
   * Generates JSON schema from Zod schema for MCP
   */
  zodToJsonSchema(zodSchema: z.ZodObject<any>): Record<string, any> {
    const shape = zodSchema.shape;
    const properties: Record<string, any> = {};
    const required: string[] = [];

    for (const [key, value] of Object.entries(shape)) {
      const zodType = value as z.ZodTypeAny;

      // Check if required
      if (!(zodType instanceof z.ZodOptional)) {
        required.push(key);
      }

      // Convert to JSON Schema
      properties[key] = this.zodTypeToJsonSchema(zodType);
    }

    return {
      type: 'object',
      properties,
      required: required.length > 0 ? required : undefined,
    };
  }

  private zodTypeToJsonSchema(zodType: z.ZodTypeAny): any {
    // Unwrap optional
    if (zodType instanceof z.ZodOptional) {
      return this.zodTypeToJsonSchema(zodType.unwrap());
    }

    // Get description
    const description = zodType.description;

    if (zodType instanceof z.ZodString) {
      return { type: 'string', description };
    }
    if (zodType instanceof z.ZodNumber) {
      return { type: 'number', description };
    }
    if (zodType instanceof z.ZodBoolean) {
      return { type: 'boolean', description };
    }
    if (zodType instanceof z.ZodArray) {
      return {
        type: 'array',
        items: this.zodTypeToJsonSchema(zodType.element),
        description,
      };
    }
    if (zodType instanceof z.ZodObject) {
      const shape = zodType.shape;
      const properties: Record<string, any> = {};
      const required: string[] = [];

      for (const [key, value] of Object.entries(shape)) {
        const innerType = value as z.ZodTypeAny;
        if (!(innerType instanceof z.ZodOptional)) {
          required.push(key);
        }
        properties[key] = this.zodTypeToJsonSchema(innerType);
      }

      return {
        type: 'object',
        properties,
        required: required.length > 0 ? required : undefined,
        description,
      };
    }
    if (zodType instanceof z.ZodEnum) {
      return {
        type: 'string',
        enum: zodType.options,
        description,
      };
    }

    return { type: 'string', description };
  }
}
