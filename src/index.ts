#!/usr/bin/env node

/**
 * Doc2MCP - MCP server that converts API documentation into callable tools
 * with Arize observability
 */

import { Doc2MCPServer } from './server/index.js';

// Configuration from environment variables
const config = {
  name: 'doc2mcp',
  version: '1.0.0',
  documentationUrls: process.env.DOC_URLS ? process.env.DOC_URLS.split(',') : [],
  tracing: {
    enabled: process.env.TRACING_ENABLED !== 'false',
    arizeEndpoint: process.env.ARIZE_ENDPOINT,
    arizeApiKey: process.env.ARIZE_API_KEY,
  },
};

async function main() {
  const server = new Doc2MCPServer(config);

  // Handle graceful shutdown
  const shutdown = async () => {
    console.error('\nShutting down Doc2MCP server...');
    await server.stop();
    process.exit(0);
  };

  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);

  try {
    await server.initialize();
    await server.start();
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

main();
