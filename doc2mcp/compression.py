"""Token compression utilities using The Token Company's tokenc library.

This module provides content compression for reducing LLM token usage
when processing large documentation content.
"""

import os
from dataclasses import dataclass
from typing import Any

from opentelemetry import trace

# Optional tokenc integration - gracefully degrade if API key not available
try:
    from tokenc import (
        APIError,
        AuthenticationError,
        CompressionSettings,
        InvalidRequestError,
        RateLimitError,
        TokenClient,
    )
    TOKENC_AVAILABLE = True
except ImportError:
    TOKENC_AVAILABLE = False
    TokenClient = None
    CompressionSettings = None


@dataclass
class CompressionResult:
    """Result of a compression operation."""

    original_text: str
    compressed_text: str
    original_tokens: int
    compressed_tokens: int
    tokens_saved: int
    compression_ratio: float
    was_compressed: bool


class ContentCompressor:
    """Compresses documentation content to reduce LLM token usage.

    This compressor uses The Token Company's API to intelligently compress
    text while preserving semantic meaning and important details like code.

    If the TOKENC_API_KEY environment variable is not set, or if the tokenc
    library is not available, compression is silently skipped and original
    content is returned.
    """

    def __init__(
        self,
        api_key: str | None = None,
        aggressiveness: float = 0.5,
        min_content_length: int = 1000,
        enabled: bool = True,
    ) -> None:
        """Initialize the content compressor.

        Args:
            api_key: The Token Company API key. If None, reads from
                     TOKENC_API_KEY environment variable.
            aggressiveness: Compression aggressiveness from 0.0 to 1.0.
                           Lower values preserve more content.
                           - 0.1-0.3: Light compression
                           - 0.4-0.6: Moderate compression (recommended)
                           - 0.7-0.9: Aggressive compression
            min_content_length: Minimum content length to trigger compression.
                               Content shorter than this is returned as-is.
            enabled: Whether compression is enabled.
        """
        self.aggressiveness = aggressiveness
        self.min_content_length = min_content_length
        self.enabled = enabled
        self.tracer = trace.get_tracer("doc2mcp.compression")

        # Initialize client if possible
        self._client = None
        if enabled and TOKENC_AVAILABLE:
            api_key = api_key or os.environ.get("TOKENC_API_KEY")
            if api_key:
                try:
                    self._client = TokenClient(api_key=api_key)
                except Exception:
                    # Silently fail - compression will be disabled
                    pass

    @property
    def is_available(self) -> bool:
        """Check if compression is available and configured."""
        return self._client is not None

    def compress(
        self,
        content: str,
        aggressiveness: float | None = None,
        max_output_tokens: int | None = None,
    ) -> CompressionResult:
        """Compress text content to reduce token count.

        Args:
            content: The text content to compress.
            aggressiveness: Override default aggressiveness for this call.
            max_output_tokens: Optional maximum tokens for compressed output.

        Returns:
            CompressionResult with original and compressed text, plus metrics.
        """
        # Return original if compression is not available or content is too short
        if not self.is_available or len(content) < self.min_content_length:
            return CompressionResult(
                original_text=content,
                compressed_text=content,
                original_tokens=0,
                compressed_tokens=0,
                tokens_saved=0,
                compression_ratio=1.0,
                was_compressed=False,
            )

        with self.tracer.start_as_current_span("compress_content") as span:
            span.set_attribute("content_length", len(content))
            span.set_attribute("aggressiveness", aggressiveness or self.aggressiveness)

            try:
                # Build compression settings
                settings_kwargs: dict[str, Any] = {
                    "aggressiveness": aggressiveness or self.aggressiveness,
                }
                if max_output_tokens:
                    settings_kwargs["max_output_tokens"] = max_output_tokens

                settings = CompressionSettings(**settings_kwargs)

                # Compress
                response = self._client.compress_input(
                    input=content,
                    compression_settings=settings,
                )

                result = CompressionResult(
                    original_text=content,
                    compressed_text=response.output,
                    original_tokens=response.original_input_tokens,
                    compressed_tokens=response.output_tokens,
                    tokens_saved=response.tokens_saved,
                    compression_ratio=response.compression_ratio,
                    was_compressed=True,
                )

                span.set_attribute("original_tokens", result.original_tokens)
                span.set_attribute("compressed_tokens", result.compressed_tokens)
                span.set_attribute("tokens_saved", result.tokens_saved)
                span.set_attribute("compression_ratio", result.compression_ratio)

                return result

            except (AuthenticationError, InvalidRequestError, RateLimitError, APIError) as e:
                # Log error and return original content
                span.set_attribute("error", str(e))
                return CompressionResult(
                    original_text=content,
                    compressed_text=content,
                    original_tokens=0,
                    compressed_tokens=0,
                    tokens_saved=0,
                    compression_ratio=1.0,
                    was_compressed=False,
                )
            except Exception as e:
                # Catch any unexpected errors
                span.set_attribute("error", str(e))
                return CompressionResult(
                    original_text=content,
                    compressed_text=content,
                    original_tokens=0,
                    compressed_tokens=0,
                    tokens_saved=0,
                    compression_ratio=1.0,
                    was_compressed=False,
                )

    def compress_for_analysis(self, content: str) -> str:
        """Compress content for page analysis (moderate compression).

        Uses moderate compression settings suitable for analyzing
        documentation pages while preserving key details.

        Args:
            content: The documentation content to compress.

        Returns:
            Compressed content string.
        """
        result = self.compress(content, aggressiveness=0.4)
        return result.compressed_text

    def compress_for_synthesis(self, content: str) -> str:
        """Compress content for answer synthesis (light compression).

        Uses lighter compression to preserve more detail in the final
        answer synthesis step where accuracy is critical.

        Args:
            content: The combined documentation content.

        Returns:
            Compressed content string.
        """
        result = self.compress(content, aggressiveness=0.3)
        return result.compressed_text


# Default global compressor instance
_default_compressor: ContentCompressor | None = None


def get_compressor() -> ContentCompressor:
    """Get or create the default content compressor instance.

    Returns:
        The default ContentCompressor instance.
    """
    global _default_compressor
    if _default_compressor is None:
        _default_compressor = ContentCompressor()
    return _default_compressor


def compress_content(content: str, aggressiveness: float = 0.5) -> str:
    """Convenience function to compress content using default compressor.

    Args:
        content: The text content to compress.
        aggressiveness: Compression aggressiveness from 0.0 to 1.0.

    Returns:
        Compressed content string.
    """
    compressor = get_compressor()
    result = compressor.compress(content, aggressiveness=aggressiveness)
    return result.compressed_text
