/**
 * Core types for Doc2MCP
 */

export interface APIEndpoint {
  path: string;
  method: string;
  description: string;
  parameters: APIParameter[];
  responses: APIResponse[];
  tags?: string[];
  operationId?: string;
  summary?: string;
}

export interface APIParameter {
  name: string;
  in: 'query' | 'path' | 'header' | 'body';
  description?: string;
  required: boolean;
  type: string;
  schema?: Record<string, any>;
  example?: any;
}

export interface APIResponse {
  statusCode: number;
  description: string;
  schema?: Record<string, any>;
  example?: any;
}

export interface APIDocumentation {
  title: string;
  description?: string;
  version?: string;
  baseUrl?: string;
  endpoints: APIEndpoint[];
  sourceUrl: string;
  sourceType: 'openapi' | 'html' | 'markdown';
}

export interface ParsedTool {
  name: string;
  description: string;
  inputSchema: Record<string, any>;
  handler: ToolHandler;
  metadata: ToolMetadata;
}

export interface ToolMetadata {
  sourceUrl: string;
  sourceType: string;
  endpoint: APIEndpoint;
  generatedAt: Date;
}

export type ToolHandler = (args: Record<string, any>) => Promise<any>;

export interface ParserOptions {
  validateSchema?: boolean;
  includeExamples?: boolean;
  strictMode?: boolean;
}
