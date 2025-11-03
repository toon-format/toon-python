"""Utilities for detecting literal token types."""

from toon_format._constants import FALSE_LITERAL, NULL_LITERAL, TRUE_LITERAL


def is_boolean_or_null_literal(token: str) -> bool:
    """Check if a token is a boolean or null literal (`true`, `false`, `null`).

    Args:
        token: The token to check

    Returns:
        True if the token is a boolean or null literal
    """
    return token == TRUE_LITERAL or token == FALSE_LITERAL or token == NULL_LITERAL


def is_numeric_literal(token: str) -> bool:
    """Check if a token represents a valid numeric literal.

    Rejects numbers with leading zeros (except `"0"` itself or decimals like `"0.5"`).

    Args:
        token: The token to check

    Returns:
        True if the token is a valid numeric literal
    """
    if not token:
        return False

    # Must not have leading zeros (except for `"0"` itself or decimals like `"0.5"`)
    if len(token) > 1 and token[0] == "0" and token[1] != ".":
        return False

    # Check if it's a valid number
    try:
        num = float(token)
        return not (num != num or not (-float("inf") < num < float("inf")))
    except ValueError:
        return False
