"""Token counting helpers of the deprecated ``toon_format`` 0.9 API.

Requires ``tiktoken`` (``pip install "toon-format[tokens]"``).
"""

from __future__ import annotations

import functools
import json
from typing import Any

import toon

__all__ = ["compare_formats", "count_tokens", "estimate_savings"]


@functools.cache
def _encoding(name: str) -> Any:
    try:
        import tiktoken
    except ImportError as exc:
        raise RuntimeError(
            'tiktoken is required for token counting: pip install "toon-format[tokens]"'
        ) from exc
    return tiktoken.get_encoding(name)


def count_tokens(text: str, encoding: str = "o200k_base") -> int:
    """Count the tokens of ``text`` with a tiktoken encoding."""
    return len(_encoding(encoding).encode(text))


def estimate_savings(data: Any, encoding: str = "o200k_base") -> dict[str, Any]:
    """Compare the token counts of ``data`` as indented JSON and as TOON."""
    json_tokens = count_tokens(json.dumps(data, indent=2, ensure_ascii=False), encoding)
    toon_tokens = count_tokens(toon.dumps(data), encoding)
    savings = max(0, json_tokens - toon_tokens)
    return {
        "json_tokens": json_tokens,
        "toon_tokens": toon_tokens,
        "savings": savings,
        "savings_percent": savings / json_tokens * 100.0 if json_tokens else 0.0,
    }


def compare_formats(data: Any, encoding: str = "o200k_base") -> str:
    """Return a small table comparing JSON and TOON for ``data``."""
    metrics = estimate_savings(data, encoding)
    json_chars = len(json.dumps(data, indent=2, ensure_ascii=False))
    toon_chars = len(toon.dumps(data))
    separator = "─" * 48
    return "\n".join(
        [
            "Format Comparison",
            separator,
            "Format      Tokens    Size (chars)",
            f"JSON      {metrics['json_tokens']:>7,}    {json_chars:>11,}",
            f"TOON      {metrics['toon_tokens']:>7,}    {toon_chars:>11,}",
            separator,
            f"Savings: {metrics['savings']:,} tokens "
            f"({metrics['savings_percent']:.1f}%)",
        ]
    )
