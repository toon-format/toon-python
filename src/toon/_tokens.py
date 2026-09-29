"""Token counting for ``toon stats`` and the deprecated ``toon_format`` helpers.

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
            'tiktoken is required for token counting: pip install "toon-python[tokens]"'
        ) from exc
    return tiktoken.get_encoding(name)


def count_tokens(text: str, encoding: str = DEFAULT_ENCODING) -> int:
    """Count the tokens of ``text`` with a tiktoken encoding."""
    return len(_encoding(encoding).encode(text))


def stats(data: Any) -> str:
    """Return a table of the tokens of ``data`` as JSON and as TOON.

    TOON is written with each delimiter (§11); every row is compared with
    compact JSON, the smallest JSON a prompt can hold.
    """
    texts = {
        "JSON (compact)": json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        "JSON (indent 2)": json.dumps(data, ensure_ascii=False, indent=2),
        "TOON (comma)": dumps(data),
        "TOON (tab)": dumps(data, delimiter="\t"),
        "TOON (pipe)": dumps(data, delimiter="|"),
    }
    tokens = {name: count_tokens(text) for name, text in texts.items()}
    baseline = tokens["JSON (compact)"]
    lines = [
        f"Tokens with tiktoken {DEFAULT_ENCODING} (exact for OpenAI models only)",
        f"{'Format':<16} {'Tokens':>9} {'Characters':>11} {'vs compact JSON':>16}",
    ]
    for name, text in texts.items():
        change = ""
        if name != "JSON (compact)" and baseline:
            change = f"{(tokens[name] - baseline) / baseline:+.1%}"
        row = f"{name:<16} {tokens[name]:>9,} {len(text):>11,} {change:>16}"
        lines.append(row.rstrip())
    return "\n".join(lines)
