# Example: Using Doc2MCP with Petstore API

This example demonstrates how to use Doc2MCP with the Swagger Petstore API.

## Setup

1. Start the Doc2MCP server with the Petstore OpenAPI spec:

```bash
export DOC_URLS="https://petstore.swagger.io/v2/swagger.json"
npm start
```

2. The server will parse the OpenAPI spec and generate tools for all endpoints.

## Available Tools

Doc2MCP will generate the following tools:

### Pet Operations

- `getPetById` - Find pet by ID
  ```json
  {
    "petId": 1
  }
  ```

- `addPet` - Add a new pet to the store
  ```json
  {
    "body": {
      "name": "doggie",
      "photoUrls": ["https://example.com/photo.jpg"],
      "status": "available"
    }
  }
  ```

- `updatePet` - Update an existing pet
  ```json
  {
    "body": {
      "id": 1,
      "name": "doggie",
      "status": "sold"
    }
  }
  ```

- `deletePet` - Delete a pet
  ```json
  {
    "petId": 1
  }
  ```

- `findPetsByStatus` - Find pets by status
  ```json
  {
    "status": "available"
  }
  ```

### Store Operations

- `getInventory` - Returns pet inventories by status
- `placeOrder` - Place an order for a pet
- `getOrderById` - Find purchase order by ID
- `deleteOrder` - Delete purchase order by ID

### User Operations

- `createUser` - Create user
- `loginUser` - Logs user into the system
- `logoutUser` - Logs out current logged in user session
- `getUserByName` - Get user by user name
- `updateUser` - Update user
- `deleteUser` - Delete user

## Testing with MCP Client

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "petstore": {
      "command": "node",
      "args": ["/path/to/doc2mcp/dist/index.js"],
      "env": {
        "DOC_URLS": "https://petstore.swagger.io/v2/swagger.json",
        "TRACING_ENABLED": "true"
      }
    }
  }
}
```

## Example Interactions

### Get Pet by ID

Request:
```json
{
  "tool": "getPetById",
  "arguments": {
    "petId": 1
  }
}
```

Response:
```json
{
  "status": 200,
  "data": {
    "id": 1,
    "name": "doggie",
    "photoUrls": ["https://example.com/photo.jpg"],
    "status": "available"
  }
}
```

### Add a New Pet

Request:
```json
{
  "tool": "addPet",
  "arguments": {
    "body": {
      "name": "Fluffy",
      "photoUrls": ["https://example.com/fluffy.jpg"],
      "status": "available",
      "category": {
        "name": "cats"
      }
    }
  }
}
```

## Observability

With tracing enabled, you can view the execution traces in Arize Phoenix:

1. Start Phoenix:
```bash
docker run -p 6006:6006 arizephoenix/phoenix:latest
```

2. Open http://localhost:6006 in your browser

3. Execute some tools and see the traces with:
   - Tool execution time
   - Input parameters
   - Response status
   - Documentation source lineage
