"""Scanner for parsing TOON input into lines with depth information."""

from dataclasses import dataclass

from toon_format._constants import SPACE, TAB


@dataclass
class ParsedLine:
    """A parsed line with metadata."""

    raw: str
    depth: int
    indent: int
    content: str
    line_num: int


@dataclass
class BlankLineInfo:
    """Information about a blank line."""

    line_num: int
    indent: int
    depth: int


class LineCursor:
    """Iterator-like class for traversing parsed lines."""

    def __init__(
        self,
        lines: list[ParsedLine],
        blank_lines: list[BlankLineInfo] | None = None,
    ) -> None:
        """Initialize a line cursor.

        Args:
            lines: The parsed lines to traverse
            blank_lines: Optional list of blank line information
        """
        self._lines = lines
        self._index = 0
        self._blank_lines = blank_lines or []

    def get_blank_lines(self) -> list[BlankLineInfo]:
        """Get the list of blank lines."""
        return self._blank_lines

    def peek(self) -> ParsedLine | None:
        """Peek at the current line without advancing.

        Returns:
            The current line, or None if at end
        """
        if self._index >= len(self._lines):
            return None
        return self._lines[self._index]

    def next(self) -> ParsedLine | None:
        """Get the current line and advance.

        Returns:
            The current line, or None if at end
        """
        if self._index >= len(self._lines):
            return None
        line = self._lines[self._index]
        self._index += 1
        return line

    def current(self) -> ParsedLine | None:
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

    def peek_at_depth(self, target_depth: int) -> ParsedLine | None:
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


def to_parsed_lines(
    source: str,
    indent_size: int,
    strict: bool,
) -> tuple[list[ParsedLine], list[BlankLineInfo]]:
    """Convert source string to parsed lines with depth information.

    Per Section 12 of the TOON specification for indentation handling.

    Args:
        source: The source string to parse
        indent_size: The number of spaces per indentation level
        strict: Whether to enforce strict indentation validation

    Returns:
        A tuple of (parsed_lines, blank_lines)

    Raises:
        SyntaxError: If strict mode validation fails (tabs indented, invalid spacing)
    """
    if not source.strip():
        return [], []

    lines = source.split("\n")
    parsed: list[ParsedLine] = []
    blank_lines: list[BlankLineInfo] = []

    for i, raw in enumerate(lines):
        line_num = i + 1
        indent = 0
        while indent < len(raw) and raw[indent] == SPACE:
            indent += 1

        content = raw[indent:]

        # Track blank lines
        if not content.strip():
            depth = _compute_depth_from_indent(indent, indent_size)
            blank_lines.append(
                BlankLineInfo(
                    line_num=line_num,
                    indent=indent,
                    depth=depth,
                )
            )
            continue

        depth = _compute_depth_from_indent(indent, indent_size)

        # Strict mode validation
        if strict:
            # Find the full leading whitespace region (spaces and tabs)
            ws_end = 0
            while ws_end < len(raw) and (raw[ws_end] == SPACE or raw[ws_end] == TAB):
                ws_end += 1

            # Check for tabs in leading whitespace (before actual content)
            if TAB in raw[:ws_end]:
                raise SyntaxError(
                    f"Line {line_num}: Tabs not allowed in indentation in strict mode"
                )

            # Check for exact multiples of indentSize
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
    """
    return indent_spaces // indent_size
