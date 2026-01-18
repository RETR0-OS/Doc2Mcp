from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import logging
from datetime import datetime
import sys
import os

# Add parent directory to path to import doc2mcp
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from doc2mcp.agents.doc_search import DocSearchAgent
from doc2mcp.config import Config, ToolConfig, WebSource
from doc2mcp.fetchers.web import WebFetcher
from doc2mcp.cache import PageCache

app = FastAPI(title="Doc2MCP API", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://web:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize doc2mcp components
config = Config(tools={}, settings=Config.Settings())
agent: Optional[DocSearchAgent] = None
cache = PageCache("./doc_cache.json")
web_fetcher = WebFetcher()

# Models
class IndexRequest(BaseModel):
    job_id: str
    user_id: str
    tool_id: str
    url: str

class SearchRequest(BaseModel):
    job_id: str
    user_id: str
    tool_id: str
    tool_name: str
    tool_description: str
    query: str

class SyncRequest(BaseModel):
    job_id: str
    user_id: str

class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: int
    logs: List[str]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Job tracking with WebSocket support
jobs: Dict[str, JobStatus] = {}
websocket_connections: Dict[str, WebSocket] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize agent on startup"""
    global agent
    try:
        agent = DocSearchAgent(config, max_pages=10)
        logger.info("Doc2MCP agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if agent:
        await agent.close()
    await web_fetcher.close()

@app.get("/")
async def root():
    return {
        "service": "Doc2MCP API",
        "version": "0.1.0",
        "status": "running",
        "agent_ready": agent is not None
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "agent": "ready" if agent else "not initialized"
    }

@app.post("/index")
async def start_indexing(request: IndexRequest, background_tasks: BackgroundTasks):
    """Start a documentation indexing job"""
    
    # Initialize job
    jobs[request.job_id] = JobStatus(
        job_id=request.job_id,
        status="running",
        progress=0,
        logs=["Starting indexing job..."],
    )
    
    # Start background task
    background_tasks.add_task(run_indexing_job, request)
    
    return {"job_id": request.job_id, "status": "started"}

@app.post("/search")
async def start_search(request: SearchRequest, background_tasks: BackgroundTasks):
    """Start a documentation search job"""
    
    # Initialize job
    jobs[request.job_id] = JobStatus(
        job_id=request.job_id,
        status="running",
        progress=0,
        logs=["Starting search job..."],
    )
    
    # Start background task
    background_tasks.add_task(run_search_job, request)
    
    return {"job_id": request.job_id, "status": "started"}

@app.get("/jobs/{job_id}/status")
async def get_job_status(job_id: str):
    """Get status of a job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs[job_id]

async def run_indexing_job(request: IndexRequest):
    """Background task for indexing - crawls and caches documentation"""
    job = jobs[request.job_id]
    
    try:
        await send_job_update(request.job_id, f"Starting to index {request.url}...")
        job.progress = 10
        
        # Fetch the initial page
        await send_job_update(request.job_id, f"Fetching {request.url}...")
        fetch_result = await web_fetcher.fetch_with_links(request.url, None)
        job.progress = 30
        
        pages_indexed = 1
        links_found = len(fetch_result.links)
        
        # Cache the main page
        await send_job_update(request.job_id, "Caching page content...")
        cache.put(
            url=fetch_result.url,
            title=fetch_result.title,
            summary=fetch_result.title,
            content=fetch_result.content,
            links=fetch_result.links,
            domain=request.url.split('/')[2] if '/' in request.url else request.url
        )
        job.progress = 50
        
        # Index linked pages (limited to 5 for speed)
        await send_job_update(request.job_id, f"Indexing {min(5, len(fetch_result.links))} linked pages...")
        for i, link in enumerate(fetch_result.links[:5]):
            try:
                link_url = link['url']
                await send_job_update(request.job_id, f"Fetching: {link_url[:60]}...")
                
                link_result = await web_fetcher.fetch_with_links(link_url, None)
                cache.put(
                    url=link_result.url,
                    title=link_resul - uses doc2mcp agent"""
                    job = jobs[request.job_id]
                    
                    try:
                        await send_job_update(request.job_id, f"Searching for: {request.query}")
                        job.progress = 10
                        
                        # Create a temporary tool config for this search
                        tool_config = ToolConfig(
                            name=request.tool_name,
                            description=request.tool_description,
                            sources=[]  # Agent will use cached pages
                        )
                        
                        # Update agent config
                        if agent:
                            agent.config.tools[request.tool_id] = tool_config
                            
                            await send_job_update(request.job_id, "Initializing search agent...")
                            job.progress = 20
                            
                            # Perform the search
                            await send_job_update(request.job_id, "Exploring documentation...")
                            result = await agent.search(request.tool_id, request.query)
                            job.progress = 80
                            
                            if result.get("error"):
                                raise Exception(result["error"])
                            
                            await send_job_update(request.job_id, "Synthesizing answer...")
                            job.progress = 95
                            
                            await send_job_update(request.job_id, "Search complete!")
                            job.progress = 100
                            job.status = "completed"
                            job.result = {
                                "content": result.get("content", "No content found"),
                                "sources": result.get("sources", []),
                                "pages_explored": result.get("pages_explored", 0),
                                "tool": result.get("tool", {})
                            }
                        else:
                            raise Exception("Agent not initialized")
                        
                    except Exception as e:
                        logger.error(f"Search job {request.job_id} failed: {e}")
                        job.status = "failed"
                        job.error = str(e)
                        await send_job_update(request.job_id, f"Searching for: {request.query}")
                        job.progress = 20
                        await asyncio.sleep(1)
                        
                        job.logs.append("Exploring documentation...")
                        job.progress = 50
                        await asyncio.sleep(2)
                        
                        job.logs.append("Analyzing content...")
                        job.progress = 80
                        await asyncio.sleep(1)
                        
                        job.logs.append("Synthesizing answer...")
                        job.progress = 95
                        await asyncio.sleep(1)
                        
                        job.logs.append("Search complete!")
async def send_job_update(job_id: str, log_message: str):
    """Send job update to WebSocket if connected"""
    if job_id in jobs:
        jobs[job_id].logs.append(log_message)
        
        # Send to WebSocket if connected
        if job_id in websocket_connections:
            try:
                await websocket_connections[job_id].send_json({
                    "type": "log",
                    "message": log_message,
                    "progress": jobs[job_id].progress,
                    "status": jobs[job_id].status
                })
            except:
                pass

@app.websocket("/ws/jobs/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket for real-time job updates"""
    await websocket.accept()
    websocket_connections[job_id] = websocket
    
    try:
        # Send current job status
        if job_id in jobs:
            await websocket.send_json({
                "type": "status",
                "job": jobs[job_id].dict()
            })
        
        # Keep connection alive
        while True:
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        if job_id in websocket_connections:
            del websocket_connections[job_id]

        job.progress = 100
        job.status = "completed"
        job.result = {
            "answer": "This is a placeholder answer that would come from Gemini.",
            "sources": ["https://example.com/page1", "https://example.com/page2"],
            "pages_explored": 5
        }
        
    except Exception as e:
        logger.error(f"Search job {request.job_id} failed: {e}")
        job.status = "failed"
        job.error = str(e)
        job.logs.append(f"Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
