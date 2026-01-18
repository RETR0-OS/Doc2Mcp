/**
 * HTML documentation parser
 */

import * as cheerio from 'cheerio';
import { APIDocumentation, APIEndpoint, APIParameter } from '../types/index.js';

export class HTMLParser {
  /**
   * Parses HTML documentation
   */
  async parse(content: string, sourceUrl: string): Promise<APIDocumentation> {
    const $ = cheerio.load(content);
    const endpoints: APIEndpoint[] = [];

    // Extract title
    const title = $('title').text() || $('h1').first().text() || 'API Documentation';
    const description = $('meta[name="description"]').attr('content') || '';

    // Try to find API endpoint patterns in the HTML
    // Look for common patterns like <code>/api/...</code> or method badges
    const codeBlocks = $('code, pre code, .endpoint, .api-endpoint');
    const methodPattern = /\b(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD)\b/gi;
    const pathPattern = /\/[a-zA-Z0-9\/_\-{}\:]+/g;

    const foundEndpoints = new Set<string>();

    codeBlocks.each((_, element) => {
      const text = $(element).text();
      const methods = text.match(methodPattern);
      const paths = text.match(pathPattern);

      if (methods && paths) {
        methods.forEach((method, idx) => {
          const path = paths[idx] || paths[0];
          const key = `${method}:${path}`;

          if (!foundEndpoints.has(key)) {
            foundEndpoints.add(key);

            // Try to find description near the endpoint
            const parent = $(element).parent();
            const description =
              parent.find('p').first().text() ||
              parent.next('p').text() ||
              $(element).attr('title') ||
              `${method} ${path}`;

            endpoints.push({
              path,
              method: method.toUpperCase(),
              description: description.trim(),
              parameters: this.extractParameters(path, parent, $),
              responses: [
                {
                  statusCode: 200,
                  description: 'Successful response',
                },
              ],
            });
          }
        });
      }
    });

    // If no endpoints found, try alternative parsing strategies
    if (endpoints.length === 0) {
      // Look for heading-based structure
      $('h2, h3, h4').each((_, element) => {
        const heading = $(element).text();
        const methods = heading.match(methodPattern);
        const paths = heading.match(pathPattern);

        if (methods && paths) {
          const method = methods[0];
          const path = paths[0];
          const key = `${method}:${path}`;

          if (!foundEndpoints.has(key)) {
            foundEndpoints.add(key);
            const description = $(element).next('p').text() || heading;

            endpoints.push({
              path,
              method: method.toUpperCase(),
              description: description.trim(),
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
      });
    }

    return {
      title,
      description,
      endpoints,
      sourceUrl,
      sourceType: 'html',
    };
  }

  private extractParameters(
    path: string,
    context: cheerio.Cheerio<any>,
    $: cheerio.CheerioAPI
  ): APIParameter[] {
    const parameters: APIParameter[] = [];

    // Extract path parameters from {param} or :param
    const pathParams = path.match(/\{([^}]+)\}|:([a-zA-Z0-9_]+)/g);
    if (pathParams) {
      pathParams.forEach((param) => {
        const name = param.replace(/[{}:]/g, '');
        parameters.push({
          name,
          in: 'path',
          description: `Path parameter: ${name}`,
          required: true,
          type: 'string',
        });
      });
    }

    // Try to find parameter tables or lists
    const tables = context.find('table');
    tables.each((_, table) => {
      const rows = $(table).find('tr');
      rows.each((_, row) => {
        const cells = $(row).find('td');
        if (cells.length >= 2) {
          const name = $(cells[0]).text().trim();
          const description = $(cells[1]).text().trim();
          if (name && !parameters.some((p) => p.name === name)) {
            parameters.push({
              name,
              in: 'query',
              description,
              required: description.toLowerCase().includes('required'),
              type: 'string',
            });
          }
        }
      });
    });

    return parameters;
  }
}
