"""Arize Phoenix tracing setup for observability."""

import functools
import logging
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable

# Global tracer instance
_tracer: Any | None = None
_tracing_available = False

# Try to import tracing dependencies
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    _tracing_available = True
except ImportError:
    trace = None
    TracerProvider = None
    SimpleSpanProcessor = None

logger = logging.getLogger(__name__)

# Default Phoenix data directory (stable path, not temp)
DEFAULT_PHOENIX_DIR = Path("./phoenix_data")


def init_tracing(service_name: str = "doc2mcp") -> Any:
    """Initialize Arize Phoenix tracing.

    This sets up OpenTelemetry tracing with Phoenix as the backend.
    If PHOENIX_API_KEY is set, it connects to cloud Phoenix.
    Otherwise, it starts a local Phoenix instance.

    Args:
        service_name: Name of the service for tracing.

    Returns:
        Configured tracer instance or None if tracing is not available.
    """
    global _tracer

    if _tracer is not None:
        return _tracer

    if not _tracing_available:
        logger.info("Tracing not available - opentelemetry not installed")
        return None

    # Import Phoenix here to avoid import errors if not installed
    try:
        import phoenix as px
        from phoenix.otel import register
    except ImportError:
        # Phoenix not installed, return a no-op tracer
        logger.info("Phoenix not installed - tracing disabled")
        provider = TracerProvider()
        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer(service_name)
        return _tracer

    # Check for cloud Phoenix configuration
    phoenix_api_key = os.environ.get("PHOENIX_API_KEY")
    collector_endpoint = os.environ.get(
        "PHOENIX_COLLECTOR_ENDPOINT", "https://app.phoenix.arize.com"
    )

    if phoenix_api_key:
        # Use cloud Phoenix
        tracer_provider = register(
            project_name=service_name,
            endpoint=collector_endpoint,
            headers={"api_key": phoenix_api_key},
        )
    else:
        # Start local Phoenix instance with stable storage path
        phoenix_dir = Path(os.environ.get("PHOENIX_WORKING_DIR", str(DEFAULT_PHOENIX_DIR)))
        phoenix_dir.mkdir(parents=True, exist_ok=True)

        # Set env var for Phoenix to use (it reads PHOENIX_WORKING_DIR)
        os.environ["PHOENIX_WORKING_DIR"] = str(phoenix_dir.absolute())

        # use_temp_dir=False makes Phoenix use PHOENIX_WORKING_DIR for SQLite storage
        px.launch_app(use_temp_dir=False)
        tracer_provider = register(project_name=service_name)

    _tracer = trace.get_tracer(service_name)
    return _tracer


def get_tracer() -> trace.Tracer:
    """Get the global tracer instance.

    Returns:
        The tracer, initializing if needed.
    """
    global _tracer
    if _tracer is None:
        return init_tracing()
    return _tracer


def trace_llm_call(
    model: str,
    messages: list[dict[str, Any]],
    response: str,
    tokens_in: int | None = None,
    tokens_out: int | None = None,
) -> None:
    """Record an LLM call in the trace.

    Args:
        model: Model name/ID used.
        messages: Input messages.
        response: Model response.
        tokens_in: Input token count (optional).
        tokens_out: Output token count (optional).
    """
    tracer = get_tracer()

    with tracer.start_as_current_span("llm_call") as span:
        span.set_attribute("llm.model", model)
        span.set_attribute("llm.messages", str(messages))
        span.set_attribute("llm.response", response[:1000])  # Truncate for storage

        if tokens_in is not None:
            span.set_attribute("llm.tokens_in", tokens_in)
        if tokens_out is not None:
            span.set_attribute("llm.tokens_out", tokens_out)


def trace_doc_retrieval(
    tool_name: str,
    query: str,
    sources: list[str],
    content_length: int,
) -> None:
    """Record a documentation retrieval in the trace.

    Args:
        tool_name: Name of the tool whose docs were fetched.
        query: Search query used.
        sources: List of source URLs/paths used.
        content_length: Length of retrieved content.
    """
    tracer = get_tracer()

    with tracer.start_as_current_span("doc_retrieval") as span:
        span.set_attribute("doc.tool_name", tool_name)
        span.set_attribute("doc.query", query)
        span.set_attribute("doc.sources", str(sources))
        span.set_attribute("doc.content_length", content_length)


@contextmanager
def trace_mcp_call(tool_name: str, arguments: dict[str, Any] | None = None):
    """Context manager to trace an MCP tool call.

    Args:
        tool_name: Name of the MCP tool being called.
        arguments: Arguments passed to the tool.

    Yields:
        The span for additional attributes.
    """
    tracer = get_tracer()
    if tracer is None:
        yield None
        return

    with tracer.start_as_current_span(
        "mcp_tool_call",
        attributes={
            "mcp.tool_name": tool_name,
            "mcp.arguments": str(arguments) if arguments else "{}",
        },
    ) as span:
        try:
            yield span
            span.set_attribute("mcp.status", "success")
        except Exception as e:
            span.set_attribute("mcp.status", "error")
            span.set_attribute("mcp.error", str(e))
            span.record_exception(e)
            raise
