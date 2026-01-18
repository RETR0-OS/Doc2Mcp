"""Local file fetcher for documentation."""

import fnmatch
from pathlib import Path

from doc2mcp.config import LocalSource


class LocalFetcher:
    """Fetches documentation from local files."""

    async def fetch(self, source: LocalSource) -> str:
        """Fetch documentation from local files.

        Args:
            source: Local source configuration with path and patterns.

        Returns:
            Combined text content from matching files.
        """
        base_path = Path(source.path).resolve()

        if not base_path.exists():
            raise FileNotFoundError(f"Documentation path not found: {base_path}")

        if base_path.is_file():
            return self._read_file(base_path)

        # Collect all matching files
        content_parts: list[str] = []

        for file_path in self._find_files(base_path, source.patterns):
            try:
                file_content = self._read_file(file_path)
                relative_path = file_path.relative_to(base_path)
                content_parts.append(f"# File: {relative_path}\n\n{file_content}")
            except Exception:
                # Skip files that can't be read
                continue

        return "\n\n---\n\n".join(content_parts)

    def _find_files(self, base_path: Path, patterns: list[str]) -> list[Path]:
        """Find all files matching the given patterns.

        Args:
            base_path: Base directory to search.
            patterns: Glob patterns to match.

        Returns:
            List of matching file paths, sorted by name.
        """
        matching_files: set[Path] = set()

        for pattern in patterns:
            # Handle recursive patterns
            if "**" in pattern:
                for file_path in base_path.rglob(pattern.replace("**/", "")):
                    if file_path.is_file():
                        matching_files.add(file_path)
            else:
                for file_path in base_path.iterdir():
                    if file_path.is_file() and fnmatch.fnmatch(file_path.name, pattern):
                        matching_files.add(file_path)

        return sorted(matching_files)

    def _read_file(self, file_path: Path) -> str:
        """Read content from a file.

        Args:
            file_path: Path to the file.

        Returns:
            File content as string.
        """
        # Try UTF-8 first, fall back to latin-1
        try:
            return file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return file_path.read_text(encoding="latin-1")
