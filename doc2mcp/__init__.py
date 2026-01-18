"""Doc2MCP - MCP server for tool documentation search."""

from doc2mcp.compression import (
    CompressionResult,
    ContentCompressor,
    compress_content,
    get_compressor,
)

__version__ = "0.1.0"

__all__ = [
    "CompressionResult",
    "ContentCompressor",
    "compress_content",
    "get_compressor",
]
