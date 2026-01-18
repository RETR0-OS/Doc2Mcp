"""Tests for web documentation fetcher."""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from doc2mcp.config import WebSource
from doc2mcp.fetchers.web import WebFetcher


class TestWebFetcher:
    """Tests for the web documentation fetcher."""

    @pytest.fixture
    def fetcher(self):
        """Create a WebFetcher instance with direct fetching (no Jina)."""
        return WebFetcher(timeout=30, use_jina=False)

    @pytest.fixture
    def jina_fetcher(self):
        """Create a WebFetcher instance using Jina Reader."""
        return WebFetcher(timeout=30, use_jina=True)

    @pytest.fixture
    def sample_html(self):
        """Sample HTML content for testing."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Documentation</title>
            <script>console.log('remove me');</script>
            <style>.test { color: red; }</style>
        </head>
        <body>
            <nav class="sidebar">Navigation Menu</nav>
            <main class="content">
                <h1>Main Documentation</h1>
                <p>This is the main content.</p>
                <p>Multiple paragraphs here.</p>
            </main>
            <footer>Footer content</footer>
        </body>
        </html>
        """

    @pytest.mark.asyncio
    async def test_fetch_basic_html(self, fetcher, sample_html):
        """Test fetching and extracting content from basic HTML."""
        source = WebSource(url="https://doc.babylonjs.com/")

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.text = sample_html
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            content = await fetcher.fetch(source)

            assert "Main Documentation" in content
            assert "main content" in content
            assert "console.log" not in content  # Script removed
            assert ".test { color: red; }" not in content  # Style removed

    @pytest.mark.asyncio
    async def test_fetch_with_content_selector(self, fetcher, sample_html):
        """Test fetching with content selector."""
        source = WebSource(
            url="https://doc.babylonjs.com/features/introToFeatures",
            selectors={"content": "main.content"}
        )

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.text = sample_html
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            content = await fetcher.fetch(source)

            assert "Main Documentation" in content
            assert "main content" in content
            assert "Navigation Menu" not in content  # Outside main
            assert "Footer content" not in content  # Outside main

    @pytest.mark.asyncio
    async def test_fetch_with_exclude_selector(self, fetcher):
        """Test fetching with exclude selector."""
        html = """
        <html>
        <body>
            <div class="content">Important content</div>
            <div class="ads">Advertisement</div>
            <div class="sidebar">Sidebar content</div>
        </body>
        </html>
        """
        source = WebSource(
            url="https://doc.babylonjs.com/setup/",
            selectors={"exclude": ".ads, .sidebar"}
        )

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.text = html
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            content = await fetcher.fetch(source)

            assert "Important content" in content
            assert "Advertisement" not in content
            assert "Sidebar content" not in content

    @pytest.mark.asyncio
    async def test_fetch_with_multiple_selectors(self, fetcher):
        """Test fetching with both content and exclude selectors."""
        html = """
        <html>
        <body>
            <nav>Navigation</nav>
            <main id="docs">
                <article>Article content</article>
                <aside class="notes">Side notes</aside>
            </main>
            <footer>Footer</footer>
        </body>
        </html>
        """
        source = WebSource(
            url="https://doc.babylonjs.com/typedoc/",
            selectors={
                "content": "main#docs",
                "exclude": "aside.notes"
            }
        )

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.text = html
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            content = await fetcher.fetch(source)

            assert "Article content" in content
            assert "Side notes" not in content
            assert "Navigation" not in content
            assert "Footer" not in content

    @pytest.mark.asyncio
    async def test_extract_content_cleans_whitespace(self, fetcher):
        """Test that excessive whitespace is cleaned up."""
        html = """
        <html>
        <body>
            <p>First paragraph</p>


            <p>Second paragraph</p>



            <p>Third paragraph</p>
        </body>
        </html>
        """
        source = WebSource(url="https://doc.babylonjs.com/journey/")

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.text = html
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            content = await fetcher.fetch(source)

            # Should have single newlines between paragraphs, not multiple
            assert "\n\n\n" not in content
            assert "First paragraph" in content
            assert "Second paragraph" in content
            assert "Third paragraph" in content

    @pytest.mark.asyncio
    async def test_fetch_follows_redirects(self, fetcher):
        """Test that HTTP client follows redirects."""
        source = WebSource(url="https://doc.babylonjs.com/start")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.text = "<html><body>Redirected content</body></html>"
            mock_response.raise_for_status = Mock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            # Create new fetcher to test client creation
            new_fetcher = WebFetcher()
            content = await new_fetcher.fetch(source)

            assert "Redirected content" in content
            # Verify client was created with follow_redirects=True
            mock_client_class.assert_called_once()
            call_kwargs = mock_client_class.call_args[1]
            assert call_kwargs["follow_redirects"] is True

    @pytest.mark.asyncio
    async def test_fetch_raises_on_http_error(self, fetcher):
        """Test that HTTP errors are properly raised."""
        source = WebSource(url="https://doc.babylonjs.com/not-found")

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status = Mock(
                side_effect=Exception("404 Not Found")
            )
            mock_get.return_value = mock_response

            with pytest.raises(Exception, match="404 Not Found"):
                await fetcher.fetch(source)

    @pytest.mark.asyncio
    async def test_client_reuse(self, fetcher):
        """Test that HTTP client is reused across requests."""
        source = WebSource(url="https://doc.babylonjs.com/")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.text = "<html><body>Content</body></html>"
            mock_response.raise_for_status = Mock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            # Make multiple requests
            await fetcher.fetch(source)
            await fetcher.fetch(source)

            # Client should only be created once
            assert mock_client_class.call_count == 1

    @pytest.mark.asyncio
    async def test_close_client(self, fetcher):
        """Test closing the HTTP client."""
        source = WebSource(url="https://doc.babylonjs.com/")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.text = "<html><body>Content</body></html>"
            mock_response.raise_for_status = Mock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            # Fetch to create client
            await fetcher.fetch(source)

            # Close client
            await fetcher.close()

            # Verify aclose was called
            mock_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_without_client(self, fetcher):
        """Test closing when no client exists."""
        # Should not raise an error
        await fetcher.close()

    def test_extract_content_removes_script_tags(self, fetcher):
        """Test that script tags are removed from content."""
        html = """
        <html>
        <body>
            <script>alert('test');</script>
            <p>Real content</p>
            <script src="app.js"></script>
        </body>
        </html>
        """
        content = fetcher._extract_content(html)

        assert "Real content" in content
        assert "alert" not in content
        assert "app.js" not in content

    def test_extract_content_removes_style_tags(self, fetcher):
        """Test that style tags are removed from content."""
        html = """
        <html>
        <head>
            <style>.class { color: blue; }</style>
        </head>
        <body>
            <p>Real content</p>
        </body>
        </html>
        """
        content = fetcher._extract_content(html)

        assert "Real content" in content
        assert "color: blue" not in content

    def test_extract_content_removes_noscript_tags(self, fetcher):
        """Test that noscript tags are removed from content."""
        html = """
        <html>
        <body>
            <noscript>Please enable JavaScript</noscript>
            <p>Real content</p>
        </body>
        </html>
        """
        content = fetcher._extract_content(html)

        assert "Real content" in content
        assert "enable JavaScript" not in content

    def test_custom_timeout(self):
        """Test creating fetcher with custom timeout."""
        fetcher = WebFetcher(timeout=60)
        assert fetcher.timeout == 60

    def test_default_timeout(self):
        """Test default timeout value."""
        fetcher = WebFetcher()
        assert fetcher.timeout == 30

    def test_default_uses_jina(self):
        """Test that Jina is used by default."""
        fetcher = WebFetcher()
        assert fetcher.use_jina is True

    def test_disable_jina(self):
        """Test disabling Jina reader."""
        fetcher = WebFetcher(use_jina=False)
        assert fetcher.use_jina is False

    @pytest.mark.asyncio
    async def test_jina_fetch_constructs_correct_url(self, jina_fetcher):
        """Test that Jina fetch uses the correct URL prefix."""
        source = WebSource(url="https://doc.babylonjs.com/")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.text = "# Babylon.js Documentation\n\nThis is the content."
            mock_response.raise_for_status = Mock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            content = await jina_fetcher.fetch(source)

            # Verify Jina URL was called
            mock_client.get.assert_called_with("https://r.jina.ai/https://doc.babylonjs.com/")
            assert "Babylon.js Documentation" in content

    @pytest.mark.asyncio
    async def test_jina_fetch_returns_markdown(self, jina_fetcher):
        """Test that Jina fetch returns markdown content directly."""
        source = WebSource(url="https://docs.example.com/")
        markdown_content = """# Documentation

## Getting Started

This is a guide to get started.

```javascript
const example = 'code';
```
"""

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.text = markdown_content
            mock_response.raise_for_status = Mock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            content = await jina_fetcher.fetch(source)

            assert "# Documentation" in content
            assert "## Getting Started" in content
            assert "```javascript" in content

    @pytest.mark.asyncio
    async def test_jina_cleans_excessive_whitespace(self, jina_fetcher):
        """Test that Jina fetch cleans up excessive whitespace."""
        source = WebSource(url="https://docs.example.com/")
        content_with_whitespace = "Line 1\n\n\n\n\nLine 2\n\n\n\nLine 3"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.text = content_with_whitespace
            mock_response.raise_for_status = Mock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            content = await jina_fetcher.fetch(source)

            # Should not have more than 2 consecutive newlines
            assert "\n\n\n" not in content
            assert "Line 1" in content
            assert "Line 2" in content
            assert "Line 3" in content
