"""Token counting helpers of the deprecated ``toon_format`` 0.9 API.

Requires ``tiktoken`` (``pip install "toon-format[tokens]"``).
"""

from __future__ import annotations

import json
from typing import Any

import toon
from toon._tokens import count_tokens

__all__ = ["compare_formats", "count_tokens", "estimate_savings"]


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
