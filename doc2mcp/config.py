"""Configuration loading and validation for Doc2MCP."""

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field


class WebSource(BaseModel):
    """Web-based documentation source."""

    type: Literal["web"] = "web"
    url: str
    selectors: dict[str, str] | None = None
    sitemap_url: str | None = None  # Optional explicit sitemap URL
    index_depth: int = Field(default=3, ge=1, le=10)  # Crawl depth if no sitemap


class LocalSource(BaseModel):
    """Local file-based documentation source."""

    type: Literal["local"] = "local"
    path: str
    patterns: list[str] = Field(default_factory=lambda: ["*.md", "*.txt"])


Source = WebSource | LocalSource


class ToolConfig(BaseModel):
    """Configuration for a single tool's documentation."""

    name: str
    description: str
    sources: list[WebSource | LocalSource]


class CompressionSettings(BaseModel):
    """Settings for token compression using tokenc."""

    enabled: bool = True
    aggressiveness: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Compression aggressiveness (0.0-1.0). Higher = more compression.",
    )
    min_content_length: int = Field(
        default=1000,
        description="Minimum content length to trigger compression.",
    )
    analysis_aggressiveness: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Compression level for page analysis (moderate).",
    )
    synthesis_aggressiveness: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Compression level for answer synthesis (light).",
    )


class SitemapIndexSettings(BaseModel):
    """Settings for sitemap-based URL indexing."""

    enabled: bool = Field(
        default=True,
        description="Enable sitemap indexing for faster URL lookup.",
    )
    ttl: int = Field(
        default=86400,
        ge=0,
        description="Time-to-live for sitemap index in seconds (default: 24 hours).",
    )
    max_urls_per_domain: int = Field(
        default=1000,
        ge=100,
        le=10000,
        description="Maximum URLs to index per domain.",
    )
    parallel_fetch_limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum concurrent fetches during crawling.",
    )
    min_match_score: float = Field(
        default=1.0,
        ge=0.0,
        description="Minimum score for URL matches to be considered relevant.",
    )
    max_url_candidates: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum URL candidates to fetch directly from sitemap index.",
    )


class Settings(BaseModel):
    """Global settings for Doc2MCP."""

    max_content_length: int = 50000
    cache_ttl: int = 3600
    request_timeout: int = 30
    compression: CompressionSettings = Field(default_factory=CompressionSettings)
    sitemap_index: SitemapIndexSettings = Field(default_factory=SitemapIndexSettings)


class Config(BaseModel):
    """Root configuration model."""

    tools: dict[str, ToolConfig] = Field(default_factory=dict)
    settings: Settings = Field(default_factory=Settings)


def load_config(config_path: str | Path | None = None) -> Config:
    """Load configuration from YAML file.

    Args:
        config_path: Path to the config file. Defaults to TOOLS_CONFIG_PATH env var
                     or ./tools.yaml.

    Returns:
        Parsed configuration object.
    """
    if config_path is None:
        config_path = os.environ.get("TOOLS_CONFIG_PATH", "./tools.yaml")

    path = Path(config_path)
    if not path.exists():
        # Return empty config if file doesn't exist
        return Config()

    with open(path) as f:
        raw = yaml.safe_load(f) or {}

    return Config.model_validate(raw)
