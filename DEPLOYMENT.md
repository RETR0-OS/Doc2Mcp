# Doc2MCP Platform - Complete Deployment Guide

## 🚀 Quick Start (5 minutes)

### Prerequisites

- Docker & Docker Compose installed
- Clerk account (free): https://clerk.com
- Google AI API key (free): https://aistudio.google.com/app/apikey

### Step 1: Clone and Setup

```bash
git clone https://github.com/RETR0-OS/Doc2Mcp.git
cd Doc2Mcp

# Copy environment file
cp .env.example .env
```

### Step 2: Get API Keys

1. **Clerk**: https://dashboard.clerk.com
   - Create a new application
   - Copy Publishable Key and Secret Key

2. **Google AI**: https://aistudio.google.com/app/apikey
   - Click "Create API key"
   - Copy the key

### Step 3: Configure Environment

Edit `.env`:
```bash
GOOGLE_API_KEY=your_google_key_here
CLERK_SECRET_KEY=sk_test_your_clerk_secret
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_your_clerk_key
```

Edit `web/.env` (same Clerk keys):
```bash
cp web/.env.example web/.env
# Add the same CLERK keys
```

### Step 4: Start Everything

```bash
# Build and start all services
docker-compose up -d

# Initialize database
docker-compose exec web npx prisma generate
docker-compose exec web npx prisma db push

# View logs
docker-compose logs -f
```

### Step 5: Access Platform

- **Web App**: http://localhost:3000
- **API**: http://localhost:8000
- **Phoenix**: http://localhost:6006

## 📦 What's Running

The Docker Compose stack includes:

1. **Next.js Web App** (Port 3000)
   - Landing page with authentication
   - Dashboard for tool management
   - Job monitoring with real-time updates
   - MCP config generator

2. **FastAPI Backend** (Port 8000)
   - Integrates with doc2mcp agent
   - Handles indexing and search jobs
   - WebSocket support for live updates

3. **Redis** (Port 6379)
   - Job queue management
   - Caching layer

4. **Phoenix** (Port 6006)
   - LLM observability
   - Trace visualization
   - Performance metrics

5. **MCP Server** (stdio)
   - Standalone for testing
   - Can be used directly with Claude Desktop

## 🎯 Using the Platform

### 1. Create an Account

1. Go to http://localhost:3000
2. Click "Get Started"
3. Sign up with email or Google

### 2. Add a Documentation Tool

1. Go to Dashboard → Tools
2. Click "Add Tool"
3. Fill in:
   - **Tool ID**: `anthropic` (lowercase, no spaces)
   - **Name**: `Anthropic Claude API`
   - **Description**: `Claude AI documentation`
   - **Source URL**: `https://docs.anthropic.com/en/api`
4. Click "Create Tool"

### 3. Index Documentation

1. In the tools list, click "Index" on your tool
2. Go to Jobs page to watch progress in real-time
3. The agent will:
   - Fetch the main page
   - Extract links
   - Cache pages with summaries
   - Build search index

### 4. Generate MCP Config

1. Go to Dashboard → Config
2. Copy the generated `tools.yaml`
3. Save it in your project directory
4. Copy the MCP server config JSON
5. Add to VS Code or Claude Desktop config

### 5. Use with VS Code

```bash
# Install doc2mcp (from this directory)
pip install -e .

# Set environment
export GOOGLE_API_KEY="your-key"

# Your tools.yaml is automatically synced from the database
```

In VS Code Copilot Chat:
```
@doc2mcp search anthropic for how to use streaming
```

## 🛠️ Development Mode

### Run Services Individually

```bash
# Terminal 1: Web (Next.js)
cd web
npm install
npx prisma generate
npm run dev

# Terminal 2: API (FastAPI)
cd api
pip install -r requirements.txt
uvicorn main:app --reload

# Terminal 3: Redis
docker run -p 6379:6379 redis:alpine

# Terminal 4: Phoenix
docker run -p 6006:6006 arizephoenix/phoenix:latest
```

## 📊 API Endpoints

### Tools API

```bash
# List tools
GET /api/tools

# Create tool
POST /api/tools
{
  "toolId": "my-tool",
  "name": "My Tool",
  "description": "Description",
  "sources": [{"type": "web", "url": "https://..."}]
}

# Update tool
PUT /api/tools/:id

# Delete tool
DELETE /api/tools/:id

# Toggle enabled
PATCH /api/tools/:id
{"enabled": true}
```

### Jobs API

```bash
# List jobs
GET /api/jobs

# Create indexing job
POST /api/jobs
{
  "type": "index",
  "toolId": "my-tool",
  "url": "https://docs.example.com"
}

# Create search job
POST /api/jobs
{
  "type": "search",
  "toolId": "my-tool",
  "query": "how to use the API"
}

# Get job status
GET /api/jobs/:id
```

### Backend API

```bash
# Health check
GET http://localhost:8000/health

# Start indexing
POST http://localhost:8000/index
{
  "job_id": "uuid",
  "user_id": "uuid",
  "tool_id": "anthropic",
  "url": "https://docs.anthropic.com"
}

# WebSocket for live updates
WS ws://localhost:8000/ws/jobs/:job_id
```

## 🔧 Database Management

```bash
# View database
cd web
npx prisma studio

# Reset database
docker-compose exec web npx prisma db push --force-reset

# Migrations (for production)
npx prisma migrate dev --name init
```

## 📝 Environment Variables

### Required

- `GOOGLE_API_KEY`: Your Google AI API key
- `CLERK_SECRET_KEY`: Clerk secret key
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`: Clerk publishable key

### Optional

- `DATABASE_URL`: SQLite path (default: `file:./data/dev.db`)
- `REDIS_URL`: Redis connection (default: `redis://redis:6379`)
- `PHOENIX_API_KEY`: For cloud Phoenix (leave empty for local)

## 🐛 Troubleshooting

### Database Locked

```bash
# Stop all services
docker-compose down

# Remove database file
rm web/data/dev.db

# Restart and reinitialize
docker-compose up -d
docker-compose exec web npx prisma db push
```

### Port Already in Use

```bash
# Find what's using the port
lsof -i :3000
lsof -i :8000

# Kill the process or change ports in docker-compose.yml
```

### WebSocket Connection Failed

- Check API is running: http://localhost:8000/health
- Check browser console for errors
- Ensure no firewall blocking WebSocket

### Agent Initialization Failed

```bash
# Check API logs
docker-compose logs api

# Common issue: GOOGLE_API_KEY not set
docker-compose exec api env | grep GOOGLE
```

## 🔒 Security Notes

### For Development

- SQLite database with file:// URL
- No authentication on Redis
- Clerk in development mode
- CORS allows localhost

### For Production

- Use PostgreSQL instead of SQLite
- Add Redis password
- Configure Clerk for production domain
- Update CORS settings
- Use environment secrets
- Enable HTTPS
- Add rate limiting

## 📚 Additional Resources

- [MCP Protocol](https://modelcontextprotocol.io)
- [Clerk Documentation](https://clerk.com/docs)
- [Google AI Studio](https://aistudio.google.com)
- [Phoenix Documentation](https://docs.arize.com/phoenix)

## 🎉 You're All Set!

The platform is now running with:
- ✅ Authentication system
- ✅ Tool management
- ✅ Real-time job monitoring  
- ✅ MCP server integration
- ✅ Observability dashboard

Start adding documentation tools and making them AI-searchable! 🚀
