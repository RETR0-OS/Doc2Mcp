# Doc2MCP

Turn any documentation into AI-searchable knowledge for GitHub Copilot and Claude.

Built for NexHacks 2026 - Dev Tools Track | Arize | The Token Company

## Overview

Doc2MCP enables AI assistants to search and understand any documentation. Simply add a URL, and your AI can instantly query it for accurate, sourced answers.

The system combines a web interface for managing documentation sources with an MCP server that provides intelligent search capabilities through a Gemini-powered agent. Every interaction is traced through Phoenix for complete observability, while token compression reduces costs and latency.

## Architecture

The platform consists of four core components. The web UI handles documentation ingestion from URLs or local files. The MCP server indexes content using Gemini AI and exposes it through the Model Context Protocol. Phoenix provides full LLM observability with span visualization, token tracking, and latency analysis. All documentation metadata is stored in SQLite for fast retrieval.

When an AI assistant queries documentation, the Gemini-powered agent explores relevant pages and returns sourced answers. Phoenix traces the entire flow, showing exactly which pages were explored, token counts, and timing information.

## Key Integrations

Arize Phoenix provides complete LLM observability. Every agent action is instrumented with spans that capture tool usage, query parameters, pages explored, and performance metrics. Access the Phoenix dashboard at http://localhost:6006 to monitor real-time traces and debug issues.

The Token Company integration delivers intelligent compression that reduces documentation size by 40-60% while preserving code blocks and technical details. This semantic compression keeps meaning intact while removing unnecessary content, resulting in faster responses and lower API costs.

## Quick Start

Clone the repository and copy the example environment file:

```bash
git clone https://github.com/RETR0-OS/Doc2Mcp.git
cd Doc2Mcp
cp .env.example .env
Add your API keys to the .env file. You'll need GOOGLE_API_KEY for Gemini, TOKENC_API_KEY for compression (optional but recommended), and Clerk keys for authentication.
```

Launch the services:

```bash
docker-compose up -d
docker-compose exec web npx prisma db push
```
Open http://localhost:3000 to access the interface.

Environment Variables
GOOGLE_API_KEY is required for Gemini AI documentation exploration. TOKENC_API_KEY is optional but recommended for token compression. CLERK_SECRET_KEY is required for authentication. PHOENIX_API_KEY is optional and only needed for cloud Phoenix (local deployment works without it).

Technical Stack
Frontend: Next.js 14, Tailwind CSS, Clerk Auth, Prisma ORM Backend: FastAPI, Gemini AI, WebSocket support Infrastructure: Docker, Redis, SQLite, Phoenix observability

Why This Matters
AI coding assistants are powerful but limited to their training data. Doc2MCP bridges the gap by making your documentation instantly accessible to AI with full observability into search behavior and performance.

Built for NexHacks 2026 by RETR0-OS and ashworks1706
