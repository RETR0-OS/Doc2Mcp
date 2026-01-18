"""Documentation fetchers for web and local sources."""

from doc2mcp.fetchers.local import LocalFetcher
from doc2mcp.fetchers.web import FetchResult, WebFetcher

__all__ = ["WebFetcher", "LocalFetcher", "FetchResult"]
