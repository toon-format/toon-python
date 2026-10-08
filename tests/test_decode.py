"""Decoder behavior beyond the specification fixtures."""

from __future__ import annotations

import pickle
import sys
from collections import OrderedDict
from decimal import Decimal
from typing import Any

import pytest

import toon_format

# -- numbers (§4) ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected", "kind"),
    [
        ("42", 42, int),
        ("-0", 0, int),
        ("1180591620717411303424", 2**70, int),
        ("1.5", 1.5, float),
        ("1e3", 1000.0, float),
        ("-0.0", 0.0, float),
        ("1e-400", 0.0, float),
    ],
)
def test_number_types(text: str, expected: Any, kind: type) -> None:
    value = toon_format.loads(text)
    assert value == expected
    assert type(value) is kind


def test_negative_zero_decodes_to_positive_zero() -> None:
    assert str(toon_format.loads("-0.0")) == "0.0"


def test_out_of_range_floats() -> None:
    with pytest.raises(toon_format.ToonDecodeError, match="out of range"):
        toon_format.loads("x: 1e400")


def test_parse_float_and_parse_int() -> None:
    text = "a: 0.1\nb: 1e400\nc: 7"
    assert toon_format.loads(text, parse_float=Decimal) == {
        "a": Decimal("0.1"),
        "b": Decimal("1e400"),
        "c": 7,
    }
    assert toon_format.loads("n[2]: 1,2.5", parse_int=str) == {"n": ["1", 2.5]}


# -- hooks ------------------------------------------------------------------------


def test_object_hook_sees_every_object() -> None:
    text = "a:\n  b: 1\nrows[1]{x,g{y}}:\n  1,2\nm[2:]{v}:\n  k: 1\n  l: 2"
    seen: list[dict[str, Any]] = []

    def hook(obj: dict[str, Any]) -> dict[str, Any]:
        seen.append(dict(obj))
        return obj

    toon_format.loads(text, object_hook=hook)
    assert seen == [
        {"b": 1},
        {"y": 2},
        {"x": 1, "g": {"y": 2}},
        {"v": 1},
        {"v": 2},
        {"k": {"v": 1}, "l": {"v": 2}},
        {
            "a": {"b": 1},
            "rows": [{"x": 1, "g": {"y": 2}}],
            "m": {"k": {"v": 1}, "l": {"v": 2}},
        },
    ]


def test_object_pairs_hook_takes_priority() -> None:
    result = toon_format.loads(
        "b: 1\na:\n  c: 2", object_pairs_hook=OrderedDict, object_hook=lambda obj: 1 / 0
    )
    assert result == OrderedDict([("b", 1), ("a", OrderedDict([("c", 2)]))])
    assert isinstance(result["a"], OrderedDict)


def test_empty_document_goes_through_the_hook() -> None:
    assert toon_format.loads("", object_pairs_hook=list) == []


# -- input handling (§4, §12) ---------------------------------------------------------


def test_bytes_input() -> None:
    assert toon_format.loads("name: café".encode()) == {"name": "café"}
    assert toon_format.loads(bytearray(b"a: 1")) == {"a": 1}


def test_invalid_utf8_is_an_error() -> None:
    with pytest.raises(toon_format.ToonDecodeError, match="Invalid UTF-8"):
        toon_format.loads(b"a: \xff")
    with pytest.raises(toon_format.ToonDecodeError, match="Invalid UTF-8"):
        toon_format.loads(b"a: \xed\xa0\x80")  # an encoded surrogate


def test_wrong_input_type() -> None:
    with pytest.raises(TypeError, match="must be str, bytes or bytearray"):
        toon_format.loads(42)  # type: ignore[arg-type]


def test_bom_and_line_endings() -> None:
    assert toon_format.loads("\ufeffa: 1\r\nb:\r\n  c: 2\r\n") == {
        "a": 1,
        "b": {"c": 2},
    }
    assert toon_format.loads("a: x\ry") == {
        "a": "x\ry"
    }  # a CR inside a line is content


# -- errors -------------------------------------------------------------------------


def test_error_attributes() -> None:
    with pytest.raises(toon_format.ToonDecodeError) as info:
        toon_format.loads("a: 1\nitems[3]: x,y")
    error = info.value
    assert isinstance(error, ValueError)
    assert error.line == 2
    assert error.source == "items[3]: x,y"
    assert error.msg == "Declared length 3 but found 2"
    assert str(error) == "line 2: Declared length 3 but found 2"


def test_error_is_picklable() -> None:
    error = toon_format.ToonDecodeError("boom", 3, "x")
    clone = pickle.loads(pickle.dumps(error))
    assert (clone.msg, clone.line, clone.source, str(clone)) == (
        "boom",
        3,
        "x",
        "line 3: boom",
    )


@pytest.mark.parametrize(
    "text",
    [
        'a: "unterminated',
        'a: "bad \\x escape"',
        'a: "\\u12"',
        'a: "\\ud83d\\ude80"',  # surrogate escapes are rejected even in pairs (§7.1)
        'a: "x" y',
        '"k"x: 1',
        "a\nb",
        "a:\n  b: 1\n  loose",
    ],
)
def test_errors_in_any_mode(text: str) -> None:
    for strict in (True, False):
        with pytest.raises(toon_format.ToonDecodeError):
            toon_format.loads(text, strict=strict)


def test_deep_nesting_raises_decode_error() -> None:
    text = "\n".join("  " * depth + "a:" for depth in range(5000))
    with pytest.raises(toon_format.ToonDecodeError, match="nested too deeply"):
        toon_format.loads(text)


# -- indentation (§12) -----------------------------------------------------------------


def test_indent_size_option() -> None:
    assert toon_format.loads("a:\n    b: 1", indent_size=4) == {"a": {"b": 1}}
    with pytest.raises(toon_format.ToonDecodeError, match="multiple of 4"):
        toon_format.loads("a:\n  b: 1", indent_size=4)


# -- regressions from the issue tracker ---------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("[]", []),  # issue #61
        ("items: []", {"items": []}),
        (
            'items[1]:\n  - a:\n      b: "123"',
            {"items": [{"a": {"b": "123"}}]},
        ),  # issue #33
        (
            'text: "He said \\"hi: there\\""',
            {"text": 'He said "hi: there"'},
        ),  # issue #40
        ('a: "x,y"\nb[2]: "1,2","3"', {"a": "x,y", "b": ["1,2", "3"]}),
    ],
)
def test_regressions(text: str, expected: Any) -> None:
    assert toon_format.loads(text) == expected


def test_nested_length_mismatch_is_reported() -> None:
    # issue #47: a count mismatch deep inside must not truncate the document silently.
    text = "outer[1]:\n  - inner[3]: a,b\n    x: 1\ntail: 2"
    with pytest.raises(
        toon_format.ToonDecodeError, match="Declared length 3 but found 2"
    ) as info:
        toon_format.loads(text)
    assert info.value.line == 2
    assert toon_format.loads(text, strict=False) == {
        "outer": [{"inner": ["a", "b"], "x": 1}],
        "tail": 2,
    }


def test_row_or_key_value_at_row_depth() -> None:
    # §9.3: a delimiter before the first colon keeps the line a row...
    assert toon_format.loads("t[1]{x,y}:\n  a,b:c") == {"t": [{"x": "a", "y": "b:c"}]}
    # ...and a colon first ends the rows, leaving the line in no scope.
    with pytest.raises(toon_format.ToonDecodeError, match="Unexpected indentation"):
        toon_format.loads("t[1]{x}:\n  1\n  n: 2")


def test_hyphen_outside_a_list_is_part_of_the_key() -> None:
    # §5.2: a leading hyphen marks a list item only at item depth; elsewhere it
    # is ordinary text.
    assert toon_format.loads("- a") == "- a"
    assert toon_format.loads("items[1]:\n  - x\n- a: 1", strict=False) == {
        "items": ["x"],
        "- a": 1,
    }


def test_integer_beyond_the_conversion_limit() -> None:
    if not hasattr(sys, "set_int_max_str_digits"):
        pytest.skip("no integer string conversion limit")
    with pytest.raises(toon_format.ToonDecodeError, match="line 1"):
        toon_format.loads("n: " + "9" * 5000)


def test_unterminated_quote_in_a_field_list_hides_the_colon() -> None:
    assert toon_format.loads('t[1]{"x}:') == 't[1]{"x}:'
