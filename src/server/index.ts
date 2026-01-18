/**
 * Main MCP server implementation for Doc2MCP
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import { DocumentationParser } from '../parsers/index.js';
import { ToolGenerator } from '../generators/tool-generator.js';
import { TracingManager, traceToolExecution, traceDocumentationParsing } from '../observability/tracing.js';
import { ParsedTool } from '../types/index.js';

export interface ServerConfig {
  name: string;
  version: string;
  documentationUrls?: string[];
  tracing: {
    enabled: boolean;
    arizeEndpoint?: string;
    arizeApiKey?: string;
  };
}

export class Doc2MCPServer {
  private server: Server;
  private parser = new DocumentationParser();
  private generator = new ToolGenerator();
  private tracingManager: TracingManager;
  private tools: Map<string, ParsedTool> = new Map();

  constructor(private config: ServerConfig) {
    this.server = new Server(
      {
        name: config.name,
        version: config.version,
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.tracingManager = new TracingManager({
      serviceName: config.name,
      serviceVersion: config.version,
      arizeEndpoint: config.tracing.arizeEndpoint,
      arizeApiKey: config.tracing.arizeApiKey,
      enabled: config.tracing.enabled,
    });

    this.setupHandlers();
  }

  /**
   * Initializes the server
   */
  async initialize() {
    // Initialize tracing
    this.tracingManager.initialize();

    // Load documentation URLs if provided
    if (this.config.documentationUrls && this.config.documentationUrls.length > 0) {
      for (const url of this.config.documentationUrls) {
        await this.loadDocumentation(url);
      }
    }
  }

  /**
   * Loads and parses documentation from a URL
   */
  async loadDocumentation(url: string): Promise<void> {
    try {
      console.error(`Loading documentation from: ${url}`);

      const tracer = this.tracingManager.getTracer();

      const documentation = await traceDocumentationParsing(
        tracer,
        url,
        'unknown',
        async () => {
          return this.parser.parseFromUrl(url);
        }
      );

      console.error(
        `Parsed ${documentation.endpoints.length} endpoints from ${documentation.title}`
      );

      // Generate tools
      const generatedTools = this.generator.generateTools(documentation);

      // Register tools
      for (const tool of generatedTools) {
        this.tools.set(tool.name, tool);
        console.error(`Registered tool: ${tool.name}`);
      }
    } catch (error) {
      console.error(`Failed to load documentation from ${url}:`, error);
      throw error;
    }
  }

  /**
   * Sets up MCP request handlers
   */
  private setupHandlers() {
    // List tools handler
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      const tools: Tool[] = Array.from(this.tools.values()).map((tool) => ({
        name: tool.name,
        description: tool.description,
        inputSchema: {
          type: 'object' as const,
          ...tool.inputSchema,
        },
      }));

      return { tools };
    });

    // Call tool handler
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const toolName = request.params.name;
      const tool = this.tools.get(toolName);

      if (!tool) {
        throw new Error(`Tool not found: ${toolName}`);
      }

      try {
        const tracer = this.tracingManager.getTracer();

        const result = await traceToolExecution(
          tracer,
          tool.name,
          tool.metadata.sourceUrl,
          tool.metadata.sourceType,
          {
            path: tool.metadata.endpoint.path,
            method: tool.metadata.endpoint.method,
          },
          request.params.arguments || {},
          async () => {
            return tool.handler(request.params.arguments || {});
          }
        );

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(
                {
                  error: errorMessage,
                  tool: toolName,
                },
                null,
                2
              ),
            },
          ],
          isError: true,
        };
      }
    });
  }

  /**
   * Starts the server
   */
  async start() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Doc2MCP server running on stdio');
  }

  /**
   * Stops the server
   */
  async stop() {
    await this.tracingManager.shutdown();
    await this.server.close();
  }
}
