# Copyright (c) 2025 TOON Format Organization
# SPDX-License-Identifier: MIT
"""Line writer for managing indented TOON output.

Provides LineWriter class that manages indented text generation with optimized
indent string caching for performance.
"""

from typing import Dict, List

from .types import Depth


class LineWriter:
    """Manages indented text output with optimized indent caching."""

    def __init__(self, indent_size: int) -> None:
        """Initialize the line writer.

        Args:
            indent_size: Number of spaces per indentation level
        """
        self._lines: List[str] = []
        # Ensure nested structures remain distinguishable even for indent=0
        normalized_indent = indent_size if indent_size > 0 else 1
        self._indentation_string = " " * normalized_indent
        self._indent_cache: Dict[int, str] = {0: ""}
        self._indent_size = indent_size

    def push(self, depth: Depth, content: str) -> None:
        """Add a line with appropriate indentation.

        Args:
            depth: Indentation depth level
            content: Content to add
        """
        # Use cached indent string for performance
        if depth not in self._indent_cache:
            if self._indent_size == 0:
                # indent=0 uses minimal spacing to preserve structure
                self._indent_cache[depth] = " " * depth
            else:
                self._indent_cache[depth] = self._indentation_string * depth
        indent = self._indent_cache[depth]
        self._lines.append(indent + content)

    def to_string(self) -> str:
        """Return all lines joined with newlines.

        Returns:
            Complete output string
        """
        return "\n".join(self._lines)
