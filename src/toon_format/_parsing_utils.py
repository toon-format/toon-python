# Copyright (c) 2025 TOON Format Organization
# SPDX-License-Identifier: MIT
"""Parsing utilities for quote-aware string processing.

This module provides utilities for parsing TOON strings while respecting
quoted sections and escape sequences. Used extensively in decoder for
finding delimiters and structural characters outside of quoted strings.
"""

from typing import Iterator, List, Tuple

from .constants import BACKSLASH, DOUBLE_QUOTE


def iter_unquoted(line: str, start: int = 0) -> Iterator[Tuple[int, str, bool]]:
    """Iterate over characters in a line, tracking quote state.

    This is the core utility for quote-aware string processing. It handles:
    - Tracking quote boundaries
    - Skipping escaped characters within quotes
    - Yielding (index, character, is_quoted) tuples

    Args:
        line: The line to iterate over
        start: Starting position (default: 0)

    Yields:
        Tuple of (index, char, is_quoted) for each character

    Examples:
        >>> list(iter_unquoted('a"b:c"d'))
        [(0, 'a', False), (1, '"', False), (2, 'b', True), (3, ':', True),
         (4, 'c', True), (5, '"', True), (6, 'd', False)]
    """
    in_quotes = False
    i = start

    while i < len(line):
        char = line[i]

        if char == DOUBLE_QUOTE:
            # Yield quote with current state, THEN toggle for next char
            yield (i, char, in_quotes)
            in_quotes = not in_quotes
        elif char == BACKSLASH and i + 1 < len(line) and in_quotes:
            # Escaped character - yield backslash, then skip and yield next char
            yield (i, char, True)
            i += 1
            if i < len(line):
                yield (i, line[i], True)
        else:
            yield (i, char, in_quotes)

        i += 1


def find_unquoted_char(line: str, target_char: str, start: int = 0) -> int:
    """Find first occurrence of target character outside of quoted strings.

    Args:
        line: Line to search
        target_char: Character to find
        start: Starting position (default: 0)

    Returns:
        Index of character, or -1 if not found

    Examples:
        >>> find_unquoted_char('a:b"c:d"e', ':')
        1
        >>> find_unquoted_char('a"b:c"d:e', ':', 0)
        7
        >>> find_unquoted_char('"a:b":c', ':', 0)
        5
    """
    for i, char, is_quoted in iter_unquoted(line, start):
        if char == target_char and not is_quoted:
            return i
    return -1


def parse_delimited_values(line: str, delimiter: str) -> List[str]:
    """Parse delimiter-separated values, respecting quotes and escapes.

    This function splits a line on the delimiter, but only at unquoted positions.
    Quotes and escape sequences within quoted sections are preserved.

    Args:
        line: Line content
        delimiter: Active delimiter (e.g., ',', '\\t', '|')

    Returns:
        List of token strings (with quotes and escapes preserved)

    Examples:
        >>> parse_delimited_values('a,b,c', ',')
        ['a', 'b', 'c']
        >>> parse_delimited_values('a,"b,c",d', ',')
        ['a', '"b,c"', 'd']
        >>> parse_delimited_values('"a,b",c', ',')
        ['"a,b"', 'c']
    """
    tokens: List[str] = []
    current: List[str] = []

    for i, char, is_quoted in iter_unquoted(line):
        if char == delimiter and not is_quoted:
            # Split on unquoted delimiter
            tokens.append("".join(current))
            current = []
        else:
            current.append(char)

    # Add final token (always add, even if empty, to handle trailing delimiters)
    if current or tokens:
        tokens.append("".join(current))

    return tokens


def split_at_unquoted_char(line: str, target_char: str) -> Tuple[str, str]:
    """Split a line at the first unquoted occurrence of target character.

    Args:
        line: Line content
        target_char: Character to split on

    Returns:
        Tuple of (before, after) strings

    Raises:
        ValueError: If target character not found outside quotes

    Examples:
        >>> split_at_unquoted_char('key: value', ':')
        ('key', ' value')
        >>> split_at_unquoted_char('"key:1": value', ':')
        ('"key:1"', ' value')
    """
    idx = find_unquoted_char(line, target_char)
    if idx == -1:
        raise ValueError(f"Character '{target_char}' not found outside quotes")
    return (line[:idx], line[idx + 1 :])


def find_first_unquoted(line: str, chars: List[str], start: int = 0) -> Tuple[int, str]:
    """Find the first occurrence of any character in chars, outside quotes.

    Args:
        line: Line to search
        chars: List of characters to search for
        start: Starting position (default: 0)

    Returns:
        Tuple of (index, character) for first match, or (-1, '') if none found

    Examples:
        >>> find_first_unquoted('a:b,c', [':', ','])
        (1, ':')
        >>> find_first_unquoted('a"b:c",d', [':', ','])
        (7, ',')
    """
    char_set = set(chars)
    for i, char, is_quoted in iter_unquoted(line, start):
        if char in char_set and not is_quoted:
            return (i, char)
    return (-1, "")
