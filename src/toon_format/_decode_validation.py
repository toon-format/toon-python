"""Validation functions for decoder strict mode."""

from toon_format._constants import COLON, LIST_ITEM_PREFIX
from toon_format._parser import ArrayHeaderInfo
from toon_format._scanner import BlankLineInfo, LineCursor
from toon_format.types import ResolvedDecodeOptions


def assert_expected_count(
    actual: int,
    expected: int,
    item_type: str,
    options: ResolvedDecodeOptions,
) -> None:
    """Assert that the actual count matches the expected count in strict mode.

    Per Section 14.1 of the TOON specification.

    Args:
        actual: The actual count
        expected: The expected count
        item_type: The type of items being counted
        (e.g., 'list array items', 'tabular rows')
        options: Decode options

    Raises:
        ValueError: If counts don't match in strict mode
    """
    if options.strict and actual != expected:
        raise ValueError(f"Expected {expected} {item_type}, but got {actual}")


def validate_no_extra_list_items(
    cursor: LineCursor,
    item_depth: int,
    expected_count: int,
) -> None:
    """Validate that there are no extra list items beyond the expected count.

    Args:
        cursor: The line cursor
        item_depth: The expected depth of items
        expected_count: The expected number of items

    Raises:
        ValueError: If extra items are found
    """
    if cursor.at_end():
        return

    next_line = cursor.peek()
    if (
        next_line
        and next_line.depth == item_depth
        and next_line.content.startswith(LIST_ITEM_PREFIX)
    ):
        raise ValueError(f"Expected {expected_count} list array items, but found more")


def validate_no_extra_tabular_rows(
    cursor: LineCursor,
    row_depth: int,
    header: ArrayHeaderInfo,
) -> None:
    """Validate that there are no extra tabular rows beyond the expected count.

    Args:
        cursor: The line cursor
        row_depth: The expected depth of rows
        header: The array header info containing length and delimiter

    Raises:
        ValueError: If extra rows are found
    """
    if cursor.at_end():
        return

    next_line = cursor.peek()
    if (
        next_line
        and next_line.depth == row_depth
        and not next_line.content.startswith(LIST_ITEM_PREFIX)
        and _is_data_row(next_line.content, header.delimiter)
    ):
        raise ValueError(f"Expected {header.length} tabular rows, but found more")


def validate_no_blank_lines_in_range(
    start_line: int,
    end_line: int,
    blank_lines: list[BlankLineInfo],
    strict: bool,
    context: str,
) -> None:
    """Validate that there are no blank lines within a specific line range.

    In strict mode, blank lines inside arrays/tabular rows are not allowed.
    Per Section 14.4 of the TOON specification.

    Args:
        start_line: The starting line number (inclusive)
        end_line: The ending line number (inclusive)
        blank_lines: Array of blank line information
        strict: Whether strict mode is enabled
        context: Description of the context (e.g., 'list array', 'tabular array')

    Raises:
        SyntaxError: If blank lines are found in strict mode
    """
    if not strict:
        return

    # Find blank lines within the range
    blanks_in_range = [
        blank
        for blank in blank_lines
        if (blank.line_num > start_line and blank.line_num < end_line)
    ]

    if blanks_in_range:
        raise SyntaxError(
            f"Line {blanks_in_range[0].line_num}: Blank lines inside {context} "
            "are not allowed in strict mode"
        )


def _is_data_row(content: str, delimiter: str) -> bool:
    """Check if a line represents a data row (as opposed to a key-value pair)
    in a tabular array.

    Args:
        content: The line content
        delimiter: The delimiter used in the table

    Returns:
        True if the line is a data row, False if it's a key-value pair
    """
    colon_pos = content.find(COLON)
    delimiter_pos = content.find(delimiter)

    # No colon = definitely a data row
    if colon_pos == -1:
        return True

    # Has delimiter and it comes before colon = data row
    if delimiter_pos != -1 and delimiter_pos < colon_pos:
        return True

    # Colon before delimiter or no delimiter = key-value pair
    return False
