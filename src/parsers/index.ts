/**
 * Main parser that delegates to specific parsers based on documentation type
 */

import { APIDocumentation } from '../types/index.js';
import { fetchUrl, detectDocumentationType } from '../utils/helpers.js';
import { OpenAPIParser } from './openapi-parser.js';
import { HTMLParser } from './html-parser.js';
import { MarkdownParser } from './markdown-parser.js';

export class DocumentationParser {
  private openApiParser = new OpenAPIParser();
  private htmlParser = new HTMLParser();
  private markdownParser = new MarkdownParser();

  /**
   * Parses documentation from a URL
   */
  async parseFromUrl(url: string): Promise<APIDocumentation> {
    const content = await fetchUrl(url);
    return this.parseFromContent(content, url);
  }

  /**
   * Parses documentation from content string
   */
  async parseFromContent(content: string, sourceUrl: string): Promise<APIDocumentation> {
    const docType = detectDocumentationType(sourceUrl, content);

    switch (docType) {
      case 'openapi':
        return this.openApiParser.parse(content, sourceUrl);
      case 'html':
        return this.htmlParser.parse(content, sourceUrl);
      case 'markdown':
        return this.markdownParser.parse(content, sourceUrl);
      default:
        throw new Error(`Unsupported documentation type: ${docType}`);
    }
  }
}
