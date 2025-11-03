"""String utilities for TOON encoding and decoding."""

from toon_format._constants import (
    BACKSLASH,
    CARRIAGE_RETURN,
    DOUBLE_QUOTE,
    NEWLINE,
    TAB,
)


def escape_string(value: str) -> str:
    """Escape special characters in a string for encoding.

    Handles backslashes, quotes, newlines, carriage returns, and tabs.
    Per Section 7.1 of the TOON specification.

    Args:
        value: The string to escape

    Returns:
        The escaped string
    """
    return (
        value.replace(BACKSLASH, BACKSLASH + BACKSLASH)
        .replace(DOUBLE_QUOTE, BACKSLASH + DOUBLE_QUOTE)
        .replace(NEWLINE, BACKSLASH + "n")
        .replace(CARRIAGE_RETURN, BACKSLASH + "r")
        .replace(TAB, BACKSLASH + "t")
    )


def unescape_string(value: str) -> str:
    """Unescape a string by processing escape sequences.

    Handles `\\n`, `\\t`, `\\r`, `\\\\`, and `\\"` escape sequences.
    Per Section 7.1 of the TOON specification.

    Args:
        value: The string to unescape

    Returns:
        The unescaped string

    Raises:
        SyntaxError: If an invalid escape sequence is encountered
    """
    result = ""
    i = 0

    while i < len(value):
        if value[i] == BACKSLASH:
            if i + 1 >= len(value):
                raise SyntaxError("Invalid escape sequence: backslash at end of string")

            next_char = value[i + 1]
            if next_char == "n":
                result += NEWLINE
                i += 2
                continue
            if next_char == "t":
                result += TAB
                i += 2
                continue
            if next_char == "r":
                result += CARRIAGE_RETURN
                i += 2
                continue
            if next_char == BACKSLASH:
                result += BACKSLASH
                i += 2
                continue
            if next_char == DOUBLE_QUOTE:
                result += DOUBLE_QUOTE
                i += 2
                continue

            raise SyntaxError(f"Invalid escape sequence: \\{next_char}")

        result += value[i]
        i += 1

    return result


def find_closing_quote(content: str, start: int) -> int:
    """Find the index of the closing double quote, accounting for escape sequences.

    Args:
        content: The string to search in
        start: The index of the opening quote

    Returns:
        The index of the closing quote, or -1 if not found
    """
    i = start + 1
    while i < len(content):
        if content[i] == BACKSLASH and i + 1 < len(content):
            # Skip escaped character
            i += 2
            continue
        if content[i] == DOUBLE_QUOTE:
            return i
        i += 1
    return -1  # Not found


def find_unquoted_char(content: str, char: str, start: int = 0) -> int:
    """Find the index of a specific character outside of quoted sections.

    Args:
        content: The string to search in
        char: The character to look for
        start: Optional starting index (defaults to 0)

    Returns:
        The index of the character, or -1 if not found outside quotes
    """
    in_quotes = False
    i = start

    while i < len(content):
        if content[i] == BACKSLASH and i + 1 < len(content) and in_quotes:
            # Skip escaped character
            i += 2
            continue

        if content[i] == DOUBLE_QUOTE:
            in_quotes = not in_quotes
            i += 1
            continue

        if content[i] == char and not in_quotes:
            return i

        i += 1

    return -1
