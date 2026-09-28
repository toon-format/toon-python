"""The deprecated ``toon_format`` 0.9 API keeps working on top of ``toon``."""

from __future__ import annotations

import importlib
import sys
from datetime import date
from types import ModuleType
from typing import Any

import pytest

import toon


@pytest.fixture
def toon_format() -> ModuleType:
    for name in [name for name in sys.modules if name.split(".")[0] == "toon_format"]:
        del sys.modules[name]
    with pytest.warns(DeprecationWarning, match="import toon"):
        return importlib.import_module("toon_format")


def test_encode_and_decode(toon_format: ModuleType) -> None:
    data = {"users": [{"id": 1, "name": "Ada"}], "day": date(2025, 1, 2)}
    text = toon_format.encode(data)
    assert text == toon.dumps(data)
    assert toon_format.decode(text) == {
        "users": [{"id": 1, "name": "Ada"}],
        "day": "2025-01-02",
    }


@pytest.mark.parametrize(
    ("delimiter", "expected"),
    [("\t", "[2\t]: 1\t2"), ("pipe", "[2|]: 1|2"), ("comma", "[2]: 1,2")],
)
def test_encode_options(toon_format: ModuleType, delimiter: str, expected: str) -> None:
    assert toon_format.encode([1, 2], {"delimiter": delimiter, "indent": 4}) == expected


def test_length_marker_is_ignored(toon_format: ModuleType) -> None:
    with pytest.warns(DeprecationWarning, match="lengthMarker"):
        assert toon_format.encode([1], {"lengthMarker": "#"}) == "[1]: 1"


def test_unsupported_values_become_null(toon_format: ModuleType) -> None:
    assert toon_format.encode({"f": print, "o": object()}) == "f: null\no: null"


@pytest.mark.parametrize("options", [None, {"strict": False}, "object"])
def test_decode_options(toon_format: ModuleType, options: Any) -> None:
    if options == "object":
        from toon_format.types import DecodeOptions

        options = DecodeOptions(indent=2, strict=False)
    if options is None:
        with pytest.raises(toon_format.ToonDecodeError):
            toon_format.decode("a[2]: 1", options)
    else:
        assert toon_format.decode("a[2]: 1", options) == {"a": [1]}


def test_decode_error_is_the_new_exception(toon_format: ModuleType) -> None:
    assert toon_format.ToonDecodeError is toon.ToonDecodeError


def test_pydantic_alias(toon_format: ModuleType) -> None:
    pytest.importorskip("pydantic")
    from toon.pydantic import ToonPydanticModel as Model
    from toon_format.pydantic import ToonPydanticModel

    assert ToonPydanticModel is Model


def test_token_utilities(
    toon_format: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    from toon_format import utils

    class FakeEncoding:
        def encode(self, text: str) -> list[str]:
            return text.split()

    monkeypatch.setattr(utils, "_encoding", lambda name: FakeEncoding())
    data = {"users": [{"id": 1, "name": "Ada"}, {"id": 2, "name": "Bob"}]}
    assert toon_format.count_tokens("a b c") == 3
    savings = toon_format.estimate_savings(data)
    assert savings["toon_tokens"] < savings["json_tokens"]
    assert toon_format.compare_formats(data).startswith("Format Comparison")


def test_token_utilities_need_tiktoken(
    toon_format: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    from toon_format import utils

    utils._encoding.cache_clear()
    monkeypatch.setitem(sys.modules, "tiktoken", None)
    with pytest.raises(RuntimeError, match="tiktoken is required"):
        toon_format.count_tokens("x", encoding="cl100k_base")
