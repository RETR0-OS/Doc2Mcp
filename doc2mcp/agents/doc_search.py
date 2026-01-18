"""Background agent for intelligent documentation search."""

import os
from typing import Any

import google.generativeai as genai
from opentelemetry import trace

from doc2mcp.config import Config, LocalSource, ToolConfig, WebSource
from doc2mcp.fetchers.local import LocalFetcher
from doc2mcp.fetchers.web import WebFetcher
from doc2mcp.tracing.phoenix import trace_doc_retrieval, trace_llm_call


class DocSearchAgent:
    """Agent that searches documentation using Gemini for intelligent extraction.

    This agent:
    1. Fetches raw documentation from configured sources (web/local)
    2. Uses Gemini to extract the most relevant parts based on the query
    3. Returns structured, relevant documentation to the caller
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        self.web_fetcher = WebFetcher(timeout=config.settings.request_timeout)
        self.local_fetcher = LocalFetcher()

        # Initialize Gemini client
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=self._get_system_prompt(),
        )
        self.tracer = trace.get_tracer("doc2mcp.agent")

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the documentation search agent."""
        return """You are a documentation search assistant. Your job is to:
1. Read the provided documentation
2. Extract and return ONLY the parts that are relevant to the user's query
3. Preserve code examples, API signatures, and technical details
4. Format the output clearly with proper markdown
5. Include source references when available

If the documentation doesn't contain relevant information, say so clearly.
Do NOT make up information - only use what's in the provided documentation."""

    async def search(self, tool_name: str, query: str) -> dict[str, Any]:
        """Search for documentation relevant to the query.

        Args:
            tool_name: Name of the tool to search documentation for.
            query: Search query describing what information is needed.

        Returns:
            Dictionary containing:
                - content: The relevant documentation text
                - sources: List of source URLs/paths used
                - tool: Tool name and description
        """
        with self.tracer.start_as_current_span("doc_search") as span:
            span.set_attribute("tool_name", tool_name)
            span.set_attribute("query", query)

            # Get tool config
            tool_config = self.config.tools.get(tool_name)
            if not tool_config:
                available = list(self.config.tools.keys())
                return {
                    "error": f"Tool '{tool_name}' not found",
                    "available_tools": available,
                    "content": None,
                    "sources": [],
                }

            # Fetch all documentation
            raw_docs, sources = await self._fetch_all_docs(tool_config)

            if not raw_docs:
                return {
                    "error": "No documentation could be fetched",
                    "content": None,
                    "sources": sources,
                    "tool": {
                        "name": tool_config.name,
                        "description": tool_config.description,
                    },
                }

            # Use Gemini to extract relevant information
            relevant_content = await self._extract_relevant_content(
                query=query,
                tool_name=tool_config.name,
                raw_docs=raw_docs,
            )

            # Truncate if needed
            max_len = self.config.settings.max_content_length
            if len(relevant_content) > max_len:
                relevant_content = relevant_content[:max_len] + "\n\n[Content truncated...]"

            # Trace the retrieval
            trace_doc_retrieval(
                tool_name=tool_name,
                query=query,
                sources=sources,
                content_length=len(relevant_content),
            )

            return {
                "content": relevant_content,
                "sources": sources,
                "tool": {
                    "name": tool_config.name,
                    "description": tool_config.description,
                },
            }

    async def _fetch_all_docs(
        self, tool_config: ToolConfig
    ) -> tuple[str, list[str]]:
        """Fetch documentation from all configured sources.

        Args:
            tool_config: Configuration for the tool.

        Returns:
            Tuple of (combined documentation text, list of source URLs/paths).
        """
        docs_parts: list[str] = []
        sources: list[str] = []

        for source in tool_config.sources:
            try:
                if isinstance(source, WebSource):
                    content = await self.web_fetcher.fetch(source)
                    source_id = source.url
                elif isinstance(source, LocalSource):
                    content = await self.local_fetcher.fetch(source)
                    source_id = source.path
                else:
                    continue

                if content:
                    docs_parts.append(f"## Source: {source_id}\n\n{content}")
                    sources.append(source_id)

            except Exception as e:
                # Log but continue with other sources
                sources.append(f"{source.type}:error:{e!s}")

        return "\n\n---\n\n".join(docs_parts), sources

    async def _extract_relevant_content(
        self,
        query: str,
        tool_name: str,
        raw_docs: str,
    ) -> str:
        """Use Gemini to extract relevant content from documentation.

        Args:
            query: The user's search query.
            tool_name: Name of the tool.
            raw_docs: Raw combined documentation.

        Returns:
            Extracted relevant content.
        """
        # Truncate raw docs if too long for context
        # Gemini 2.5 Flash has 1M token context, but we limit for efficiency
        max_input = 500000
        if len(raw_docs) > max_input:
            raw_docs = raw_docs[:max_input] + "\n\n[Documentation truncated for processing...]"

        user_message = f"""I need documentation about: {query}

Tool: {tool_name}

Here is the raw documentation to search through:

{raw_docs}

Please extract and return the relevant documentation for my query. Include code examples if available."""

        with self.tracer.start_as_current_span("gemini_extraction") as span:
            span.set_attribute("query", query)

            response = await self.model.generate_content_async(
                user_message,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=8192,
                    temperature=0.1,
                ),
            )

            result = response.text

            # Get token counts if available
            tokens_in = None
            tokens_out = None
            if hasattr(response, "usage_metadata"):
                tokens_in = getattr(response.usage_metadata, "prompt_token_count", None)
                tokens_out = getattr(response.usage_metadata, "candidates_token_count", None)

            # Trace the LLM call
            trace_llm_call(
                model="gemini-2.5-flash",
                messages=[{"role": "user", "content": user_message[:500]}],
                response=result,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
            )

            return result

    async def list_tools(self) -> list[dict[str, str]]:
        """List all available tools.

        Returns:
            List of tool info dictionaries with name and description.
        """
        return [
            {
                "id": tool_id,
                "name": tool_config.name,
                "description": tool_config.description,
            }
            for tool_id, tool_config in self.config.tools.items()
        ]

    async def close(self) -> None:
        """Clean up resources."""
        await self.web_fetcher.close()
