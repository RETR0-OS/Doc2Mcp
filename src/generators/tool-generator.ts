/**
 * Tool generator that creates MCP tools from API documentation
 */

import axios from 'axios';
import { APIDocumentation, APIEndpoint, ParsedTool, ToolHandler } from '../types/index.js';
import { SchemaGenerator } from './schema-generator.js';
import { generateToolName } from '../utils/helpers.js';

export class ToolGenerator {
  private schemaGenerator = new SchemaGenerator();

  /**
   * Generates MCP tools from API documentation
   */
  generateTools(documentation: APIDocumentation): ParsedTool[] {
    return documentation.endpoints.map((endpoint) => this.generateTool(endpoint, documentation));
  }

  /**
   * Generates a single MCP tool from an API endpoint
   */
  private generateTool(endpoint: APIEndpoint, documentation: APIDocumentation): ParsedTool {
    const zodSchema = this.schemaGenerator.generateInputSchema(endpoint.parameters);
    const inputSchema = this.schemaGenerator.zodToJsonSchema(zodSchema);

    const toolName = endpoint.operationId || generateToolName(endpoint.method, endpoint.path);

    const handler: ToolHandler = async (args: Record<string, any>) => {
      return this.executeEndpoint(endpoint, args, documentation.baseUrl);
    };

    return {
      name: toolName,
      description: endpoint.description || endpoint.summary || `${endpoint.method} ${endpoint.path}`,
      inputSchema,
      handler,
      metadata: {
        sourceUrl: documentation.sourceUrl,
        sourceType: documentation.sourceType,
        endpoint,
        generatedAt: new Date(),
      },
    };
  }

  /**
   * Executes an API endpoint with given arguments
   */
  private async executeEndpoint(
    endpoint: APIEndpoint,
    args: Record<string, any>,
    baseUrl?: string
  ): Promise<any> {
    try {
      // Build URL
      let url = endpoint.path;

      // Replace path parameters
      for (const param of endpoint.parameters.filter((p) => p.in === 'path')) {
        if (args[param.name] !== undefined) {
          url = url.replace(`{${param.name}}`, encodeURIComponent(String(args[param.name])));
          url = url.replace(`:${param.name}`, encodeURIComponent(String(args[param.name])));
        }
      }

      // Add base URL if available
      if (baseUrl && !url.startsWith('http')) {
        url = `${baseUrl}${url.startsWith('/') ? '' : '/'}${url}`;
      }

      // Build query parameters
      const queryParams: Record<string, string> = {};
      for (const param of endpoint.parameters.filter((p) => p.in === 'query')) {
        if (args[param.name] !== undefined) {
          queryParams[param.name] = String(args[param.name]);
        }
      }

      // Build headers
      const headers: Record<string, string> = {
        'User-Agent': 'Doc2MCP/1.0.0',
      };
      for (const param of endpoint.parameters.filter((p) => p.in === 'header')) {
        if (args[param.name] !== undefined) {
          headers[param.name] = String(args[param.name]);
        }
      }

      // Get body
      const bodyParam = endpoint.parameters.find((p) => p.in === 'body');
      const body = bodyParam && args[bodyParam.name] !== undefined ? args[bodyParam.name] : undefined;

      if (body && typeof body === 'object') {
        headers['Content-Type'] = 'application/json';
      }

      // Make request
      const response = await axios({
        method: endpoint.method,
        url,
        params: queryParams,
        headers,
        data: body,
        timeout: 30000,
        validateStatus: () => true, // Don't throw on any status
      });

      return {
        status: response.status,
        statusText: response.statusText,
        headers: response.headers,
        data: response.data,
      };
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          `API request failed: ${error.message}${error.response ? ` (${error.response.status})` : ''}`
        );
      }
      throw error;
    }
  }
}
