"""
Intelligent documentation scraper using Gemini LLM
"""
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from google import genai
from google.genai import types
from urllib.parse import urljoin, urlparse
import asyncio
import sys


class DocScraper:
    """Scrape and chunk documentation intelligently"""
    
    def __init__(self, gemini_api_key: str):
        from opentelemetry import trace
        self.api_key = gemini_api_key
        self.client = genai.Client(api_key=gemini_api_key)
        self.model = 'gemini-2.0-flash-exp'
        self.tracer = trace.get_tracer(__name__)
        print(f"[SCRAPER] 🌐 Initialized web scraper", file=sys.stderr)
        
    async def scrape_url(self, url: str) -> Dict[str, Any]:
        """Scrape content from a URL"""
        with self.tracer.start_as_current_span("scraper.scrape_url") as span:
            span.set_attribute("url", url)
            print(f"[SCRAPER] 📥 Fetching: {url[:80]}...", file=sys.stderr)
            
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                    span.set_attribute("http.status_code", response.status_code)
                    span.set_attribute("content.length", len(response.text))
                    print(f"[SCRAPER] ✅ Success: {response.status_code} ({len(response.text)} bytes)", file=sys.stderr)
                    
                    # Parse HTML
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Remove script and style elements
                    removed_count = 0
                    for script in soup(["script", "style", "nav", "footer", "header"]):
                        script.decompose()
                        removed_count += 1
                    print(f"[SCRAPER] 🧹 Cleaned {removed_count} non-content elements", file=sys.stderr)
                    
                    # Get text content
                    text = soup.get_text()
                    
                    # Clean up whitespace
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = ' '.join(chunk for chunk in chunks if chunk)
                    
                    # Find links
                    links = []
                    base_domain = urlparse(url).netloc
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        full_url = urljoin(url, href)
                        # Only include links from same domain
                        if urlparse(full_url).netloc == base_domain:
                            links.append({
                                'url': full_url,
                                'text': link.get_text(strip=True)
                            })
                    
                    span.set_attribute("links.found", len(links))
                    span.set_attribute("content.final_length", len(text))
                    print(f"[SCRAPER] 📊 Extracted {len(text)} chars, found {len(links)} links", file=sys.stderr)
                    span.add_event("scrape_complete", {
                        "content_length": len(text),
                        "links_count": len(links)
                    })
                    
                    return {
                        'url': url,
                        'title': soup.title.string if soup.title else '',
                        'content': text[:50000],  # Limit content size
                        'links': links[:100]  # Limit number of links
                    }
                    
                except Exception as e:
                    span.set_attribute("error", True)
                    span.set_attribute("error.message", str(e))
                    print(f"[SCRAPER] ❌ Error scraping {url}: {e}", file=sys.stderr)
                    span.add_event("scrape_failed", {"error": str(e)})
                return {
                    'url': url,
                    'title': '',
                    'content': '',
                    'links': [],
                    'error': str(e)
                }
    
    def chunk_content(self, content: str, chunk_size: int = 8000) -> List[str]:
        """Split content into manageable chunks"""
        words = content.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            word_size = len(word) + 1
            if current_size + word_size > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_size = word_size
            else:
                current_chunk.append(word)
                current_size += word_size
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    async def discover_related_pages(self, base_url: str, max_pages: int = 10) -> List[Dict[str, Any]]:
        """Discover related documentation pages"""
        with self.tracer.start_as_current_span("scraper.discover_pages") as span:
            span.set_attribute("base.url", base_url)
            span.set_attribute("max.pages", max_pages)
            print(f"[SCRAPER] 🔍 Starting page discovery from: {base_url}", file=sys.stderr)
            print(f"[SCRAPER] 🎯 Target: {max_pages} pages", file=sys.stderr)
            
            visited = set()
            to_visit = [base_url]
            discovered = []
            
            base_domain = urlparse(base_url).netloc
            base_path = urlparse(base_url).path.rsplit('/', 1)[0] if '/' in urlparse(base_url).path else ''
            
            while to_visit and len(discovered) < max_pages:
                url = to_visit.pop(0)
                if url in visited:
                    continue
                
                visited.add(url)
                print(f"[SCRAPER] 📖 Page {len(discovered)+1}/{max_pages}: Scraping {url[:70]}...", file=sys.stderr)
                page_data = await asyncio.create_task(self.scrape_url(url))
                
                if page_data.get('content'):
                    discovered.append(page_data)
                    print(f"[SCRAPER] ✅ Page {len(discovered)}/{max_pages} added to collection", file=sys.stderr)
                    span.add_event(f"page_{len(discovered)}_discovered", {
                        "url": url,
                        "title": page_data.get('title', ''),
                        "content_length": len(page_data.get('content', ''))
                    })
                    
                    # Add relevant links to visit - be more aggressive for first page
                    link_limit = 50 if len(discovered) == 1 else 20
                    links_added = 0
                    for link in page_data.get('links', [])[:link_limit]:
                        link_url = link['url']
                        parsed = urlparse(link_url)
                        
                        # Remove fragments and query params for comparison
                        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                        
                        # Only follow links from same domain
                        # For library docs, be more permissive about path
                        same_domain = parsed.netloc == base_domain
                        not_visited = clean_url not in visited and clean_url not in to_visit
                        not_media = not any(clean_url.endswith(ext) for ext in ['.pdf', '.zip', '.jpg', '.png', '.gif', '.mp4'])
                        
                        if same_domain and not_visited and not_media:
                            # Prioritize docs that look like API/library docs
                            link_text_lower = link.get('text', '').lower()
                            is_priority = any(keyword in link_text_lower or keyword in clean_url.lower() 
                                            for keyword in ['api', 'reference', 'guide', 'tutorial', 'class', 'function', 'method', 'example'])
                            
                            if is_priority:
                                to_visit.insert(0, clean_url)  # Priority at front
                                links_added += 1
                            elif not base_path or parsed.path.startswith(base_path):
                                to_visit.append(clean_url)  # Regular at back
                                links_added += 1
                    
                    print(f"[SCRAPER] 🔗 Added {links_added} new links to queue (queue size: {len(to_visit)})", file=sys.stderr)
                else:
                    print(f"[SCRAPER] ⚠️  Page had no content, skipping", file=sys.stderr)
                
                # Small delay to be respectful
                await asyncio.sleep(0.3)
            
            span.set_attribute("pages.discovered", len(discovered))
            span.set_attribute("pages.visited", len(visited))
            print(f"[SCRAPER] 🎉 Discovery complete: {len(discovered)} pages scraped, {len(visited)} URLs visited", file=sys.stderr)
            span.add_event("discovery_complete", {
                "pages_discovered": len(discovered),
                "urls_visited": len(visited)
            })
            return discovered
