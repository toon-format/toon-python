"""Writer for building TOON output lines."""

from toon_format._constants import LIST_ITEM_PREFIX


class LineWriter:
    """Writer for accumulating formatted TOON lines."""

    def __init__(self, indent_size: int):
        """Initialize a line writer.

        Args:
            indent_size: Number of spaces per indentation level
        """
        self._lines: list[str] = []
        self._indentation_string = " " * indent_size

    def push(self, depth: int, content: str) -> None:
        """Add a line with indentation.

        Args:
            depth: The indentation depth
            content: The line content
        """
        indent = self._indentation_string * depth
        self._lines.append(indent + content)

    def push_list_item(self, depth: int, content: str) -> None:
        """Add a list item line with indentation.

        Args:
            depth: The indentation depth
            content: The line content (without the '- ' prefix)
        """
        self.push(depth, f"{LIST_ITEM_PREFIX}{content}")

    def __str__(self) -> str:
        """Get the formatted output (no trailing newline).

        Returns:
            The joined lines without trailing newline
        """
        return "\n".join(self._lines)
