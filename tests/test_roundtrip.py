"""Property: decoding an encoded value gives the value back (§2)."""

from __future__ import annotations

from typing import Any

from hypothesis import given
from hypothesis import strategies as st

import toon_format

from .strategies import documents


@given(
    documents,
    st.sampled_from(list(toon_format.Delimiter)),
    st.integers(min_value=1, max_value=4),
)
def test_round_trip(
    value: Any, delimiter: toon_format.Delimiter, indent_size: int
) -> None:
    text = toon_format.dumps(value, delimiter=delimiter, indent_size=indent_size)
    assert toon_format.loads(text, indent_size=indent_size) == value


@given(documents)
def test_output_invariants(value: Any) -> None:
    text = toon_format.dumps(value)
    assert not text.endswith("\n")
    for line in text.split("\n"):
        assert line == line.rstrip(" "), "no trailing spaces (§12)"
        assert not line.lstrip(" ").startswith("#"), "no comment lines (§5.1)"
        assert "\t" not in line[: len(line) - len(line.lstrip(" \t"))], (
            "no tab indentation"
        )
