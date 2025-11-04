# Copyright (c) 2025 TOON Format Organization
# SPDX-License-Identifier: MIT
"""Scanner for parsing TOON input into lines with depth information.

This module implements the first stage of the TOON decoding pipeline:
scanning the input text and converting it into structured line objects
with depth and indentation metadata. Handles strict and lenient parsing modes.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .constants import SPACE, TAB


@dataclass
class ParsedLine:
    """A parsed line with metadata.

    Attributes:
        raw: The original raw line content
        depth: The indentation depth (number of indent levels)
        indent: The number of leading spaces
        content: The line content after removing indentation
        line_num: The 1-based line number in the source
    """

    raw: str
    depth: int
    indent: int
    content: str
    line_num: int

    @property
    def is_blank(self) -> bool:
        """Check if this line is blank (only whitespace).

        Returns:
            True if the line contains only whitespace
        """
        return not self.content.strip()


@dataclass
class BlankLineInfo:
    """Information about a blank line.

    Attributes:
        line_num: The 1-based line number
        indent: The number of leading spaces
        depth: The computed indentation depth
    """

    line_num: int
    indent: int
    depth: int


class LineCursor:
    """Iterator-like class for traversing parsed lines.

    Provides methods to peek at the current line, advance to the next line,
    and check for lines at specific depths. This abstraction makes the decoder
    logic cleaner and easier to test.
    """

    def __init__(
        self,
        lines: List[ParsedLine],
        blank_lines: Optional[List[BlankLineInfo]] = None,
    ) -> None:
        """Initialize a line cursor.

        Args:
            lines: The parsed lines to traverse
            blank_lines: Optional list of blank line information
        """
        self._lines = lines
        self._index = 0
        self._blank_lines = blank_lines or []

    def get_blank_lines(self) -> List[BlankLineInfo]:
        """Get the list of blank lines."""
        return self._blank_lines

    def peek(self) -> Optional[ParsedLine]:
        """Peek at the current line without advancing.

        Returns:
            The current line, or None if at end
        """
        if self._index >= len(self._lines):
            return None
        return self._lines[self._index]

    def next(self) -> Optional[ParsedLine]:
        """Get the current line and advance.

        Returns:
            The current line, or None if at end
        """
        if self._index >= len(self._lines):
            return None
        line = self._lines[self._index]
        self._index += 1
        return line

    def current(self) -> Optional[ParsedLine]:
        """Get the most recently consumed line.

        Returns:
            The previous line, or None if no line has been consumed
        """
        if self._index > 0:
            return self._lines[self._index - 1]
        return None

    def advance(self) -> None:
        """Advance to the next line."""
        self._index += 1

    def at_end(self) -> bool:
        """Check if cursor is at the end of lines.

        Returns:
            True if at end
        """
        return self._index >= len(self._lines)

    @property
    def length(self) -> int:
        """Get the total number of lines."""
        return len(self._lines)

    def peek_at_depth(self, target_depth: int) -> Optional[ParsedLine]:
        """Peek at the next line at a specific depth.

        Args:
            target_depth: The target depth

        Returns:
            The line if it matches the depth, None otherwise
        """
        line = self.peek()
        if not line or line.depth < target_depth:
            return None
        if line.depth == target_depth:
            return line
        return None

    def has_more_at_depth(self, target_depth: int) -> bool:
        """Check if there are more lines at a specific depth.

        Args:
            target_depth: The target depth

        Returns:
            True if there are more lines at the target depth
        """
        return self.peek_at_depth(target_depth) is not None

    def skip_deeper_than(self, depth: int) -> None:
        """Skip all lines that are deeper than the given depth.

        This is useful for skipping over nested structures after processing them.

        Args:
            depth: The reference depth. All lines with depth > this will be skipped.

        Example:
            >>> cursor.skip_deeper_than(1)  # Skip all lines at depth 2, 3, 4, etc.
        """
        line = self.peek()
        while line and line.depth > depth:
            self.advance()
            line = self.peek()


def to_parsed_lines(
    source: str,
    indent_size: int,
    strict: bool,
) -> Tuple[List[ParsedLine], List[BlankLineInfo]]:
    """Convert source string to parsed lines with depth information.

    Per Section 12 of the TOON specification for indentation handling.
    This is the entry point for the scanning stage of the decoder pipeline.

    Args:
        source: The source string to parse
        indent_size: The number of spaces per indentation level
        strict: Whether to enforce strict indentation validation

    Returns:
        A tuple of (parsed_lines, blank_lines)

    Raises:
        SyntaxError: If strict mode validation fails (tabs in indentation, invalid spacing)

    Examples:
        >>> lines, blanks = to_parsed_lines("name: Alice\\n  age: 30", 2, True)
        >>> lines[0].content
        'name: Alice'
        >>> lines[1].depth
        1
    """
    if not source.strip():
        return [], []

    lines = source.split("\n")
    parsed: List[ParsedLine] = []
    blank_lines: List[BlankLineInfo] = []

    for i, raw in enumerate(lines):
        line_num = i + 1
        indent = 0
        while indent < len(raw) and raw[indent] == SPACE:
            indent += 1

        content = raw[indent:]

        # Compute depth for both blank and non-blank lines
        depth = _compute_depth_from_indent(indent, indent_size)

        # Track blank lines (but still include them in parsed list for validation)
        is_blank = not content.strip()
        if is_blank:
            blank_lines.append(
                BlankLineInfo(
                    line_num=line_num,
                    indent=indent,
                    depth=depth,
                )
            )
            # Blank lines are not validated for indentation
            # But we still add them to parsed list for array blank line detection

        # Strict mode validation (skip for blank lines)
        if strict and not is_blank:
            # Find the full leading whitespace region (spaces and tabs)
            ws_end = 0
            while ws_end < len(raw) and (raw[ws_end] == SPACE or raw[ws_end] == TAB):
                ws_end += 1

            # Check for tabs in leading whitespace (before actual content)
            if TAB in raw[:ws_end]:
                raise SyntaxError(
                    f"Line {line_num}: Tabs not allowed in indentation in strict mode"
                )

            # Check for exact multiples of indent_size
            if indent > 0 and indent % indent_size != 0:
                raise SyntaxError(
                    f"Line {line_num}: Indent must be exact multiple of {indent_size}, "
                    f"but found {indent} spaces"
                )

        parsed.append(
            ParsedLine(
                raw=raw,
                indent=indent,
                content=content,
                depth=depth,
                line_num=line_num,
            )
        )

    return parsed, blank_lines


def _compute_depth_from_indent(indent_spaces: int, indent_size: int) -> int:
    """Compute depth from indentation spaces.

    Args:
        indent_spaces: Number of leading spaces
        indent_size: Number of spaces per indentation level

    Returns:
        The computed depth

    Examples:
        >>> _compute_depth_from_indent(0, 2)
        0
        >>> _compute_depth_from_indent(4, 2)
        2
        >>> _compute_depth_from_indent(3, 2)  # Lenient mode
        1
    """
    return indent_spaces // indent_size
