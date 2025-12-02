# Copyright (c) 2025 TOON Format Organization
# SPDX-License-Identifier: MIT
"""Utilities for detecting literal token types.

This module provides functions to identify different types of literal
values in TOON syntax, such as booleans, null, and numeric literals.
Used during decoding to distinguish between literal values and strings.
"""

from .constants import FALSE_LITERAL, NULL_LITERAL, TRUE_LITERAL


def is_boolean_or_null_literal(token: str) -> bool:
    """Check if a token is a boolean or null literal (`true`, `false`, `null`).

    Args:
        token: The token to check

    Returns:
        True if the token is a boolean or null literal

    Examples:
        >>> is_boolean_or_null_literal("true")
        True
        >>> is_boolean_or_null_literal("null")
        True
        >>> is_boolean_or_null_literal("hello")
        False
    """
    return token == TRUE_LITERAL or token == FALSE_LITERAL or token == NULL_LITERAL


def is_numeric_literal(token: str) -> bool:
    """Check if a token represents a valid numeric literal.

    Rejects numbers with leading zeros (except `"0"` itself or decimals like `"0.5"`).
    Per Section 7.3 of the TOON specification.

    Args:
        token: The token to check

    Returns:
        True if the token is a valid numeric literal

    Examples:
        >>> is_numeric_literal("42")
        True
        >>> is_numeric_literal("3.14")
        True
        >>> is_numeric_literal("0.5")
        True
        >>> is_numeric_literal("0123")  # Leading zero - not valid
        False
        >>> is_numeric_literal("-01")  # Negative with leading zero - not valid
        False
        >>> is_numeric_literal("hello")
        False
    """
    if not token:
        return False

    # Handle negative numbers
    start_idx = 1 if token.startswith("-") else 0
    if start_idx >= len(token):
        return False

    # Must not have leading zeros (except for `"0"` itself or decimals like `"0.5"`)
    # Check the first digit after optional minus sign
    if len(token) > start_idx + 1 and token[start_idx] == "0" and token[start_idx + 1] != ".":
        return False

    # Check if it's a valid number
    try:
        num = float(token)
        # Reject NaN and infinity
        return not (num != num or not (-float("inf") < num < float("inf")))
    except ValueError:
        return False
