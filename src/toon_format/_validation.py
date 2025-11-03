"""Validation utilities for TOON encoding."""

from toon_format._constants import COMMA, LIST_ITEM_MARKER
from toon_format._literal_utils import is_boolean_or_null_literal


def is_valid_unquoted_key(key: str) -> bool:
    """Check if a key can be used without quotes.

    Valid unquoted keys must start with a letter or underscore,
    followed by letters, digits, underscores, or dots.

    Args:
        key: The key to validate

    Returns:
        True if the key can be used without quotes
    """
    if not key:
        return False
    import re

    return bool(re.match(r"^[A-Z_][\w.]*$", key, re.IGNORECASE))


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

    Args:
        value: The string value to check
        delimiter: The active delimiter (default: comma)

    Returns:
        True if the string can be safely encoded without quotes
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
    import re

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

    Args:
        value: The string to check

    Returns:
        True if the string looks like a number
    """
    import re

    return bool(
        re.match(r"^-?\d+(?:\.\d+)?(?:e[+-]?\d+)?$", value, re.IGNORECASE)
        or re.match(r"^0\d+$", value)
    )
