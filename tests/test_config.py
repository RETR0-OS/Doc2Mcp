"""Tests for configuration loading."""

import tempfile
from pathlib import Path

import pytest

from doc2mcp.config import Config, LocalSource, Settings, ToolConfig, WebSource, load_config


def test_empty_config():
    """Test loading config when file doesn't exist."""
    config = load_config("/nonexistent/path.yaml")
    assert config.tools == {}
    assert config.settings.max_content_length == 50000


def test_load_config_from_yaml():
    """Test loading config from a YAML file."""
    yaml_content = """
tools:
  test_tool:
    name: "Test Tool"
    description: "A test tool"
    sources:
      - type: web
        url: "https://example.com/docs"
      - type: local
        path: "./docs"
        patterns:
          - "*.md"

settings:
  max_content_length: 10000
  cache_ttl: 1800
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        f.flush()

        config = load_config(f.name)

    assert "test_tool" in config.tools
    tool = config.tools["test_tool"]
    assert tool.name == "Test Tool"
    assert len(tool.sources) == 2
    assert isinstance(tool.sources[0], WebSource)
    assert isinstance(tool.sources[1], LocalSource)
    assert config.settings.max_content_length == 10000


def test_web_source_with_selectors():
    """Test web source with CSS selectors."""
    source = WebSource(
        url="https://example.com",
        selectors={"content": "main", "exclude": "nav, footer"},
    )
    assert source.type == "web"
    assert source.selectors["content"] == "main"


def test_local_source_default_patterns():
    """Test local source has default patterns."""
    source = LocalSource(path="./docs")
    assert source.type == "local"
    assert "*.md" in source.patterns
    assert "*.txt" in source.patterns


def test_settings_defaults():
    """Test settings have sensible defaults."""
    settings = Settings()
    assert settings.max_content_length == 50000
    assert settings.cache_ttl == 3600
    assert settings.request_timeout == 30
