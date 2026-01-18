#!/usr/bin/env python3
"""
Quick test of the Doc2MCP server
"""
import sys
import asyncio
sys.path.insert(0, 'src/python')

from doc_scraper import DocScraper
from agentic_parser import AgenticParser

async def test_scraper():
    """Test documentation scraping"""
    print("Testing Doc2MCP components...")
    
    # Test with JSONPlaceholder
    api_key = "AIzaSyCsPEUfryC5h-ISb3Zv9G9BzfjExSrtfF0"
    url = "https://jsonplaceholder.typicode.com/"
    
    print(f"\n1. Testing scraper with {url}")
    scraper = DocScraper(api_key)
    pages = await scraper.discover_related_pages(url, max_pages=5)
    print(f"   ✓ Scraped {len(pages)} pages")
    
    print("\n2. Testing parser")
    parser = AgenticParser(api_key)
    analysis = await parser.analyze_documentation(pages)
    print(f"   ✓ Identified: {analysis.get('api_name')}")
    print(f"   ✓ Type: {analysis.get('documentation_type')}")
    print(f"   ✓ Base URL: {analysis.get('base_url')}")
    
    print("\n3. Generating tools")
    tools = await parser.create_tools_from_pages(pages, analysis)
    print(f"   ✓ Generated {len(tools)} tools")
    
    if tools:
        print("\n   Sample tools:")
        for tool in tools[:5]:
            print(f"     - {tool['name']}: {tool['description'][:60]}...")
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_scraper())
