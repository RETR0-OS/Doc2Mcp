# Dockerfile for Doc2MCP MCP Server
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml and install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy application code
COPY doc2mcp ./doc2mcp
COPY tools.yaml .
COPY doc_cache.json .

# Create data directory
RUN mkdir -p /app/phoenix_data

# Run MCP server
CMD ["python", "-m", "doc2mcp.server"]
