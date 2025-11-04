"""Shared pytest fixtures for TOON format tests.

This module provides reusable test data and fixtures following pytest best practices.
"""

import pytest
from typing import Any, Dict, List


# Simple test data fixtures
@pytest.fixture
def simple_object() -> Dict[str, Any]:
    """A simple object for basic encoding/decoding tests."""
    return {"id": 123, "name": "Alice", "active": True}


@pytest.fixture
def nested_object() -> Dict[str, Any]:
    """A nested object structure for testing deep nesting."""
    return {
        "user": {
            "id": 123,
            "profile": {"name": "Alice", "city": "NYC"},
        }
    }


@pytest.fixture
def tabular_array() -> List[Dict[str, Any]]:
    """Array of uniform objects suitable for tabular format."""
    return [
        {"id": 1, "name": "Alice", "age": 30},
        {"id": 2, "name": "Bob", "age": 25},
        {"id": 3, "name": "Charlie", "age": 35},
    ]


@pytest.fixture
def primitive_array() -> List[Any]:
    """Array of primitive values for inline format."""
    return [1, 2, 3, 4, 5]


@pytest.fixture
def mixed_array() -> List[Any]:
    """Array with mixed types requiring list format."""
    return [
        {"name": "Alice"},
        42,
        "hello",
        True,
    ]


# Parametrized delimiter fixture
@pytest.fixture(params=[",", "\t", "|"])
def delimiter(request) -> str:
    """Parametrized fixture providing all three supported delimiters.

    Returns comma, tab, or pipe delimiter.
    """
    return request.param


# Edge case values
@pytest.fixture
def edge_case_values() -> Dict[str, Any]:
    """Collection of edge case values for testing normalization."""
    return {
        "infinity": float("inf"),
        "negative_infinity": float("-inf"),
        "nan": float("nan"),
        "negative_zero": -0.0,
        "large_int": 9007199254740992,  # 2^53
        "none": None,
    }


# Python-specific types
@pytest.fixture
def python_types() -> Dict[str, Any]:
    """Python-specific types that need normalization."""
    from decimal import Decimal

    return {
        "tuple": (1, 2, 3),
        "set": {3, 1, 2},
        "frozenset": frozenset([3, 1, 2]),
        "decimal": Decimal("3.14"),
    }


# Options fixtures
@pytest.fixture
def encode_options_comma() -> Dict[str, Any]:
    """Encode options with comma delimiter."""
    return {"delimiter": ",", "indent": 2}


@pytest.fixture
def encode_options_tab() -> Dict[str, Any]:
    """Encode options with tab delimiter."""
    return {"delimiter": "\t", "indent": 2}


@pytest.fixture
def encode_options_pipe() -> Dict[str, Any]:
    """Encode options with pipe delimiter."""
    return {"delimiter": "|", "indent": 2}


@pytest.fixture
def decode_options_strict() -> Dict[str, bool]:
    """Decode options with strict mode enabled."""
    return {"strict": True}


@pytest.fixture
def decode_options_lenient() -> Dict[str, bool]:
    """Decode options with strict mode disabled."""
    return {"strict": False}
