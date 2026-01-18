#!/usr/bin/env python3
"""
Test MCP client to call doc2mcp tools
"""
import asyncio
import json
import sys
import os

# Set environment variables
os.environ['DOC_URLS'] = 'https://jsonplaceholder.typicode.com/guide/'
os.environ['GEMINI_API_KEY'] = 'AIzaSyCsPEUfryC5h-ISb3Zv9G9BzfjExSrtfF0'

sys.path.insert(0, 'src/python')
from server import Doc2MCPServer

async def test_mcp_server():
    """Test the MCP server by initializing and calling a tool"""
    
    print("=" * 60)
    print("Testing Doc2MCP Server")
    print("=" * 60)
    
    # Initialize server
    server = Doc2MCPServer(os.environ['GEMINI_API_KEY'])
    
    print("\n[TEST] Step 1: Initializing server...")
    await server.initialize(os.environ['DOC_URLS'])
    
    print(f"\n[TEST] ✓ Server initialized with {len(server.tools)} tools")
    
    # List available tools
    print("\n[TEST] Step 2: Listing tools...")
    tools = await server.list_tools_handler()
    
    print(f"\n[TEST] ✓ Found {len(tools)} tools:\n")
    for i, tool in enumerate(tools[:10], 1):
        print(f"  {i}. {tool.name}")
        print(f"     Description: {tool.description[:80]}...")
        print()
    
    if len(tools) > 10:
        print(f"  ... and {len(tools) - 10} more tools\n")
    
    # Try calling a tool
    if tools:
        tool_name = tools[0].name
        print(f"[TEST] Step 3: Calling tool '{tool_name}'...")
        print(f"[TEST] Tool description: {tools[0].description}\n")
        
        # Get required parameters
        input_schema = tools[0].inputSchema
        arguments = {}
        
        # Check if tool has required parameters
        required_params = input_schema.get('required', [])
        if required_params:
            print(f"[TEST] Tool requires parameters: {required_params}")
            
            # Try to provide sensible defaults for testing
            properties = input_schema.get('properties', {})
            for param in required_params:
                param_info = properties.get(param, {})
                param_type = param_info.get('type', 'string')
                
                # Provide test values
                if 'id' in param.lower():
                    arguments[param] = 1
                elif param_type == 'number':
                    arguments[param] = 1
                elif param_type == 'boolean':
                    arguments[param] = True
                else:
                    arguments[param] = "test"
            
            print(f"[TEST] Using test arguments: {arguments}\n")
        
        # Call the tool
        try:
            result = await server.call_tool_handler(tool_name, arguments)
            
            print("[TEST] ✓ Tool execution successful!")
            print("\n[TEST] Response:")
            print("-" * 60)
            for content in result:
                if hasattr(content, 'text'):
                    response_data = json.loads(content.text)
                    print(json.dumps(response_data, indent=2))
            print("-" * 60)
            
        except Exception as e:
            print(f"[TEST] ✗ Tool execution failed: {e}")
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_mcp_server())
