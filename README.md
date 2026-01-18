# Doc2MCP 🚀

**Turn any documentation into AI-searchable knowledge for GitHub Copilot & Claude**

> 🏆 **NexHacks 2026** — Dev Tools Track | Arize | The Token Company

---

## What It Does

Doc2MCP lets you point AI assistants at *any* documentation. Just add a URL, and your AI can instantly search and understand it.

```
You: "How do I authenticate with the Stripe API?"
AI:  *searches your indexed Stripe docs* → gives accurate, sourced answer
```

## How It Works

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web UI        │───▶│   MCP Server    │───▶│  AI Assistant   │
│  (Add docs)     │    │ (Search agent)  │    │ (Copilot/Claude)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                      │
         ▼                      ▼
    ┌─────────┐         ┌──────────────┐
    │ SQLite  │         │ Phoenix      │
    │   DB    │         │ (Tracing)    │
    └─────────┘         └──────────────┘
```

1. **Add docs** via web UI (URLs or local files)
2. **MCP server** auto-indexes using Gemini AI
3. **AI assistants** query through Model Context Protocol
4. **Phoenix** traces every LLM call for debugging

---

## 🔬 Key Integrations

### Arize Phoenix — Full LLM Observability

Every search goes through our Gemini-powered agent. Phoenix traces the entire flow:

- **Span visualization** — See exactly which pages the agent explored
- **Token tracking** — Monitor input/output tokens per request
- **Latency analysis** — Identify slow documentation sources
- **Error debugging** — Trace failures back to specific LLM calls

```python
# Every agent action is traced
with tracer.start_as_current_span("search_docs") as span:
    span.set_attribute("tool", tool_name)
    span.set_attribute("query", query)
    result = await agent.search(query)
    span.set_attribute("pages_explored", len(result.sources))
```

Access Phoenix at `http://localhost:6006` to see real-time traces.

### The Token Company — Intelligent Compression

Documentation can be *huge*. We use **tokenc** to compress content before sending to LLMs:

- **40-60% token reduction** on documentation content
- **Preserves code blocks** and technical details
- **Semantic compression** — keeps meaning, removes fluff
- **Configurable aggressiveness** — tune for your use case

```python
# Before: 15,000 tokens of raw HTML docs
# After: 6,000 tokens of compressed, meaningful content

compressor = ContentCompressor(aggressiveness=0.5)
result = compressor.compress(raw_docs)
# result.compression_ratio → 0.40 (60% savings!)
```

This means **faster responses** and **lower API costs**.

---

## Quick Start

```bash
# Clone & setup
git clone https://github.com/RETR0-OS/Doc2Mcp.git
cd Doc2Mcp
cp .env.example .env

# Add your keys to .env:
# - GOOGLE_API_KEY (Gemini)
# - TOKENC_API_KEY (The Token Company)
# - CLERK keys (auth)

# Launch everything
docker-compose up -d
docker-compose exec web npx prisma db push

# Open http://localhost:3000
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | Gemini AI for doc exploration |
| `TOKENC_API_KEY` | No | Token compression (recommended) |
| `CLERK_SECRET_KEY` | Yes | Authentication |
| `PHOENIX_API_KEY` | No | Cloud Phoenix (local works without) |

---

## Tech Stack

- **Frontend**: Next.js 14, Tailwind, Clerk Auth, Prisma
- **Backend**: FastAPI, Gemini AI, WebSockets
- **Infra**: Docker, Redis, SQLite, Phoenix

---

## Why This Matters

AI coding assistants are powerful but limited to their training data. Doc2MCP bridges the gap — making *your* documentation instantly accessible to AI, with full observability into how it searches and responds.

---

**Built for NexHacks 2026** by [@RETR0-OS](https://github.com/RETR0-OS)

[GitHub](https://github.com/RETR0-OS/Doc2Mcp) · [MCP Protocol](https://modelcontextprotocol.io)
