"""Token counting for ``toon --stats`` and the deprecated ``toon_format`` helpers.

Counts use OpenAI's tokenizers through ``tiktoken`` (the ``tokens`` extra), so
they are exact for OpenAI models only. They run offline.
"""

from __future__ import annotations

import functools
import json
from typing import Any

from ._api import dumps

DEFAULT_ENCODING = "o200k_base"


@functools.cache
def _encoding(name: str) -> Any:
    try:
        import tiktoken
    except ImportError as exc:
        raise RuntimeError(
            'tiktoken is required for token counting: pip install "toon-format[tokens]"'
        ) from exc
    return tiktoken.get_encoding(name)


def count_tokens(text: str, encoding: str = DEFAULT_ENCODING) -> int:
    """Count the tokens of ``text`` with a tiktoken encoding."""
    return len(_encoding(encoding).encode(text))


def stats(data: Any, *, delimiter: str, indent_size: int) -> str:
    """Return a table comparing ``data`` as compact JSON, indented JSON, and TOON."""
    texts = {
        "JSON (compact)": json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        "JSON (indent 2)": json.dumps(data, ensure_ascii=False, indent=2),
        "TOON": dumps(data, delimiter=delimiter, indent_size=indent_size),
    }
    tokens = {name: count_tokens(text) for name, text in texts.items()}
    lines = [
        f"Tokens with tiktoken {DEFAULT_ENCODING} (exact for OpenAI models only)",
        f"{'Format':<16} {'Tokens':>9} {'Characters':>11} {'TOON vs':>8}",
    ]
    for name, text in texts.items():
        change = ""
        if name != "TOON" and tokens[name]:
            change = f"{(tokens['TOON'] - tokens[name]) / tokens[name]:+.1%}"
        row = f"{name:<16} {tokens[name]:>9,} {len(text):>11,} {change:>8}"
        lines.append(row.rstrip())
    return "\n".join(lines)
