"""Run the official conformance fixtures of the TOON specification."""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

import pytest

import toon_format

FIXTURES = Path(__file__).parent / "fixtures"


def _cases(category: str) -> list[Any]:
    cases = []
    for path in sorted((FIXTURES / category).glob("*.json")):
        for index, case in enumerate(
            json.loads(path.read_text(encoding="utf-8"))["tests"]
        ):
            cases.append(pytest.param(case, id=f"{path.stem}[{index}] {case['name']}"))
    return cases


def _encode_options(case: dict[str, Any]) -> dict[str, Any]:
    options = case.get("options", {})
    return {
        "indent_size": options.get("indentSize", 2),
        "delimiter": options.get("delimiter", ","),
    }


def _decode_options(case: dict[str, Any]) -> dict[str, Any]:
    options = case.get("options", {})
    return {
        "indent_size": options.get("indentSize", 2),
        "strict": options.get("strict", True),
    }


def _key_order(value: Any) -> Any:
    """The nested key sequences of a value, which ``==`` on dicts ignores."""
    if isinstance(value, dict):
        return [(key, _key_order(item)) for key, item in value.items()]
    if isinstance(value, list):
        return [_key_order(item) for item in value]
    return None


def _dumps_via_file(value: Any, **options: Any) -> str:
    buffer = io.StringIO()
    toon_format.dump(value, buffer, **options)
    return buffer.getvalue()


def _loads_via_file(text: str, **options: Any) -> Any:
    return toon_format.load(io.BytesIO(text.encode()), **options)


@pytest.mark.parametrize("encode", [toon_format.dumps, _dumps_via_file])
@pytest.mark.parametrize("case", _cases("encode"))
def test_encode(case: dict[str, Any], encode: Any) -> None:
    assert encode(case["input"], **_encode_options(case)) == case["expected"]


@pytest.mark.parametrize("decode", [toon_format.loads, _loads_via_file])
@pytest.mark.parametrize("case", _cases("decode"))
def test_decode(case: dict[str, Any], decode: Any) -> None:
    if case.get("shouldError"):
        with pytest.raises(toon_format.ToonDecodeError):
            decode(case["input"], **_decode_options(case))
    else:
        result = decode(case["input"], **_decode_options(case))
        assert result == case["expected"]
        # Key order is part of the data model (§2).
        assert _key_order(result) == _key_order(case["expected"])
