"""Sitemap parser for extracting URLs from documentation sites."""

import asyncio
import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx

logger = logging.getLogger(__name__)


@dataclass
class PageInfo:
    """Information about a documentation page."""
    url: str
    path: str
    title: str  # Derived from URL path
    priority: float = 0.5
    keywords: list[str] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = self._extract_keywords()
    
    def _extract_keywords(self) -> list[str]:
        """Extract keywords from URL path."""
        # Split path into segments, remove common prefixes
        segments = [s for s in self.path.split('/') if s and s not in ('docs', 'api', 'reference', 'guide', 'en', 'v1', 'latest')]
        
        keywords = []
        for seg in segments:
            # Split camelCase and kebab-case
            words = re.split(r'[-_]', seg)
            for word in words:
                # Split camelCase
                camel_split = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', word)
                if camel_split:
                    keywords.extend([w.lower() for w in camel_split])
                else:
                    keywords.append(word.lower())
        
        return [k for k in keywords if len(k) > 1]


class SitemapParser:
    """Parse sitemap.xml to extract documentation pages."""
    
    def __init__(self, base_url: str, max_pages: int = 100):
        """
        Initialize parser.
        
        Args:
            base_url: The documentation site base URL
            max_pages: Maximum number of pages to extract
        """
        self.base_url = base_url.rstrip('/')
        self.max_pages = max_pages
        self.parsed_url = urlparse(base_url)
        
    async def parse(self) -> list[PageInfo]:
        """
        Parse sitemap and return list of documentation pages.
        
        Falls back to link extraction if no sitemap found.
        """
        pages = await self._try_sitemap()
        
        if not pages:
            logger.info(f"No sitemap found for {self.base_url}, falling back to link extraction")
            pages = await self._extract_from_page()
        
        # Filter and sort by priority
        pages = self._filter_pages(pages)
        pages.sort(key=lambda p: (-p.priority, len(p.path)))
        
        return pages[:self.max_pages]
    
    async def _try_sitemap(self) -> list[PageInfo]:
        """Try to fetch and parse sitemap.xml."""
        sitemap_urls = [
            f"{self.parsed_url.scheme}://{self.parsed_url.netloc}/sitemap.xml",
            f"{self.base_url}/sitemap.xml",
            f"{self.parsed_url.scheme}://{self.parsed_url.netloc}/sitemap_index.xml",
        ]
        
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            for sitemap_url in sitemap_urls:
                try:
                    resp = await client.get(sitemap_url)
                    # Accept any 200 response that looks like XML (some servers return wrong content-type)
                    if resp.status_code == 200:
                        content = resp.text
                        if content.strip().startswith('<?xml') or '<urlset' in content[:500]:
                            pages = self._parse_sitemap_xml(content)
                            if pages:
                                logger.info(f"Found {len(pages)} pages in {sitemap_url}")
                                return pages
                except Exception as e:
                    logger.debug(f"Failed to fetch {sitemap_url}: {e}")
                    continue
        
        return []
    
    def _parse_sitemap_xml(self, xml_content: str) -> list[PageInfo]:
        """Parse sitemap XML content."""
        pages = []
        
        try:
            # Handle namespace
            xml_content = re.sub(r'xmlns="[^"]+"', '', xml_content)
            root = ET.fromstring(xml_content)
            
            # Check if it's a sitemap index
            sitemap_refs = root.findall('.//sitemap/loc')
            if sitemap_refs:
                # It's an index, we'll just use the main sitemap
                logger.debug("Found sitemap index, using first sitemap")
            
            # Extract URLs
            for url_elem in root.findall('.//url'):
                loc = url_elem.find('loc')
                if loc is None or not loc.text:
                    continue
                
                url = loc.text.strip()
                
                # Only include URLs under our base path
                if not self._is_valid_doc_url(url):
                    continue
                
                priority = 0.5
                priority_elem = url_elem.find('priority')
                if priority_elem is not None and priority_elem.text:
                    try:
                        priority = float(priority_elem.text)
                    except ValueError:
                        pass
                
                path = urlparse(url).path
                title = self._path_to_title(path)
                
                pages.append(PageInfo(
                    url=url,
                    path=path,
                    title=title,
                    priority=priority
                ))
        
        except ET.ParseError as e:
            logger.warning(f"Failed to parse sitemap XML: {e}")
        
        return pages
    
    async def _extract_from_page(self) -> list[PageInfo]:
        """Extract links by crawling the site (limited depth, concurrent)."""
        pages = []
        seen_urls = set()
        to_crawl = {self.base_url}
        max_crawl = min(self.max_pages * 3, 100)  # Crawl up to 3x max pages, max 100
        allowed_domains = {self.parsed_url.netloc}  # Track allowed domains (includes redirects)
        
        try:
            from bs4 import BeautifulSoup
            
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                while to_crawl and len(pages) < max_crawl:
                    # Process up to 10 URLs concurrently
                    batch = list(to_crawl)[:10]
                    to_crawl -= set(batch)
                    
                    async def fetch_one(url):
                        if url in seen_urls:
                            return None, None, None
                        seen_urls.add(url)
                        
                        try:
                            resp = await client.get(url)
                            if resp.status_code != 200:
                                return None, None, None
                            return url, str(resp.url), resp.text
                        except Exception:
                            return None, None, None
                    
                    results = await asyncio.gather(*[fetch_one(u) for u in batch])
                    
                    for orig_url, actual_url, html in results:
                        if not html:
                            continue
                        
                        # Track the actual domain after redirects
                        parsed_actual = urlparse(actual_url)
                        allowed_domains.add(parsed_actual.netloc)
                        
                        soup = BeautifulSoup(html, 'lxml')
                        
                        # Add this page if valid
                        if actual_url != self.base_url:
                            path = parsed_actual.path
                            # Try to get title from page
                            title_tag = soup.find('title')
                            h1_tag = soup.find('h1')
                            title = (
                                (title_tag and title_tag.get_text(strip=True)) or
                                (h1_tag and h1_tag.get_text(strip=True)) or
                                self._path_to_title(path)
                            )
                            # Clean title
                            title = re.sub(r'\s*[|\-–—]\s*.*$', '', title)
                            
                            pages.append(PageInfo(
                                url=actual_url,
                                path=path,
                                title=title[:100],
                                priority=0.5
                            ))
                        
                        # Find more links to crawl
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            
                            # Resolve relative URLs
                            if href.startswith('/'):
                                new_url = f"{parsed_actual.scheme}://{parsed_actual.netloc}{href}"
                            elif href.startswith('http'):
                                new_url = href
                            elif not href.startswith(('#', 'mailto:', 'javascript:')):
                                new_url = urljoin(actual_url, href)
                            else:
                                continue
                            
                            # Normalize URL
                            new_url = new_url.split('#')[0].split('?')[0].rstrip('/')
                            parsed_new = urlparse(new_url)
                            
                            # Only follow links on allowed domains
                            if (new_url not in seen_urls and 
                                parsed_new.netloc in allowed_domains and
                                self._is_doc_path(parsed_new.path)):
                                to_crawl.add(new_url)
        
        except ImportError:
            logger.warning("bs4/lxml not installed, link extraction unavailable")
        except Exception as e:
            logger.warning(f"Failed to extract links from {self.base_url}: {e}")
        
        logger.info(f"Crawled {len(seen_urls)} URLs, found {len(pages)} doc pages")
        return pages
    
    def _is_doc_path(self, path: str) -> bool:
        """Check if path looks like documentation (not blog, auth, etc)."""
        skip_patterns = [
            '/blog/', '/news/', '/changelog/', '/release',
            '/auth/', '/login/', '/signup/', '/pricing/',
            '/about/', '/contact/', '/careers/', '/jobs/',
            '/search', '/404', '/500',
            '.pdf', '.zip', '.tar', '.gz',
        ]
        
        path_lower = path.lower()
        for pattern in skip_patterns:
            if pattern in path_lower:
                return False
        return True
    
    def _is_valid_doc_url(self, url: str) -> bool:
        """Check if URL is a valid documentation page."""
        parsed = urlparse(url)
        
        # Must be same domain
        if parsed.netloc != self.parsed_url.netloc:
            return False
        
        path = parsed.path.rstrip('/')
        
        # Skip root and non-doc pages (exact path matches)
        skip_exact = {'', '/search', '/playground', '/404', '/500'}
        if path in skip_exact:
            return False
        
        # Skip pages containing these patterns
        skip_patterns = [
            '/blog/', '/news/', '/changelog/', '/release',
            '/auth/', '/login/', '/signup/', '/pricing/',
            '/about/', '/contact/', '/careers/', '/jobs/',
            '.pdf', '.zip', '.tar', '.gz',
            '#', '?'
        ]
        
        path_lower = path.lower()
        for pattern in skip_patterns:
            if pattern in path_lower:
                return False
        
        # Must be under our base path (if specified)
        base_path = self.parsed_url.path.rstrip('/')
        if base_path and not path.startswith(base_path):
            return False
        
        return True
    
    def _filter_pages(self, pages: list[PageInfo]) -> list[PageInfo]:
        """Filter to most relevant documentation pages."""
        # Remove duplicates
        seen = set()
        unique = []
        for page in pages:
            # Normalize URL (remove trailing slashes, fragments)
            normalized = page.url.rstrip('/').split('#')[0].split('?')[0]
            if normalized not in seen:
                seen.add(normalized)
                unique.append(page)
        
        # Prefer pages with meaningful paths
        return [p for p in unique if len(p.path) > 1 and p.path != '/']
    
    def _path_to_title(self, path: str) -> str:
        """Convert URL path to human-readable title."""
        # Get last meaningful segment
        segments = [s for s in path.split('/') if s]
        if not segments:
            return "Home"
        
        # Use last segment
        last = segments[-1]
        
        # Remove file extension
        last = re.sub(r'\.[a-z]+$', '', last)
        
        # Convert kebab-case and snake_case to Title Case
        words = re.split(r'[-_]', last)
        title = ' '.join(w.capitalize() for w in words)
        
        return title or "Home"
