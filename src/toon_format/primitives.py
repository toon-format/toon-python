# Copyright (c) 2025 TOON Format Organization
# SPDX-License-Identifier: MIT
"""Primitive value encoding utilities.

Handles encoding of primitive values (strings, numbers, booleans, null) and
array headers. Implements quoting rules, escape sequences, and header formatting
for inline and tabular array formats.
"""

import re
from typing import List, Literal, Optional, Union

from ._string_utils import escape_string
from ._validation import is_safe_unquoted, is_valid_unquoted_key
from .constants import (
    CLOSE_BRACE,
    CLOSE_BRACKET,
    COLON,
    COMMA,
    CONTROL_CHARS_REGEX,
    DOUBLE_QUOTE,
    FALSE_LITERAL,
    NULL_LITERAL,
    NUMERIC_REGEX,
    OCTAL_REGEX,
    OPEN_BRACE,
    OPEN_BRACKET,
    STRUCTURAL_CHARS_REGEX,
    TRUE_LITERAL,
    VALID_KEY_REGEX,
)
from .logging_config import get_logger
from .types import Delimiter, JsonPrimitive

# Precompiled patterns for performance
_STRUCTURAL_CHARS_PATTERN = re.compile(STRUCTURAL_CHARS_REGEX)
_CONTROL_CHARS_PATTERN = re.compile(CONTROL_CHARS_REGEX)
_NUMERIC_PATTERN = re.compile(NUMERIC_REGEX, re.IGNORECASE)
_OCTAL_PATTERN = re.compile(OCTAL_REGEX)
_VALID_KEY_PATTERN = re.compile(VALID_KEY_REGEX, re.IGNORECASE)


logger = get_logger(__name__)


def encode_primitive(value: JsonPrimitive, delimiter: str = COMMA) -> str:
    """Encode a primitive value.

    Args:
        value: Primitive value
        delimiter: Current delimiter being used

    Returns:
        Encoded string
    """
    if value is None:
        return NULL_LITERAL
    if isinstance(value, bool):
        return TRUE_LITERAL if value else FALSE_LITERAL
    if isinstance(value, (int, float)):
        # Format numbers in decimal form without scientific notation
        # Per spec Section 2: numbers must be rendered without exponent notation
        if isinstance(value, int):
            return str(value)
        # For floats, use Python's default conversion first
        formatted = str(value)
        # Check if Python used scientific notation
        if "e" in formatted or "E" in formatted:
            # Convert to fixed-point decimal notation
            # Use format with enough precision, then strip trailing zeros
            from decimal import Decimal

            # Convert through Decimal to get exact decimal representation
            dec = Decimal(str(value))
            formatted = format(dec, "f")
        return formatted
    if isinstance(value, str):
        return encode_string_literal(value, delimiter)
    return str(value)


# Note: escape_string and is_safe_unquoted are now imported from _string_utils and _validation


def encode_string_literal(value: str, delimiter: str = COMMA) -> str:
    """Encode a string, quoting only if necessary.

    Args:
        value: String value
        delimiter: Current delimiter being used

    Returns:
        Encoded string
    """
    if is_safe_unquoted(value, delimiter):
        return value
    return f"{DOUBLE_QUOTE}{escape_string(value)}{DOUBLE_QUOTE}"


def encode_key(key: str) -> str:
    """Encode an object key.

    Args:
        key: Key string

    Returns:
        Encoded key
    """
    # Keys matching /^[A-Z_][\w.]*$/i don't require quotes
    if is_valid_unquoted_key(key):
        return key
    return f"{DOUBLE_QUOTE}{escape_string(key)}{DOUBLE_QUOTE}"


def join_encoded_values(values: List[str], delimiter: Delimiter) -> str:
    """Join encoded primitive values with a delimiter.

    Args:
        values: List of encoded values
        delimiter: Delimiter to use

    Returns:
        Joined string
    """
    return delimiter.join(values)


def format_header(
    key: Optional[str],
    length: int,
    fields: Optional[List[str]],
    delimiter: Delimiter,
    length_marker: Union[str, Literal[False], None],
) -> str:
    """Format array/table header.

    Args:
        key: Optional key name
        length: Array length
        fields: Optional field names for tabular format
        delimiter: Delimiter character
        length_marker: Optional length marker prefix

    Returns:
        Formatted header string
    """
    # Build length marker
    marker_prefix = length_marker if length_marker else ""

    # Build fields if provided
    fields_str = ""
    if fields:
        # Encode each field name as a key (may need quoting per Section 7.3)
        encoded_fields = [encode_key(field) for field in fields]
        fields_str = f"{OPEN_BRACE}{delimiter.join(encoded_fields)}{CLOSE_BRACE}"

    # Build length string with delimiter when needed
    # Rules per TOON spec: delimiter is optional in bracket [N<delim?>]
    # - Only include delimiter if it's NOT comma (comma is the default)
    # - This applies to both tabular and primitive arrays
    if delimiter != COMMA:
        # Non-comma delimiter: show delimiter in bracket
        length_str = f"{OPEN_BRACKET}{marker_prefix}{length}{delimiter}{CLOSE_BRACKET}"
    else:
        # Comma delimiter (default): just [length]
        length_str = f"{OPEN_BRACKET}{marker_prefix}{length}{CLOSE_BRACKET}"

    # Combine parts
    if key:
        return f"{encode_key(key)}{length_str}{fields_str}{COLON}"
    return f"{length_str}{fields_str}{COLON}"
