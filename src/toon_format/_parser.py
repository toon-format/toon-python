"""Parser for TOON syntax elements (headers, tokens, keys, delimited values)."""

from dataclasses import dataclass

from toon_format._constants import (
    CLOSE_BRACE,
    CLOSE_BRACKET,
    COLON,
    DEFAULT_DELIMITER,
    DELIMITERS,
    DOUBLE_QUOTE,
    OPEN_BRACE,
    OPEN_BRACKET,
)
from toon_format._literal_utils import is_boolean_or_null_literal, is_numeric_literal
from toon_format._string_utils import (
    find_closing_quote,
    find_unquoted_char,
    unescape_string,
)
from toon_format.types import JsonPrimitive


@dataclass
class ArrayHeaderInfo:
    """Information about an array header."""

    key: str | None
    length: int
    delimiter: str
    fields: list[str] | None
    has_length_marker: bool


def parse_array_header_line(
    content: str, default_delimiter: str = DEFAULT_DELIMITER
) -> tuple[ArrayHeaderInfo, str | None] | None:
    """Parse an array header line.

    Parses syntax like `key[N<delim?>]{fields}?:`

    Args:
        content: The line content to parse
        default_delimiter: The default delimiter to use if not specified in header

    Returns:
        A tuple of (ArrayHeaderInfo, inline_values) if header is found, None otherwise
    """
    trimmed = content.lstrip()

    # Find the bracket segment, accounting for quoted keys that may contain brackets
    bracket_start = -1

    # For quoted keys, find bracket after closing quote (not inside the quoted string)
    if trimmed.startswith(DOUBLE_QUOTE):
        closing_quote_index = find_closing_quote(trimmed, 0)
        if closing_quote_index == -1:
            return None

        after_quote = trimmed[closing_quote_index + 1 :]
        if not after_quote.startswith(OPEN_BRACKET):
            return None

        # Calculate position in original content and find bracket after the quoted key
        leading_whitespace = len(content) - len(trimmed)
        key_end_index = leading_whitespace + closing_quote_index + 1
        bracket_start = content.find(OPEN_BRACKET, key_end_index)
    else:
        # Unquoted key - find first bracket
        bracket_start = content.find(OPEN_BRACKET)

    if bracket_start == -1:
        return None

    bracket_end = content.find(CLOSE_BRACKET, bracket_start)
    if bracket_end == -1:
        return None

    # Find the colon that comes after all brackets and braces
    colon_index = bracket_end + 1
    brace_end = colon_index

    # Check for fields segment (braces come after bracket)
    brace_start = content.find(OPEN_BRACE, bracket_end)
    if brace_start != -1 and brace_start < content.find(COLON, bracket_end):
        found_brace_end = content.find(CLOSE_BRACE, brace_start)
        if found_brace_end != -1:
            brace_end = found_brace_end + 1

    # Now find colon after brackets and braces
    colon_index = content.find(COLON, max(bracket_end, brace_end))
    if colon_index == -1:
        return None

    # Extract and parse the key (might be quoted)
    key: str | None = None
    if bracket_start > 0:
        raw_key = content[:bracket_start].strip()
        if raw_key.startswith(DOUBLE_QUOTE):
            try:
                key = parse_string_literal(raw_key)
            except SyntaxError:
                return None
        else:
            key = raw_key

    after_colon = content[colon_index + 1 :].strip()

    bracket_content = content[bracket_start + 1 : bracket_end]

    # Try to parse bracket segment
    try:
        parsed_bracket = parse_bracket_segment(bracket_content, default_delimiter)
    except (TypeError, ValueError):
        return None

    length_val = parsed_bracket["length"]
    delimiter_val = parsed_bracket["delimiter"]
    has_length_marker_val = parsed_bracket["has_length_marker"]

    # Type narrowing
    if not isinstance(length_val, int):
        return None
    if not isinstance(delimiter_val, str):
        return None
    if not isinstance(has_length_marker_val, bool):
        return None

    length: int = length_val
    delimiter: str = delimiter_val
    has_length_marker: bool = has_length_marker_val

    # Check for fields segment
    fields: list[str] | None = None
    if brace_start != -1 and brace_start < colon_index:
        found_brace_end = content.find(CLOSE_BRACE, brace_start)
        if found_brace_end != -1 and found_brace_end < colon_index:
            fields_content = content[brace_start + 1 : found_brace_end]
            field_tokens = parse_delimited_values(fields_content, delimiter)
            fields = [parse_string_literal(field.strip()) for field in field_tokens]

    return (
        ArrayHeaderInfo(
            key=key,
            length=length,
            delimiter=delimiter,
            fields=fields,
            has_length_marker=has_length_marker,
        ),
        after_colon or None,
    )


def parse_bracket_segment(
    seg: str, default_delimiter: str = DEFAULT_DELIMITER
) -> dict[str, int | str | bool]:
    """Parse a bracket segment `[#?N<delim?>]`.

    Args:
        seg: The bracket content (without brackets)
        default_delimiter: The default delimiter to use if not specified

    Returns:
        A dict with 'length', 'delimiter', and 'has_length_marker' keys

    Raises:
        TypeError: If the length cannot be parsed
        ValueError: If the length is invalid
    """
    has_length_marker = False
    content = seg

    # Check for length marker
    if content.startswith("#"):
        has_length_marker = True
        content = content[1:]

    # Check for delimiter suffix
    delimiter = default_delimiter
    if content.endswith(DELIMITERS["tab"]):
        delimiter = DELIMITERS["tab"]
        content = content[:-1]
    elif content.endswith(DELIMITERS["pipe"]):
        delimiter = DELIMITERS["pipe"]
        content = content[:-1]

    try:
        length = int(content)
        if length < 0:
            raise ValueError(f"Invalid array length: {seg}")
    except ValueError as e:
        raise TypeError(f"Invalid array length: {seg}") from e

    return {
        "length": length,
        "delimiter": delimiter,
        "has_length_marker": has_length_marker,
    }


def parse_delimited_values(input_str: str, delimiter: str) -> list[str]:
    """Parse delimited values, respecting quoted sections.

    Splits on delimiter only when not in quotes.

    Args:
        input_str: The input string to parse
        delimiter: The delimiter to split on

    Returns:
        A list of value strings
    """
    values: list[str] = []
    current = ""
    in_quotes = False
    i = 0

    while i < len(input_str):
        char = input_str[i]

        if char == "\\" and i + 1 < len(input_str) and in_quotes:
            # Escape sequence in quoted string
            current += char + input_str[i + 1]
            i += 2
            continue

        if char == DOUBLE_QUOTE:
            in_quotes = not in_quotes
            current += char
            i += 1
            continue

        if char == delimiter and not in_quotes:
            values.append(current.strip())
            current = ""
            i += 1
            continue

        current += char
        i += 1

    # Add last value
    if current or values:
        values.append(current.strip())

    return values


def map_row_values_to_primitives(values: list[str]) -> list[JsonPrimitive]:
    """Map row value strings to typed primitives.

    Args:
        values: List of string tokens

    Returns:
        List of typed primitives
    """
    return [parse_primitive_token(v) for v in values]


def parse_primitive_token(token: str) -> JsonPrimitive:
    """Parse a primitive token to a typed value.

    Args:
        token: The token string to parse

    Returns:
        The parsed primitive value
    """
    trimmed = token.strip()

    # Empty token
    if not trimmed:
        return ""

    # Quoted string (if starts with quote, it MUST be properly quoted)
    if trimmed.startswith(DOUBLE_QUOTE):
        return parse_string_literal(trimmed)

    # Boolean or null literals
    if is_boolean_or_null_literal(trimmed):
        if trimmed == "true":
            return True
        if trimmed == "false":
            return False
        if trimmed == "null":
            return None

    # Numeric literal
    if is_numeric_literal(trimmed):
        if "e" in trimmed.lower():
            return float(trimmed)
        if "." in trimmed:
            return float(trimmed)
        return int(trimmed)

    # Unquoted string
    return trimmed


def parse_string_literal(token: str) -> str:
    """Parse a string literal, unescaping as needed.

    Args:
        token: The token (may be quoted)

    Returns:
        The unescaped string

    Raises:
        SyntaxError: If the string is malformed
    """
    trimmed = token.strip()

    if trimmed.startswith(DOUBLE_QUOTE):
        # Find the closing quote, accounting for escaped quotes
        closing_quote_index = find_closing_quote(trimmed, 0)

        if closing_quote_index == -1:
            # No closing quote was found
            raise SyntaxError("Unterminated string: missing closing quote")

        if closing_quote_index != len(trimmed) - 1:
            raise SyntaxError("Unexpected characters after closing quote")

        content = trimmed[1:closing_quote_index]
        return unescape_string(content)

    return trimmed


def parse_unquoted_key(content: str, start: int) -> tuple[str, int]:
    """Parse an unquoted key until colon.

    Args:
        content: The content to parse
        start: The start index

    Returns:
        A tuple of (key, end_index)

    Raises:
        SyntaxError: If no colon is found after the key
    """
    end = start
    while end < len(content) and content[end] != COLON:
        end += 1

    # Validate that a colon was found
    if end >= len(content) or content[end] != COLON:
        raise SyntaxError("Missing colon after key")

    key = content[start:end].strip()

    # Skip the colon
    end += 1

    return key, end


def parse_quoted_key(content: str, start: int) -> tuple[str, int]:
    """Parse a quoted key.

    Args:
        content: The content to parse
        start: The start index (should be at opening quote)

    Returns:
        A tuple of (key, end_index)

    Raises:
        SyntaxError: If the key is malformed or colon is missing
    """
    # Find the closing quote, accounting for escaped quotes
    closing_quote_index = find_closing_quote(content, start)

    if closing_quote_index == -1:
        raise SyntaxError("Unterminated quoted key")

    # Extract and unescape the key content
    key_content = content[start + 1 : closing_quote_index]
    key = unescape_string(key_content)
    end = closing_quote_index + 1

    # Validate and skip colon after quoted key
    if end >= len(content) or content[end] != COLON:
        raise SyntaxError("Missing colon after key")
    end += 1

    return key, end


def parse_key_token(content: str, start: int) -> tuple[str, int]:
    """Parse a key token (quoted or unquoted).

    Args:
        content: The content to parse
        start: The start index

    Returns:
        A tuple of (key, end_index)

    Raises:
        SyntaxError: If the key is malformed
    """
    if content[start] == DOUBLE_QUOTE:
        return parse_quoted_key(content, start)
    else:
        return parse_unquoted_key(content, start)


def is_array_header_after_hyphen(content: str) -> bool:
    """Check if content starts with an array header after hyphen removal.

    Args:
        content: The content to check

    Returns:
        True if content starts with an array header
    """
    trimmed = content.strip()
    return trimmed.startswith(OPEN_BRACKET) and find_unquoted_char(trimmed, COLON) != -1


def is_object_first_field_after_hyphen(content: str) -> bool:
    """Check if content has key-value syntax (object first field).

    Args:
        content: The content to check

    Returns:
        True if content has a colon (key-value syntax)
    """
    return find_unquoted_char(content, COLON) != -1
