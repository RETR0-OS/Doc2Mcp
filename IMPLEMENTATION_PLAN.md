# Doc2MCP Platform - Implementation Plan

## 🎯 Overview
Transform Doc2MCP into a full-featured web platform with:
- Landing page + Clerk auth
- Tool management UI
- Real-time background job monitoring
- VS Code MCP config generator
- Dockerized deployment

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│           Docker Compose Stack              │
├─────────────────────────────────────────────┤
│                                             │
│  ┌────────────┐  ┌──────────────┐         │
│  │  Next.js   │  │   FastAPI    │         │
│  │  Frontend  │─▶│   Backend    │         │
│  │  (Port 3000)  │  (Port 8000)  │         │
│  └────────────┘  └──────────────┘         │
│        │               │                    │
│        └───────┬───────┘                    │
│                ▼                            │
│         ┌──────────────┐                   │
│         │   SQLite DB  │                   │
│         └──────────────┘                   │
│                                             │
│  ┌────────────┐  ┌──────────────┐         │
│  │   Redis    │  │   Phoenix    │         │
│  │ (Queue/WS) │  │  (Port 6006) │         │
│  └────────────┘  └──────────────┘         │
│                                             │
│  ┌──────────────────────────────┐         │
│  │     MCP Server (stdio)       │         │
│  └──────────────────────────────┘         │
└─────────────────────────────────────────────┘
```

## 📁 New Directory Structure

```
Doc2Mcp/
├── docker-compose.yml
├── .env.example
├── doc2mcp/              # Existing Python MCP server
├── web/                  # NEW: Next.js frontend
│   ├── app/
│   │   ├── page.tsx                 # Landing page
│   │   ├── dashboard/
│   │   │   ├── page.tsx             # Main dashboard
│   │   │   ├── tools/page.tsx       # Tools management
│   │   │   ├── jobs/page.tsx        # Background jobs
│   │   │   └── config/page.tsx      # MCP config generator
│   │   ├── api/
│   │   │   ├── auth/[...clerk]/route.ts
│   │   │   ├── tools/route.ts
│   │   │   ├── jobs/route.ts
│   │   │   └── webhooks/route.ts
│   │   └── layout.tsx
│   ├── components/
│   │   ├── landing/
│   │   │   ├── Hero.tsx
│   │   │   ├── Features.tsx
│   │   │   └── CTA.tsx
│   │   ├── dashboard/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── ToolCard.tsx
│   │   │   ├── JobMonitor.tsx
│   │   │   └── ConfigGenerator.tsx
│   │   └── ui/                      # shadcn/ui components
│   ├── lib/
│   │   ├── db.ts                    # Prisma client
│   │   ├── clerk.ts
│   │   └── queue.ts
│   ├── prisma/
│   │   └── schema.prisma
│   ├── public/
│   ├── tailwind.config.ts
│   ├── package.json
│   └── Dockerfile
├── api/                  # NEW: FastAPI backend
│   ├── main.py
│   ├── models.py
│   ├── jobs.py
│   ├── mcp_bridge.py
│   ├── requirements.txt
│   └── Dockerfile
└── phoenix/             # NEW: Phoenix config
    └── Dockerfile
```

## 🎨 Design System

### Color Palette
- **Primary Black**: `#0a0a0a`
- **Secondary Black**: `#1a1a1a`
- **White**: `#ffffff`
- **Red Accent**: `#ef4444` (primary actions)
- **Red Hover**: `#dc2626`
- **Gray**: `#525252` (text secondary)
- **Border**: `#262626`

### Typography
- **Font**: Inter (system default fallback)
- **Headings**: Font weight 700
- **Body**: Font weight 400
- **Mono**: JetBrains Mono for code

## 📊 Database Schema (Prisma)

```prisma
model User {
  id          String   @id @default(uuid())
  clerkId     String   @unique
  email       String   @unique
  createdAt   DateTime @default(now())
  tools       Tool[]
  jobs        Job[]
}

model Tool {
  id          String   @id @default(uuid())
  userId      String
  user        User     @relation(fields: [userId], references: [id])
  toolId      String   # e.g., "anthropic"
  name        String
  description String
  sources     Json     # Array of source configs
  enabled     Boolean  @default(true)
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
}

model Job {
  id          String   @id @default(uuid())
  userId      String
  user        User     @relation(fields: [userId], references: [id])
  type        String   # "index", "search"
  status      String   # "pending", "running", "completed", "failed"
  input       Json
  output      Json?
  progress    Int      @default(0)
  logs        Json     @default("[]")
  startedAt   DateTime?
  completedAt DateTime?
  createdAt   DateTime @default(now())
}
```

## 🔄 Background Job System

### Job Types
1. **Indexing Job**: Crawls URLs and builds documentation index
2. **Search Job**: Executes deep documentation search
3. **Sync Job**: Updates tools.yaml from database

### Job Queue (BullMQ + Redis)
```typescript
// web/lib/queue.ts
const indexQueue = new Queue('indexing', { connection: redis });

// Monitor job progress
job.on('progress', (progress) => {
  io.emit('job:progress', { jobId, progress });
});
```

## 🔌 API Endpoints

### Next.js API Routes
- `POST /api/tools` - Create tool
- `GET /api/tools` - List user's tools
- `PUT /api/tools/:id` - Update tool
- `DELETE /api/tools/:id` - Delete tool
- `POST /api/jobs` - Create indexing job
- `GET /api/jobs` - List jobs with status
- `GET /api/jobs/:id` - Get job details
- `GET /api/config/vscode` - Generate MCP config

### FastAPI Backend
- `POST /index` - Start indexing job
- `POST /search` - Execute search
- `GET /jobs/:id/status` - Get job status
- `WebSocket /jobs/:id/logs` - Stream job logs

## 🐳 Docker Services

### docker-compose.yml
```yaml
services:
  web:
    build: ./web
    ports: ["3000:3000"]
    depends_on: [api, redis]
    
  api:
    build: ./api
    ports: ["8000:8000"]
    depends_on: [redis]
    
  redis:
    image: redis:alpine
    ports: ["6379:6379"]
    
  phoenix:
    build: ./phoenix
    ports: ["6006:6006"]
    volumes:
      - phoenix-data:/phoenix
    
  mcp-server:
    build: .
    command: python -m doc2mcp.server
    depends_on: [redis]

volumes:
  phoenix-data:
```

## 🚀 Key Features

### 1. Landing Page
- Hero with animated gradient background
- Feature cards with icons
- Pricing tiers (if applicable)
- CTA buttons (Sign Up / Login)

### 2. Dashboard
- Sidebar navigation
- Stats cards (Total tools, Active jobs, Cache hit rate)
- Quick actions

### 3. Tools Management
- Grid/List view of tools
- Add/Edit modal with form validation
- Source configuration (Web URL, Local path)
- Enable/Disable toggle
- Sync to tools.yaml button

### 4. Job Monitor
- Live updating job list
- Progress bars with percentage
- Real-time logs streaming
- Filter by status/type
- Job details modal

### 5. Config Generator
- Display formatted VS Code MCP config
- One-click copy button
- Preview with syntax highlighting
- Instructions for where to paste

## 🔐 Security

- Clerk handles auth (no passwords stored)
- API routes protected with Clerk middleware
- User data isolation (RLS-style queries)
- CORS configuration
- Rate limiting on API endpoints

## 📦 Installation Flow

```bash
# 1. Clone repo
git clone https://github.com/RETR0-OS/Doc2Mcp.git
cd Doc2Mcp

# 2. Copy environment variables
cp .env.example .env

# 3. Add your keys
# CLERK_SECRET_KEY=...
# GOOGLE_API_KEY=...

# 4. Start everything
docker-compose up -d

# 5. Access at http://localhost:3000
```

## 🎯 Development Phases

### Phase 1: Foundation (Tasks 1-6)
- Next.js setup
- Clerk auth
- Database + Prisma
- Basic landing page
- Dashboard layout

### Phase 2: Core Features (Tasks 7-11)
- Tools CRUD
- URL indexing form
- Background jobs
- Job monitoring UI
- Config generator

### Phase 3: Backend Integration (Tasks 12-15)
- FastAPI server
- Job execution
- MCP bridge
- Phoenix integration

### Phase 4: Deployment (Tasks 16-20)
- Docker containers
- Compose orchestration
- Testing
- Documentation

## 📝 Environment Variables

```bash
# Clerk
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
CLERK_SECRET_KEY=

# Database
DATABASE_URL=file:./dev.db

# Google AI
GOOGLE_API_KEY=

# Redis
REDIS_URL=redis://redis:6379

# API
NEXT_PUBLIC_API_URL=http://localhost:8000
API_URL=http://api:8000

# Phoenix
PHOENIX_API_KEY=
```

## 🎨 Component Examples

### ToolCard Component
```tsx
<ToolCard
  name="Anthropic API"
  sources={2}
  enabled={true}
  onEdit={() => {}}
  onDelete={() => {}}
  onToggle={() => {}}
/>
```

### JobMonitor Component
```tsx
<JobMonitor
  jobs={jobs}
  onViewLogs={(jobId) => {}}
  onCancel={(jobId) => {}}
/>
```

## 🧪 Testing Strategy

- Unit tests for API routes
- Integration tests for job queue
- E2E tests with Playwright
- Docker health checks

---

**Ready to build!** 🚀
