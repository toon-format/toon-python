"""Primitive encoding utilities for TOON format."""

from toon_format._constants import COMMA, DEFAULT_DELIMITER, DOUBLE_QUOTE, NULL_LITERAL
from toon_format._string_utils import escape_string
from toon_format._validation import is_safe_unquoted, is_valid_unquoted_key
from toon_format.types import JsonPrimitive


def encode_primitive(value: JsonPrimitive, delimiter: str = COMMA) -> str:
    """Encode a primitive value to a TOON string.

    Args:
        value: The primitive value to encode
        delimiter: The active delimiter for quoting decisions

    Returns:
        The encoded string representation
    """
    if value is None:
        return NULL_LITERAL

    if isinstance(value, bool):
        return str(value).lower()

    if isinstance(value, (int, float)):
        if isinstance(value, float):
            formatted = f"{value:.15g}".replace("e+", "e").replace("E+", "E")
            if "e" in formatted.lower():
                return f"{value:.15f}".rstrip("0").rstrip(".")
            return formatted.rstrip("0").rstrip(".") if "." in formatted else formatted
        return str(value)

    return encode_string_literal(value, delimiter)


def encode_string_literal(value: str, delimiter: str = COMMA) -> str:
    """Encode a string literal with appropriate quoting.

    Args:
        value: The string to encode
        delimiter: The active delimiter for quoting decisions

    Returns:
        The encoded string (quoted if needed)
    """
    if is_safe_unquoted(value, delimiter):
        return value

    return f"{DOUBLE_QUOTE}{escape_string(value)}{DOUBLE_QUOTE}"


def encode_key(key: str) -> str:
    """Encode a key with appropriate quoting.

    Args:
        key: The key to encode

    Returns:
        The encoded key (quoted if needed)
    """
    if is_valid_unquoted_key(key):
        return key

    return f"{DOUBLE_QUOTE}{escape_string(key)}{DOUBLE_QUOTE}"


def encode_and_join_primitives(
    values: list[JsonPrimitive],
    delimiter: str = COMMA,
) -> str:
    """Encode a list of primitives and join with delimiter.

    Args:
        values: List of primitive values
        delimiter: The delimiter to use for joining

    Returns:
        The joined encoded string
    """
    return delimiter.join(encode_primitive(v, delimiter) for v in values)


def format_header(
    length: int,
    key: str | None = None,
    fields: list[str] | None = None,
    delimiter: str = COMMA,
    length_marker: str | bool = False,
) -> str:
    """Format an array header.

    Formats syntax like `key[N<delim?>]{fields}?:`

    Args:
        length: The array length
        key: Optional key name
        fields: Optional field names for tabular arrays
        delimiter: The delimiter (comma if not tab/pipe, tab/pipe if specified)
        length_marker: Optional length marker ('#' or False)

    Returns:
        The formatted header string
    """
    header = ""

    if key:
        header += encode_key(key)

    # Only include delimiter if it's not the default (comma)
    marker_str = str(length_marker) if length_marker else ""
    if delimiter != DEFAULT_DELIMITER:
        header += f"[{marker_str}{length}{delimiter}]"
    else:
        header += f"[{marker_str}{length}]"

    if fields:
        quoted_fields = [encode_key(f) for f in fields]
        header += f"{{{delimiter.join(quoted_fields)}}}"

    header += ":"

    return header


def encode_inline_array_line(
    values: list[JsonPrimitive],
    delimiter: str,
    prefix: str | None = None,
    length_marker: str | bool = False,
) -> str:
    """Format an inline array line.

    Args:
        values: List of primitive values
        delimiter: The delimiter
        prefix: Optional key prefix
        length_marker: Optional length marker

    Returns:
        The formatted line string
    """
    header = format_header(
        len(values),
        key=prefix,
        delimiter=delimiter,
        length_marker=length_marker,
    )
    joined_value = encode_and_join_primitives(values, delimiter)
    if len(values) == 0:
        return header
    return f"{header} {joined_value}"
