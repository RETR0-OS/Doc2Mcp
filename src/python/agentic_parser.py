"""
Agentic documentation parser using Gemini LLM
"""
from google import genai
from google.genai import types
import json
import sys
from typing import List, Dict, Any


class AgenticParser:
    """Use Gemini to intelligently parse documentation and generate tools"""
    
    def __init__(self, gemini_api_key: str):
        from opentelemetry import trace
        self.api_key = gemini_api_key
        self.client = genai.Client(api_key=gemini_api_key)
        self.model = 'gemini-2.0-flash-exp'
        self.tracer = trace.get_tracer(__name__)
        print(f"[PARSER] 🤖 Initialized with Gemini model: {self.model}", file=sys.stderr)
        
    async def analyze_documentation(self, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze documentation to understand its structure and purpose"""
        with self.tracer.start_as_current_span("parser.analyze_documentation") as span:
            span.set_attribute("pages.count", len(pages))
            print(f"[PARSER] 🔍 Analyzing {len(pages)} documentation pages...", file=sys.stderr)
            
            # Create a summary of all pages
            summary = "Documentation Pages:\n\n"
            for i, page in enumerate(pages[:10], 1):  # Limit to first 10 pages
                summary += f"{i}. {page['title']} ({page['url']})\n"
                summary += f"   Content preview: {page['content'][:500]}...\n\n"
                print(f"[PARSER]   • Page {i}: {page['title'][:60]}", file=sys.stderr)
            
            prompt = f"""Analyze this API/library documentation and provide a structured understanding:

{summary}

Return a JSON object with:
1. "api_name": The name of the API/library
2. "description": Brief description of what it does
3. "base_url": The base URL for API calls (if applicable, otherwise empty string)
4. "documentation_type": One of: "rest_api", "graphql_api", "library_docs", "framework_docs", "other"
5. "authentication": Description of authentication method (if any)

Return ONLY valid JSON, no markdown formatting."""

            print("[PARSER] 🤖 Sending analysis request to Gemini...", file=sys.stderr)
            span.add_event("gemini_request_sent", {"prompt_length": len(prompt)})
            
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
                result = response.text.strip()
                print(f"[PARSER] ✅ Received response from Gemini ({len(result)} chars)", file=sys.stderr)
                span.add_event("gemini_response_received", {"response_length": len(result)})
                
                # Clean up markdown formatting if present
                if result.startswith('```'):
                    print("[PARSER] 🧹 Cleaning markdown formatting from response", file=sys.stderr)
                    result = result.split('```')[1]
                    if result.startswith('json'):
                        result = result[4:]
                
                analysis = json.loads(result)
                span.set_attribute("doc.name", analysis.get('api_name', 'Unknown'))
                span.set_attribute("doc.type", analysis.get('documentation_type', 'unknown'))
                span.set_attribute("doc.has_base_url", bool(analysis.get('base_url')))
                
                print(f"[PARSER] ✨ Analysis complete:", file=sys.stderr)
                print(f"[PARSER]   📚 Name: {analysis.get('api_name', 'Unknown')}", file=sys.stderr)
                print(f"[PARSER]   📊 Type: {analysis.get('documentation_type', 'unknown')}", file=sys.stderr)
                print(f"[PARSER]   🔗 Base URL: {analysis.get('base_url', 'N/A')}", file=sys.stderr)
                print(f"[PARSER]   🔐 Auth: {analysis.get('authentication', 'N/A')}", file=sys.stderr)
                span.add_event("analysis_complete", analysis)
                return analysis
                
            except Exception as e:
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                print(f"[PARSER] ❌ Error analyzing documentation: {e}", file=sys.stderr)
            return {
                "api_name": "Unknown API",
                "description": "Unable to analyze documentation",
                "base_url": "",
                "documentation_type": "other",
                "authentication": "Unknown"
            }
    
    async def extract_endpoints(self, page_content: str, page_url: str, doc_type: str) -> List[Dict[str, Any]]:
        """Extract API endpoints or functions from documentation content"""
        with self.tracer.start_as_current_span("parser.extract_endpoints") as span:
            span.set_attribute("page.url", page_url)
            span.set_attribute("doc.type", doc_type)
            span.set_attribute("content.length", len(page_content))
            
            # Adjust prompt based on documentation type
            if doc_type in ['library_docs', 'framework_docs']:
                extraction_type = "classes, methods, and functions"
                method_instruction = '"method": "FUNCTION" for all entries'
                path_instruction = '"path": Full function/method signature with parameters'
                example_path = "Scene.createDefaultCamera(name, createArcRotateCamera, target, scene)"
            elif doc_type == 'graphql_api':
                extraction_type = "GraphQL queries and mutations"
                method_instruction = '"method": "QUERY" or "MUTATION"'
                path_instruction = '"path": GraphQL operation signature'
                example_path = "query getUser($id: ID!)"
            else:  # REST API
                extraction_type = "API endpoints"
                method_instruction = '"method": HTTP method (GET/POST/PUT/DELETE/PATCH)'
                path_instruction = '"path": API path with parameter placeholders'
                example_path = "/users/{id}"
            
            print(f"[PARSER] 🔍 Extracting {extraction_type} from: {page_url[:80]}...", file=sys.stderr)
            span.set_attribute("extraction.type", extraction_type)
            
            prompt = f"""Analyze this {doc_type} documentation page and extract all {extraction_type}.

Page URL: {page_url}
Content:
{page_content[:8000]}

For each entry, provide:
1. "name": Unique identifier (use snake_case, e.g., create_scene, get_user)
2. "description": What it does (1-2 sentences)
3. {method_instruction}
4. {path_instruction} (e.g., "{example_path}")
5. "parameters": Array of parameter objects with "name", "type", "required", "description"
6. "returns": Description of return value/response

Important: Extract at least 3-10 significant entries if available.
For library documentation, focus on the most commonly used functions and classes.

Return a JSON array of objects. If no entries found, return empty array [].
Return ONLY valid JSON, no markdown formatting."""

            print(f"[PARSER] 🤖 Sending extraction request to Gemini ({len(prompt)} chars)...", file=sys.stderr)
            span.add_event("gemini_extraction_request", {"prompt_length": len(prompt)})
            
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
                result = response.text.strip()
                print(f"[PARSER] ✅ Received extraction response ({len(result)} chars)", file=sys.stderr)
                span.add_event("gemini_extraction_response", {"response_length": len(result)})
                
                # Clean up markdown formatting
                if result.startswith('```'):
                    print("[PARSER] 🧹 Cleaning markdown from response", file=sys.stderr)
                    result = result.split('```')[1]
                    if result.startswith('json'):
                        result = result[4:]
                
                endpoints = json.loads(result)
                
                if isinstance(endpoints, list):
                    span.set_attribute("endpoints.count", len(endpoints))
                    print(f"[PARSER] ✨ Successfully extracted {len(endpoints)} endpoints", file=sys.stderr)
                    for i, ep in enumerate(endpoints[:5], 1):  # Log first 5
                        print(f"[PARSER]   {i}. {ep.get('name', 'unknown')} - {ep.get('description', 'N/A')[:60]}", file=sys.stderr)
                    if len(endpoints) > 5:
                        print(f"[PARSER]   ... and {len(endpoints) - 5} more", file=sys.stderr)
                    span.add_event("endpoints_extracted", {"count": len(endpoints)})
                    return endpoints
                else:
                    print("[PARSER] ⚠️  Response was not a list, returning empty array", file=sys.stderr)
                    return []
                    
            except Exception as e:
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                print(f"[PARSER] ❌ Error extracting endpoints: {e}", file=sys.stderr)
                span.add_event("extraction_failed", {"error": str(e)})
                return endpoints
            else:
                return []
    
    async def generate_tool_schema(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """Generate MCP tool schema from endpoint description"""
        
        properties = {}
        required = []
        
        for param in endpoint.get('parameters', []):
            param_name = param.get('name', '')
            param_type = param.get('type', 'string').lower()
            
            # Map types to JSON schema types
            type_mapping = {
                'string': 'string',
                'str': 'string',
                'int': 'number',
                'integer': 'number',
                'float': 'number',
                'number': 'number',
                'bool': 'boolean',
                'boolean': 'boolean',
                'array': 'array',
                'list': 'array',
                'object': 'object',
                'dict': 'object',
            }
            
            json_type = type_mapping.get(param_type, 'string')
            
            prop_schema = {
                'type': json_type,
                'description': param.get('description', '')
            }
            
            # Handle arrays
            if json_type == 'array':
                prop_schema['items'] = {'type': 'string'}
            
            properties[param_name] = prop_schema
            
            if param.get('required', False):
                required.append(param_name)
        
        return {
            'type': 'object',
            'properties': properties,
            'required': required
        }
    
    async def create_tools_from_pages(self, pages: List[Dict[str, Any]], doc_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create MCP tools from all documentation pages"""
        with self.tracer.start_as_current_span("parser.create_tools") as span:
            span.set_attribute("pages.count", len(pages))
            span.set_attribute("doc.type", doc_analysis.get('documentation_type', 'other'))
            
            print(f"[PARSER] 🛠️  Creating tools from {len(pages)} pages...", file=sys.stderr)
            print(f"[PARSER] 📋 Documentation type: {doc_analysis.get('documentation_type', 'other')}", file=sys.stderr)
            
            all_tools = []
            doc_type = doc_analysis.get('documentation_type', 'other')
            
            for i, page in enumerate(pages, 1):
                if not page.get('content'):
                    print(f"[PARSER] ⏭️  Skipping page {i}/{len(pages)} (no content): {page.get('url', 'unknown')[:60]}...", file=sys.stderr)
                    continue
                
                print(f"[PARSER] 📄 Processing page {i}/{len(pages)}: {page.get('title', 'Untitled')[:60]}...", file=sys.stderr)
                span.add_event(f"processing_page_{i}", {"url": page['url'], "title": page.get('title', '')})
                
                # Extract endpoints from this page
                endpoints = await self.extract_endpoints(page['content'], page['url'], doc_type)
                
                for j, endpoint in enumerate(endpoints, 1):
                    print(f"[PARSER]   🔧 Creating tool {j}/{len(endpoints)}: {endpoint.get('name', 'unknown')}", file=sys.stderr)
                    # Generate tool schema
                    tool_schema = await self.generate_tool_schema(endpoint)
                    
                    tool = {
                        'name': endpoint.get('name', '').replace('-', '_').replace('.', '_'),
                        'description': endpoint.get('description', ''),
                        'method': endpoint.get('method', 'GET'),
                        'path': endpoint.get('path', ''),
                        'url': page['url'],
                        'returns': endpoint.get('returns', ''),
                        'input_schema': tool_schema
                    }
                    
                    all_tools.append(tool)
                    span.add_event("tool_created", {
                        "tool_name": tool['name'],
                        "method": tool['method'],
                        "page": i
                    })
            
            span.set_attribute("tools.total", len(all_tools))
            print(f"[PARSER] ✅ Successfully generated {len(all_tools)} tools from documentation", file=sys.stderr)
            span.add_event("tools_creation_complete", {"total_tools": len(all_tools)})
            return all_tools
