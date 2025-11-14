# Copyright (c) 2025 TOON Format Organization
# SPDX-License-Identifier: MIT
"""Token analysis utilities for TOON format.

This module provides utilities for counting tokens and comparing
token efficiency between JSON and TOON formats. Useful for:
- Estimating API costs (tokens are the primary cost driver)
- Optimizing prompt sizes for LLM context windows
- Benchmarking TOON's token efficiency

Functions:
    count_tokens: Count tokens in a text string
    estimate_savings: Compare JSON vs TOON token counts
    compare_formats: Generate formatted comparison table

Requirements:
    tiktoken: Install with `uv add tiktoken` or `uv add toon_format[benchmark]`

Example:
    >>> import toon_format
    >>> data = {"name": "Alice", "age": 30}
    >>> result = toon_format.estimate_savings(data)
    >>> print(f"TOON saves {result['savings_percent']:.1f}% tokens")
"""

import functools
import json
from typing import Any, Dict

# Import encode from parent package (defined in __init__.py before this module is imported)
# __init__.py defines encode() before importing utils, so this is safe
from . import encode

__all__ = ["count_tokens", "estimate_savings", "compare_formats"]


_TIKTOKEN_MISSING_MSG = (
    "tiktoken is required for token counting. "
    "Install with: uv add tiktoken or uv add toon_format[benchmark]"
)


def _require_tiktoken():
    try:
        import tiktoken  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - exercised via count_tokens
        raise RuntimeError(_TIKTOKEN_MISSING_MSG) from exc
    return tiktoken


@functools.lru_cache(maxsize=1)
def _get_tokenizer():
    """Get cached tiktoken tokenizer for o200k_base encoding.

    Returns:
        tiktoken.Encoding: The o200k_base tokenizer (gpt5/gpt5-mini).

    Raises:
        RuntimeError: If tiktoken is not installed.
    """
    tiktoken = _require_tiktoken()
    return tiktoken.get_encoding("o200k_base")


def count_tokens(text: str, encoding: str = "o200k_base") -> int:
    """Count tokens in a text string using tiktoken.

    Args:
        text: The string to tokenize.
        encoding: Tokenizer encoding name (default: 'o200k_base' for gpt5/gpt5-mini).
                  Other options include 'cl100k_base' (GPT-3.5), 'p50k_base' (older models).

    Returns:
        int: The number of tokens in the text.

    Example:
        >>> import toon_format
        >>> text = "Hello, world!"
        >>> toon_format.count_tokens(text)
        4

    Note:
        Requires tiktoken to be installed: uv add tiktoken or uv add toon_format[benchmark]
    """
    if encoding == "o200k_base":
        enc = _get_tokenizer()
    else:
        tiktoken = _require_tiktoken()
        enc = tiktoken.get_encoding(encoding)

    return len(enc.encode(text))


def estimate_savings(data: Any, encoding: str = "o200k_base") -> Dict[str, Any]:
    """Compare token counts between JSON and TOON formats.

    Args:
        data: Python dict or list to compare.
        encoding: Tokenizer encoding name (default: 'o200k_base').

    Returns:
        dict: Dictionary containing:
            - json_tokens (int): Token count for JSON format
            - toon_tokens (int): Token count for TOON format
            - savings (int): Absolute token savings (json_tokens - toon_tokens)
            - savings_percent (float): Percentage savings

    Example:
        >>> import toon_format
        >>> data = {"employees": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}
        >>> result = toon_format.estimate_savings(data)
        >>> print(f"Savings: {result['savings_percent']:.1f}%")
        Savings: 42.3%

    Note:
        Significant savings are typically achieved with structured data,
        especially arrays of uniform objects (tabular data).
    """
    # Encode as JSON
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    json_tokens = count_tokens(json_str, encoding)

    # Encode as TOON
    toon_str = encode(data)
    toon_tokens = count_tokens(toon_str, encoding)

    # Calculate savings
    savings = max(0, json_tokens - toon_tokens)
    savings_percent = (savings / json_tokens * 100.0) if json_tokens > 0 else 0.0

    return {
        "json_tokens": json_tokens,
        "toon_tokens": toon_tokens,
        "savings": savings,
        "savings_percent": savings_percent,
    }


def compare_formats(data: Any, encoding: str = "o200k_base") -> str:
    """Generate a formatted comparison table showing JSON vs TOON metrics.

    Args:
        data: Python dict or list to compare.
        encoding: Tokenizer encoding name (default: 'o200k_base').

    Returns:
        str: Formatted table as multi-line string showing token counts,
             character sizes, and savings percentage.

    Example:
        >>> import toon_format
        >>> data = {"users": [{"id": 1, "name": "Alice"}]}
        >>> print(toon_format.compare_formats(data))
        Format Comparison
        ────────────────────────────────────────────────
        Format      Tokens    Size (chars)
        JSON         1,234         5,678
        TOON           789         3,456
        ────────────────────────────────────────────────
        Savings: 445 tokens (36.1%)

    Note:
        This is useful for quick visual comparison during development.
    """
    # Get token metrics
    metrics = estimate_savings(data, encoding)

    # Encode both formats to get character counts
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    toon_str = encode(data)

    json_chars = len(json_str)
    toon_chars = len(toon_str)

    # Build formatted table
    separator = "─" * 48
    lines = [
        "Format Comparison",
        separator,
        "Format      Tokens    Size (chars)",
        f"JSON      {metrics['json_tokens']:>7,}    {json_chars:>11,}",
        f"TOON      {metrics['toon_tokens']:>7,}    {toon_chars:>11,}",
        separator,
        f"Savings: {metrics['savings']:,} tokens ({metrics['savings_percent']:.1f}%)",
    ]

    return "\n".join(lines)
