/**
 * OpenAPI/Swagger documentation parser
 */

import YAML from 'yaml';
import { APIDocumentation, APIEndpoint, APIParameter, APIResponse } from '../types/index.js';
import { safeJsonParse } from '../utils/helpers.js';

export class OpenAPIParser {
  /**
   * Parses OpenAPI/Swagger documentation
   */
  async parse(content: string, sourceUrl: string): Promise<APIDocumentation> {
    let spec: any;

    // Try parsing as JSON first, then YAML
    try {
      spec = safeJsonParse(content);
    } catch {
      try {
        spec = YAML.parse(content);
      } catch (error) {
        throw new Error(
          `Failed to parse OpenAPI spec: ${error instanceof Error ? error.message : 'Unknown error'}`
        );
      }
    }

    // Determine OpenAPI version
    const isOpenAPI3 = spec.openapi && spec.openapi.startsWith('3.');
    const isSwagger2 = spec.swagger && spec.swagger.startsWith('2.');

    if (!isOpenAPI3 && !isSwagger2) {
      throw new Error('Unsupported API specification format');
    }

    const endpoints: APIEndpoint[] = [];
    const paths = spec.paths || {};

    // Extract base URL
    let baseUrl = '';
    if (isOpenAPI3 && spec.servers && spec.servers.length > 0) {
      baseUrl = spec.servers[0].url;
    } else if (isSwagger2) {
      const schemes = spec.schemes || ['https'];
      const host = spec.host || '';
      const basePath = spec.basePath || '';
      baseUrl = `${schemes[0]}://${host}${basePath}`;
    }

    // Parse endpoints
    for (const [path, pathItem] of Object.entries(paths)) {
      const methods = ['get', 'post', 'put', 'delete', 'patch', 'options', 'head'];

      for (const method of methods) {
        const operation = (pathItem as any)[method];
        if (!operation) continue;

        const parameters = this.parseParameters(
          operation.parameters || [],
          (pathItem as any).parameters || [],
          isOpenAPI3
        );

        const responses = this.parseResponses(operation.responses || {});

        endpoints.push({
          path,
          method: method.toUpperCase(),
          description: operation.description || operation.summary || `${method.toUpperCase()} ${path}`,
          summary: operation.summary,
          operationId: operation.operationId,
          parameters,
          responses,
          tags: operation.tags,
        });
      }
    }

    return {
      title: spec.info?.title || 'API Documentation',
      description: spec.info?.description,
      version: spec.info?.version,
      baseUrl,
      endpoints,
      sourceUrl,
      sourceType: 'openapi',
    };
  }

  private parseParameters(
    operationParams: any[],
    pathParams: any[],
    isOpenAPI3: boolean
  ): APIParameter[] {
    const allParams = [...pathParams, ...operationParams];
    const parameters: APIParameter[] = [];

    for (const param of allParams) {
      // Handle OpenAPI 3.0 request body
      if (param.in === 'body' || param.requestBody) {
        const bodyParam = param.requestBody || param;
        const content = bodyParam.content || {};
        const jsonContent = content['application/json'] || Object.values(content)[0];

        if (jsonContent) {
          parameters.push({
            name: param.name || 'body',
            in: 'body',
            description: bodyParam.description || param.description,
            required: param.required || bodyParam.required || false,
            type: 'object',
            schema: jsonContent.schema || param.schema,
            example: jsonContent.example,
          });
        }
      } else {
        // Regular parameter (query, path, header)
        const schema = isOpenAPI3 ? param.schema : param;
        parameters.push({
          name: param.name,
          in: param.in,
          description: param.description,
          required: param.required || param.in === 'path',
          type: schema?.type || 'string',
          schema: schema,
          example: param.example || schema?.example,
        });
      }
    }

    return parameters;
  }

  private parseResponses(responses: Record<string, any>): APIResponse[] {
    const result: APIResponse[] = [];

    for (const [statusCode, response] of Object.entries(responses)) {
      const code = parseInt(statusCode);
      if (isNaN(code)) continue;

      const content = response.content || {};
      const jsonContent = content['application/json'] || Object.values(content)[0];

      result.push({
        statusCode: code,
        description: response.description || `Response ${statusCode}`,
        schema: jsonContent?.schema || response.schema,
        example: jsonContent?.example || response.example,
      });
    }

    return result;
  }
}
