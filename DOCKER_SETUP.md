# Doc2MCP Platform - Complete Setup Guide

🚀 **Full-stack platform for intelligent documentation search with AI agents**

## 🎯 What You're Building

A complete web platform with:
- ✅ Landing page with Clerk authentication
- ✅ User dashboard with tool management
- ✅ Background job system for indexing
- ✅ Real-time job monitoring
- ✅ VS Code MCP config generator
- ✅ Phoenix observability dashboard
- ✅ Fully Dockerized deployment

## 📋 Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for local development)
- Python 3.11+ (for local development)
- Clerk account (free tier: https://clerk.com)
- Google AI API key (free tier: https://aistudio.google.com)

## 🚀 Quick Start (Docker)

### 1. Clone the Repository

```bash
git clone https://github.com/RETR0-OS/Doc2Mcp.git
cd Doc2Mcp
```

### 2. Set Up Environment Variables

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your keys:
# - GOOGLE_API_KEY from https://aistudio.google.com/app/apikey
# - CLERK_SECRET_KEY from https://dashboard.clerk.com
# - NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY from https://dashboard.clerk.com
nano .env
```

### 3. Create Web Environment File

```bash
cd web
cp .env.example .env
# Add the same Clerk keys here
cd ..
```

### 4. Start All Services

```bash
docker-compose up -d
```

This will start:
- **Web Frontend**: http://localhost:3000
- **FastAPI Backend**: http://localhost:8000
- **Phoenix Dashboard**: http://localhost:6006
- **Redis**: localhost:6379
- **MCP Server**: stdio mode

### 5. Initialize Database

```bash
# Enter the web container
docker-compose exec web sh

# Run Prisma migrations
npx prisma db push
npx prisma generate

# Exit container
exit
```

### 6. Access the Platform

Open http://localhost:3000 and sign up!

## 🛠️ Local Development

### Frontend (Next.js)

```bash
cd web

# Install dependencies
npm install

# Set up database
npx prisma generate
npx prisma db push

# Run dev server
npm run dev
```

Frontend will be at http://localhost:3000

### Backend (FastAPI)

```bash
cd api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn main:app --reload
```

Backend will be at http://localhost:8000

### MCP Server

```bash
# From project root
pip install -e .

# Run server
GOOGLE_API_KEY=your-key python -m doc2mcp.server
```

## 📦 Project Structure

```
Doc2Mcp/
├── web/                      # Next.js Frontend
│   ├── app/                  # Pages and layouts
│   ├── components/           # React components
│   ├── lib/                  # Utilities
│   ├── prisma/               # Database schema
│   └── Dockerfile
├── api/                      # FastAPI Backend
│   ├── main.py               # API routes
│   ├── requirements.txt
│   └── Dockerfile
├── doc2mcp/                  # Python MCP Server
├── docker-compose.yml        # Orchestration
├── .env.example              # Environment template
└── Dockerfile                # MCP server container
```

## 🔧 Configuration

### Clerk Setup

1. Go to https://dashboard.clerk.com
2. Create a new application
3. Copy the Publishable Key and Secret Key
4. Add them to `.env` and `web/.env`
5. Set your production URL in Clerk dashboard

### Google AI Setup

1. Go to https://aistudio.google.com/app/apikey
2. Create a new API key
3. Add it to `.env` as `GOOGLE_API_KEY`

### Redis (Optional for local dev)

If not using Docker:
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis
```

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f web
docker-compose logs -f api

# Restart a service
docker-compose restart web

# Stop all services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# Clean everything (including volumes)
docker-compose down -v
```

## 📊 Accessing Services

| Service | URL | Purpose |
|---------|-----|---------|
| **Web App** | http://localhost:3000 | Main application |
| **API** | http://localhost:8000 | Backend API |
| **API Docs** | http://localhost:8000/docs | FastAPI Swagger docs |
| **Phoenix** | http://localhost:6006 | LLM tracing dashboard |
| **Prisma Studio** | Run `npm run db:studio` in web/ | Database GUI |

## 🔍 Health Checks

```bash
# Check API health
curl http://localhost:8000/health

# Check all containers
docker-compose ps
```

## 🎨 Features Implemented

### ✅ Phase 1 - Foundation
- [x] Next.js 14 with TypeScript
- [x] Clerk authentication with dark theme
- [x] SQLite database with Prisma
- [x] Black/white/red minimal design
- [x] Landing page with hero section
- [x] Dashboard layout with sidebar

### 🚧 Phase 2 - Core Features (TODO)
- [ ] Tools CRUD interface
- [ ] URL indexing form
- [ ] Background job system (BullMQ)
- [ ] Job monitoring UI
- [ ] VS Code config generator

### 🚧 Phase 3 - Integration (TODO)
- [ ] FastAPI ↔ Doc2MCP agent integration
- [ ] WebSocket for real-time updates
- [ ] tools.yaml ↔ database sync
- [ ] Phoenix iframe integration

## 🐛 Troubleshooting

### Database Issues

```bash
# Reset database
docker-compose exec web npx prisma db push --force-reset
```

### Port Conflicts

If ports are already in use:
```bash
# Edit docker-compose.yml to change ports
# Example: "3001:3000" instead of "3000:3000"
```

### Permission Errors

```bash
# Fix file permissions
sudo chown -R $USER:$USER .
```

### Container Won't Start

```bash
# Check logs
docker-compose logs [service-name]

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

## 🚀 Next Steps

### Immediate TODOs

1. **Tools Management Page** (`/dashboard/tools`)
   - List all user tools
   - Add/edit/delete tools
   - Enable/disable toggle
   - Source configuration UI

2. **Jobs Monitoring Page** (`/dashboard/jobs`)
   - Real-time job list
   - Progress indicators
   - Log streaming
   - Cancel/retry buttons

3. **Config Generator Page** (`/dashboard/config`)
   - Generate VS Code MCP config JSON
   - One-click copy
   - Instructions overlay

4. **API Integration**
   - Connect FastAPI to doc2mcp agent
   - Implement real indexing jobs
   - Add WebSocket support

5. **Phoenix Integration**
   - Embed Phoenix dashboard in iframe
   - Pass session tokens
   - Custom styling

### Future Enhancements

- [ ] User settings page
- [ ] API key management
- [ ] Usage analytics
- [ ] Billing integration
- [ ] Team collaboration
- [ ] Custom domains
- [ ] SSO support

## 📚 Documentation

- [Architecture Overview](./IMPLEMENTATION_PLAN.md)
- [API Documentation](http://localhost:8000/docs) (when running)
- [MCP Protocol](https://modelcontextprotocol.io)
- [Clerk Docs](https://clerk.com/docs)

## 🤝 Contributing

This is a hackathon project. Contributions welcome!

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - see [LICENSE](./LICENSE)

## 🏆 Hackathon Features

What makes this special:
- **Full-stack in one command**: Docker Compose orchestrates everything
- **Real-time monitoring**: Watch AI agents think
- **Production-ready**: Auth, DB, queue system, observability
- **Beautiful UX**: Minimal black/white/red design
- **Developer-friendly**: Complete docs, health checks, hot reload

---

**Built with ❤️ for smarter documentation**
