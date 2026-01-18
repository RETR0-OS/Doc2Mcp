"""
OpenAPI/Swagger specification parser
"""
import httpx
from typing import Dict, List, Any
from urllib.parse import urlparse


class OpenAPIParser:
    """Parse OpenAPI/Swagger specifications"""
    
    def __init__(self, spec_url: str):
        self.spec_url = spec_url
        self.spec: Dict[str, Any] = {}
        self.base_url = ""
        
    async def load_spec(self):
        """Load and parse OpenAPI specification"""
        async with httpx.AsyncClient() as client:
            response = await client.get(self.spec_url)
            response.raise_for_status()
            self.spec = response.json()
            
        # Determine base URL
        if "servers" in self.spec and self.spec["servers"]:
            self.base_url = self.spec["servers"][0]["url"]
        elif "schemes" in self.spec and "host" in self.spec:
            scheme = self.spec["schemes"][0] if self.spec["schemes"] else "https"
            host = self.spec["host"]
            base_path = self.spec.get("basePath", "")
            self.base_url = f"{scheme}://{host}{base_path}"
        else:
            # Fallback to spec URL host
            parsed = urlparse(self.spec_url)
            self.base_url = f"{parsed.scheme}://{parsed.netloc}"
            
    def get_operations(self) -> List[Dict[str, Any]]:
        """Extract all operations from the spec"""
        operations = []
        paths = self.spec.get("paths", {})
        
        for path, path_item in paths.items():
            for method in ["get", "post", "put", "delete", "patch"]:
                if method in path_item:
                    operation = path_item[method]
                    operations.append({
                        "path": path,
                        "method": method.upper(),
                        "operation_id": operation.get("operationId", f"{method}_{path}"),
                        "summary": operation.get("summary", ""),
                        "description": operation.get("description", ""),
                        "parameters": operation.get("parameters", []),
                        "request_body": operation.get("requestBody", {}),
                        "responses": operation.get("responses", {}),
                    })
                    
        return operations
    
    def operation_to_tool_schema(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Convert OpenAPI operation to MCP tool schema"""
        properties = {}
        required = []
        
        # Process parameters
        for param in operation.get("parameters", []):
            param_name = param["name"]
            param_type = param.get("type", "string")
            
            param_schema = {
                "type": self._convert_type(param_type),
                "description": param.get("description", "")
            }
            
            # Handle array types - must include items
            if param_type == "array":
                items = param.get("items", {})
                if items:
                    item_schema = {
                        "type": self._convert_type(items.get("type", "string"))
                    }
                    # Handle enum in array items
                    if items.get("enum"):
                        item_schema["enum"] = items["enum"]
                    param_schema["items"] = item_schema
                else:
                    # Default to string array if items not specified
                    param_schema["items"] = {"type": "string"}
            
            # Handle enum at parameter level (not for array items)
            if param.get("enum") and param_type != "array":
                param_schema["enum"] = param["enum"]
                
            properties[param_name] = param_schema
            
            if param.get("required", False):
                required.append(param_name)
        
        # Process request body
        if "requestBody" in operation and operation["requestBody"]:
            content = operation["requestBody"].get("content", {})
            if "application/json" in content:
                schema = content["application/json"].get("schema", {})
                if "properties" in schema:
                    # Convert each property schema properly
                    for prop_name, prop_schema in schema["properties"].items():
                        properties[prop_name] = self._convert_schema(prop_schema)
                if "required" in schema:
                    required.extend(schema["required"])
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
    
    def _convert_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert OpenAPI schema to JSON schema with proper handling of arrays"""
        if not isinstance(schema, dict):
            return {"type": "string"}
        
        result = {}
        
        # Convert type
        if "type" in schema:
            result["type"] = self._convert_type(schema["type"])
        
        # Add description if present
        if "description" in schema:
            result["description"] = schema["description"]
        
        # Handle array items
        if schema.get("type") == "array" and "items" in schema:
            result["items"] = self._convert_schema(schema["items"])
        elif schema.get("type") == "array":
            # Default to string array if items not specified
            result["items"] = {"type": "string"}
        
        # Handle object properties
        if "properties" in schema:
            result["properties"] = {
                k: self._convert_schema(v) 
                for k, v in schema["properties"].items()
            }
        
        # Handle required fields
        if "required" in schema:
            result["required"] = schema["required"]
        
        # Handle enum
        if "enum" in schema:
            result["enum"] = schema["enum"]
        
        return result
    
    def _convert_type(self, openapi_type: str) -> str:
        """Convert OpenAPI type to JSON schema type"""
        type_map = {
            "integer": "number",
            "number": "number",
            "string": "string",
            "boolean": "boolean",
            "array": "array",
            "object": "object"
        }
        return type_map.get(openapi_type, "string")
