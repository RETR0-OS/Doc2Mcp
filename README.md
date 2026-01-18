# Doc2MCP Platform 🚀

**Transform any documentation into AI-searchable knowledge with a full-stack web platform**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ What is This?

Doc2MCP is a complete platform that makes documentation searchable for AI assistants like GitHub Copilot and Claude. It combines:

- 🎨 **Beautiful Web UI** - Clerk auth, tool management, real-time monitoring
- 🤖 **Intelligent Agent** - Gemini-powered doc exploration and synthesis
- 📊 **Full Observability** - Phoenix tracing for every LLM call
- 🐳 **Docker Deployment** - One command to start everything

## 🎯 Features

### Web Platform
- ✅ Landing page with authentication (Clerk)
- ✅ Dashboard with tool management (CRUD)
- ✅ Real-time job monitoring with WebSockets
- ✅ VS Code MCP config generator
- ✅ Phoenix observability integration

### MCP Server
- ✅ Intelligent documentation exploration
- ✅ Smart caching with summaries
- ✅ Multiple source types (web, local)
- ✅ Gemini-powered navigation

### API Backend
- ✅ FastAPI with real doc2mcp agent integration
- ✅ Background job processing
- ✅ WebSocket for live updates
- ✅ RESTful API for all operations

## 🚀 Quick Start

```bash
# Clone the repo
git clone https://github.com/RETR0-OS/Doc2Mcp.git
cd Doc2Mcp

# Set up environment
cp .env.example .env
# Add your GOOGLE_API_KEY and CLERK keys

# Start everything with Docker
docker-compose up -d

# Initialize database
docker-compose exec web npx prisma db push

# Access the platform
open http://localhost:3000
```

**That's it!** You now have:
- Web app at http://localhost:3000
- API at http://localhost:8000
- Phoenix at http://localhost:6006

## 📚 Documentation

- **[Deployment Guide](DEPLOYMENT.md)** - Complete setup instructions
- **[Implementation Plan](IMPLEMENTATION_PLAN.md)** - Architecture details
- **[Docker Setup](DOCKER_SETUP.md)** - Container configuration

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│           Docker Compose Stack              │
├─────────────────────────────────────────────┤
│                                             │
│  ┌────────────┐  ┌──────────────┐         │
│  │  Next.js   │  │   FastAPI    │         │
│  │  Frontend  │──│   Backend    │         │
│  │  Port 3000 │  │   Port 8000  │         │
│  └────────────┘  └──────────────┘         │
│         │               │                   │
│         └───────┬───────┘                   │
│                 ▼                           │
│          ┌──────────────┐                  │
│          │   SQLite DB  │                  │
│          └──────────────┘                  │
│                                             │
│  ┌────────────┐  ┌──────────────┐         │
│  │   Redis    │  │   Phoenix    │         │
│  │  (Queue)   │  │  (Tracing)   │         │
│  └────────────┘  └──────────────┘         │
└─────────────────────────────────────────────┘
```

## 🛠️ Tech Stack

### Frontend
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Clerk Authentication
- Prisma ORM
- shadcn/ui components

### Backend
- FastAPI
- doc2mcp agent (Python)
- Google Gemini AI
- Jina Reader for web scraping
- WebSockets

### Infrastructure
- Docker & Docker Compose
- Redis (job queue)
- SQLite (development)
- Phoenix (observability)

## 🎨 Design System

Minimal black/white/red aesthetic:
- Primary: `#ef4444` (red)
- Background: `#0a0a0a` (black)
- Cards: `#1a1a1a`
- Text: `#ffffff` (white)

## 📸 Screenshots

*Coming soon - platform is fully functional!*

## 🎯 Use Cases

1. **Internal Documentation** - Index your company docs for AI search
2. **API References** - Make complex APIs easier to understand
3. **Learning Resources** - Search tutorials and guides intelligently
4. **Multi-source Knowledge** - Combine web docs and local files

## 🔧 Development

```bash
# Frontend (Next.js)
cd web
npm install
npm run dev

# Backend (FastAPI)  
cd api
pip install -r requirements.txt
uvicorn main:app --reload

# MCP Server
pip install -e .
python -m doc2mcp.server
```

## 📝 Environment Variables

Get your keys:
- **Clerk**: https://dashboard.clerk.com
- **Google AI**: https://aistudio.google.com/app/apikey

Required in `.env`:
```bash
GOOGLE_API_KEY=...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
```

## 🤝 Contributing

This is a hackathon project built with real, working code - no mockups!

Contributions welcome:
1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Submit a PR

## 📄 License

MIT - see [LICENSE](LICENSE)

## 🏆 Hackathon Features

What makes this special:
- ✅ **No mockup code** - Everything actually works
- ✅ **Full-stack** - Frontend + Backend + Agent + Observability
- ✅ **One-command deploy** - Docker Compose handles everything
- ✅ **Production-ready** - Auth, DB, queue system, monitoring
- ✅ **Beautiful UX** - Minimal design, real-time updates
- ✅ **Complete docs** - Setup guides, API docs, troubleshooting

## 🔗 Links

- [GitHub Repository](https://github.com/RETR0-OS/Doc2Mcp)
- [MCP Protocol](https://modelcontextprotocol.io)
- [Google AI Studio](https://aistudio.google.com)

---

**Built with ❤️ for smarter documentation** by [@RETR0-OS](https://github.com/RETR0-OS)
