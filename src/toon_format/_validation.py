# Copyright (c) 2025 TOON Format Organization
# SPDX-License-Identifier: MIT
"""Validation utilities for TOON encoding.

This module provides validation functions to determine whether strings,
keys, and values can be safely encoded without quotes or need quoting
according to TOON specification rules.
"""

import re

from ._literal_utils import is_boolean_or_null_literal
from .constants import (
    COMMA,
    LIST_ITEM_MARKER,
    NUMERIC_REGEX,
    OCTAL_REGEX,
    VALID_KEY_REGEX,
)


def is_valid_unquoted_key(key: str) -> bool:
    """Check if a key can be used without quotes.

    Valid unquoted keys must start with a letter or underscore,
    followed by letters, digits, underscores, or dots.
    Per Section 8.2 of the TOON specification.

    Args:
        key: The key to validate

    Returns:
        True if the key can be used without quotes

    Examples:
        >>> is_valid_unquoted_key("name")
        True
        >>> is_valid_unquoted_key("user_id")
        True
        >>> is_valid_unquoted_key("config.value")
        True
        >>> is_valid_unquoted_key("123")  # Starts with digit
        False
        >>> is_valid_unquoted_key("my-key")  # Contains hyphen
        False
    """
    if not key:
        return False
    return bool(re.match(VALID_KEY_REGEX, key, re.IGNORECASE))


def is_safe_unquoted(value: str, delimiter: str = COMMA) -> bool:
    """Determine if a string value can be safely encoded without quotes.

    A string needs quoting if it:
    - Is empty
    - Has leading or trailing whitespace
    - Could be confused with a literal (boolean, null, number)
    - Contains structural characters (colons, brackets, braces)
    - Contains quotes or backslashes (need escaping)
    - Contains control characters (newlines, tabs, etc.)
    - Contains the active delimiter
    - Starts with a list marker (hyphen)

    Per Section 7.2 of the TOON specification.

    Args:
        value: The string value to check
        delimiter: The active delimiter (default: comma)

    Returns:
        True if the string can be safely encoded without quotes

    Examples:
        >>> is_safe_unquoted("hello")
        True
        >>> is_safe_unquoted("")  # Empty
        False
        >>> is_safe_unquoted("true")  # Reserved literal
        False
        >>> is_safe_unquoted("123")  # Looks like number
        False
        >>> is_safe_unquoted("hello world")  # Has whitespace (but not leading/trailing)
        True
    """
    if not value:
        return False

    if value != value.strip():
        return False

    # Check if it looks like any literal value (boolean, null, or numeric)
    if is_boolean_or_null_literal(value) or is_numeric_like(value):
        return False

    # Check for colon (always structural)
    if ":" in value:
        return False

    # Check for quotes and backslash (always need escaping)
    if '"' in value or "\\" in value:
        return False

    # Check for brackets and braces (always structural)
    if re.search(r"[\[\]{}]", value):
        return False

    # Check for control characters (newline, carriage return, tab)
    if re.search(r"[\n\r\t]", value):
        return False

    # Check for the active delimiter
    if delimiter in value:
        return False

    # Check for hyphen at start (list marker)
    if value.startswith(LIST_ITEM_MARKER):
        return False

    return True


def is_numeric_like(value: str) -> bool:
    """Check if a string looks like a number.

    Match numbers like `42`, `-3.14`, `1e-6`, `05`, etc.
    Includes octal-like numbers (leading zero) which must be quoted.

    Args:
        value: The string to check

    Returns:
        True if the string looks like a number

    Examples:
        >>> is_numeric_like("42")
        True
        >>> is_numeric_like("-3.14")
        True
        >>> is_numeric_like("1e-6")
        True
        >>> is_numeric_like("0123")  # Octal-like
        True
        >>> is_numeric_like("hello")
        False
    """
    return bool(
        re.match(NUMERIC_REGEX, value, re.IGNORECASE)
        or re.match(OCTAL_REGEX, value)  # Octal pattern
    )
