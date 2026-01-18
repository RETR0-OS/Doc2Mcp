"""Tests for documentation fetchers."""

import tempfile
from pathlib import Path

import pytest

from doc2mcp.config import LocalSource
from doc2mcp.fetchers.local import LocalFetcher


class TestLocalFetcher:
    """Tests for the local file fetcher."""

    @pytest.fixture
    def fetcher(self):
        return LocalFetcher()

    @pytest.fixture
    def temp_docs(self):
        """Create temporary documentation files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            # Create some test files
            (base / "readme.md").write_text("# Test Readme\n\nSome content.")
            (base / "guide.txt").write_text("Guide content here.")
            (base / "other.json").write_text('{"not": "matched"}')

            subdir = base / "subdir"
            subdir.mkdir()
            (subdir / "nested.md").write_text("# Nested\n\nNested content.")

            yield base

    @pytest.mark.asyncio
    async def test_fetch_single_file(self, fetcher, temp_docs):
        """Test fetching a single file."""
        source = LocalSource(path=str(temp_docs / "readme.md"))
        content = await fetcher.fetch(source)
        assert "# Test Readme" in content
        assert "Some content." in content

    @pytest.mark.asyncio
    async def test_fetch_directory_with_patterns(self, fetcher, temp_docs):
        """Test fetching files matching patterns."""
        source = LocalSource(path=str(temp_docs), patterns=["*.md"])
        content = await fetcher.fetch(source)
        assert "Test Readme" in content
        assert "Guide content" not in content  # .txt not matched

    @pytest.mark.asyncio
    async def test_fetch_multiple_patterns(self, fetcher, temp_docs):
        """Test fetching with multiple patterns."""
        source = LocalSource(path=str(temp_docs), patterns=["*.md", "*.txt"])
        content = await fetcher.fetch(source)
        assert "Test Readme" in content
        assert "Guide content" in content
        assert "not" not in content  # JSON not matched

    @pytest.mark.asyncio
    async def test_nonexistent_path(self, fetcher):
        """Test fetching from nonexistent path raises error."""
        source = LocalSource(path="/nonexistent/path")
        with pytest.raises(FileNotFoundError):
            await fetcher.fetch(source)
