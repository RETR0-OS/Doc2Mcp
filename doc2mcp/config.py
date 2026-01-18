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


class Settings(BaseModel):
    """Global settings for Doc2MCP."""

    max_content_length: int = 50000
    cache_ttl: int = 3600
    request_timeout: int = 30


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
