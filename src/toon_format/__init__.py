# Copyright (c) 2025 TOON Format Organization
# SPDX-License-Identifier: MIT
"""TOON Format for Python.

Token-Oriented Object Notation (TOON) is a compact, human-readable serialization
format optimized for LLM contexts. Achieves 30-60% token reduction vs JSON while
maintaining readability and structure.

This package provides encoding and decoding functionality with 100% compatibility
with the official TOON specification (v1.3).

Example:
    >>> from toon_format import encode, decode
    >>> data = {"name": "Alice", "age": 30}
    >>> toon = encode(data)
    >>> print(toon)
    name: Alice
    age: 30
    >>> decode(toon)
    {'name': 'Alice', 'age': 30}
"""

from .decoder import ToonDecodeError, decode
from .encoder import encode
from .types import DecodeOptions, Delimiter, DelimiterKey, EncodeOptions
from .utils import compare_formats, count_tokens, estimate_savings

__version__ = "0.9.0-beta.1"
__all__ = [
    "encode",
    "decode",
    "ToonDecodeError",
    "Delimiter",
    "DelimiterKey",
    "EncodeOptions",
    "DecodeOptions",
    "count_tokens",
    "estimate_savings",
    "compare_formats",
]
