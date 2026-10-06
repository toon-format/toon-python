"""The public interface: signatures, options, and file helpers."""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Any

import pytest

import toon_format


def test_public_names() -> None:
    assert sorted(toon_format.__all__) == sorted(
        [
            "Delimiter",
            "ToonDecodeError",
            "__toon_spec__",
            "__version__",
            "decode",
            "dump",
            "dumps",
            "encode",
            "load",
            "loads",
        ]
    )
    assert toon_format.__toon_spec__ == "4.3"
    assert re.fullmatch(r"\d+\.\d+\.\d+.*", toon_format.__version__)


def test_encode_and_decode_are_aliases() -> None:
    assert toon_format.encode is toon_format.dumps
    assert toon_format.decode is toon_format.loads


def test_delimiter_enum() -> None:
    assert toon_format.Delimiter.TAB == "\t"
    assert str(toon_format.Delimiter.PIPE) == "|"
    assert (
        toon_format.dumps([1, 2], delimiter=toon_format.Delimiter.PIPE) == "[2|]: 1|2"
    )


@pytest.mark.parametrize("delimiter", [";", "", ",,", "comma", None])
def test_invalid_delimiter(delimiter: Any) -> None:
    with pytest.raises(ValueError, match="delimiter must be"):
        toon_format.dumps([1], delimiter=delimiter)


@pytest.mark.parametrize(
    ("indent_size", "error"),
    [(0, ValueError), (-2, ValueError), (2.0, TypeError), (True, TypeError)],
)
def test_invalid_indent_size(indent_size: Any, error: type[Exception]) -> None:
    with pytest.raises(error, match="indent_size"):
        toon_format.dumps({"a": 1}, indent_size=indent_size)
    with pytest.raises(error, match="indent_size"):
        toon_format.loads("a: 1", indent_size=indent_size)


def test_options_are_keyword_only() -> None:
    with pytest.raises(TypeError):
        toon_format.dumps({"a": 1}, 4)  # type: ignore[misc]
    with pytest.raises(TypeError):
        toon_format.loads("a: 1", False)  # type: ignore[misc]


def test_dump_and_load_with_files(tmp_path: Path) -> None:
    data = {"users": [{"id": 1, "name": "Ada"}, {"id": 2, "name": "Bob"}]}
    path = tmp_path / "data.toon"
    with path.open("w", encoding="utf-8") as fp:
        toon_format.dump(data, fp, delimiter="\t")
    assert (
        path.read_text(encoding="utf-8") == "users[2\t]{id\tname}:\n  1\tAda\n  2\tBob"
    )
    with path.open(encoding="utf-8") as fp:
        assert toon_format.load(fp) == data
    with path.open("rb") as fp:
        assert toon_format.load(fp) == data


def test_load_passes_options() -> None:
    assert toon_format.load(io.StringIO("a[2]: 1"), strict=False, parse_int=str) == {
        "a": ["1"]
    }
