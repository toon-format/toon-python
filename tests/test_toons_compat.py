"""Differential tests against toons, a Rust implementation of TOON 4.1.

The two implementations must agree on every encoding and on every document
the reference encoder can produce. Documented divergences on malformed input
are listed in AGENTS.md.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

import toon_format

from .strategies import documents

toons = pytest.importorskip("toons")

FIXTURES = Path(__file__).parent / "fixtures"


def _numbers_as_floats(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _numbers_as_floats(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_numbers_as_floats(item) for item in value]
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return value


def test_same_specification() -> None:
    assert toons.__toon_spec__ == toon_format.__toon_spec__


@given(
    documents,
    st.sampled_from(list(toon_format.Delimiter)),
    st.integers(min_value=2, max_value=4),
)
def test_encoders_agree(
    value: Any, delimiter: toon_format.Delimiter, indent_size: int
) -> None:
    ours = toon_format.dumps(value, delimiter=delimiter, indent_size=indent_size)
    theirs = toons.dumps(value, delimiter=str(delimiter), indent_size=indent_size)
    if ours != theirs:
        # §2 leaves the spelling of some floats open: toons writes plain
        # shortest digits everywhere, toon_format writes exponents outside
        # [1e-6, 1e21) and exact digits for integral floats from 2**53. Both
        # must still denote the same doubles.
        assert _numbers_as_floats(
            toon_format.loads(ours, indent_size=indent_size)
        ) == _numbers_as_floats(toon_format.loads(theirs, indent_size=indent_size))


@given(documents, st.sampled_from(list(toon_format.Delimiter)))
def test_decoders_agree(value: Any, delimiter: toon_format.Delimiter) -> None:
    text = toon_format.dumps(value, delimiter=delimiter)
    assert toon_format.loads(text) == toons.loads(text)


def _decode_fixture_inputs() -> list[Any]:
    params = []
    for path in sorted((FIXTURES / "decode").glob("*.json")):
        for index, case in enumerate(
            json.loads(path.read_text(encoding="utf-8"))["tests"]
        ):
            options = case.get("options", {})
            params.append(
                pytest.param(
                    case["input"],
                    {
                        "strict": options.get("strict", True),
                        "indent_size": options.get("indentSize", 2),
                    },
                    id=f"{path.stem}[{index}]",
                )
            )
    return params


def _outcome(module: Any, text: str, options: dict[str, Any]) -> Any:
    try:
        return module.loads(text, **options)
    except ValueError:
        return ValueError


@pytest.mark.parametrize(("text", "options"), _decode_fixture_inputs())
def test_decoders_agree_on_fixtures(text: str, options: dict[str, Any]) -> None:
    assert _outcome(toon_format, text, options) == _outcome(toons, text, options)
