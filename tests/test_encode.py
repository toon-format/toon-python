"""Encoder behavior beyond the specification fixtures: host types, numbers, forms."""

from __future__ import annotations

import collections
import dataclasses
import enum
import sys
import types
import uuid
from datetime import date, datetime, time, timezone
from decimal import Decimal
from pathlib import PurePosixPath
from typing import Any

import pytest

import toon


class Color(enum.Enum):
    RED = "red"
    GREEN = 2


class Size(enum.IntEnum):
    LARGE = 3


class Mode(str, enum.Enum):
    FAST = "fast"


@dataclasses.dataclass
class Point:
    x: int
    y: int


@dataclasses.dataclass
class Shape:
    name: str
    points: list[Point]


# -- numbers (§2, §3) -------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, "0"),
        (-7, "-7"),
        (2**70, "1180591620717411303424"),
        (1.0, "1"),
        (-0.0, "0"),
        (1.5, "1.5"),
        (0.1 + 0.2, "0.30000000000000004"),
        (1e6, "1000000"),
        (1e16, "10000000000000000"),
        (1.5e20, "150000000000000000000"),
        (1e-6, "0.000001"),
        (2.5e-4, "0.00025"),
        (1e21, "1e+21"),
        (1.25e300, "1.25e+300"),
        (1e-7, "1e-7"),
        (-5e-324, "-5e-324"),
        (float("nan"), "null"),
        (float("inf"), "null"),
        (float("-inf"), "null"),
        (Decimal("1.50"), "1.5"),
        (Decimal("-0.00"), "0"),
        (
            Decimal("123456789012345678901234567890.5"),
            "1.234567890123456789012345678905e+29",
        ),
        (Decimal("0.1"), "0.1"),
        (Decimal("NaN"), "null"),
        (Decimal("-Infinity"), "null"),
        (True, "true"),
        (False, "false"),
        (None, "null"),
    ],
)
def test_numbers_and_literals(value: Any, expected: str) -> None:
    assert toon.dumps(value) == expected
    assert toon.dumps({"v": value}) == f"v: {expected}"


@pytest.mark.parametrize(
    "value", [1e-7, 1e21, 1.7976931348623157e308, 5e-324, 0.1, 123.456]
)
def test_floats_round_trip(value: float) -> None:
    assert toon.loads(toon.dumps(value)) == value


# -- strings (§7) -------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("hello world", "hello world"),
        ("", '""'),
        (" padded", '" padded"'),
        ("tab\t", '"tab\\t"'),
        ("true", '"true"'),
        ("null", '"null"'),
        ("42", '"42"'),
        ("05", '"05"'),
        ("+1", '"+1"'),
        ("1e-6", '"1e-6"'),
        (".5", ".5"),
        ("a:b", '"a:b"'),
        ("a,b", '"a,b"'),
        ("a|b", "a|b"),
        ("[x]", '"[x]"'),
        ("{x}", '"{x}"'),
        ("- item", '"- item"'),
        ("-", '"-"'),
        ("#tag", '"#tag"'),
        ("a#b", "a#b"),
        ('say "hi"', '"say \\"hi\\""'),
        ("back\\slash", '"back\\\\slash"'),
        ("line\nbreak\r", '"line\\nbreak\\r"'),
        ("bell\x07", '"bell\\u0007"'),
        ("\x7f", "\x7f"),
        ("café 🚀", "café 🚀"),
        ("\xa0nbsp", "\xa0nbsp"),
    ],
)
def test_string_quoting(value: str, expected: str) -> None:
    assert toon.dumps({"v": value}) == f"v: {expected}"
    assert toon.loads(toon.dumps(value)) == value


def test_delimiter_aware_quoting() -> None:
    data = {"note": "a|b", "tags": ["a|b", "c,d"]}
    assert toon.dumps(data, delimiter="|") == 'note: "a|b"\ntags[2|]: "a|b"|c,d'
    assert (
        toon.dumps(data, delimiter=toon.Delimiter.TAB)
        == "note: a|b\ntags[2\t]: a|b\tc,d"
    )


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("name", "name"),
        ("_private", "_private"),
        ("user.name", "user.name"),
        ("full name", '"full name"'),
        ("my-key", '"my-key"'),
        ("2x", '"2x"'),
        ("", '""'),
        ("é", '"é"'),
        ("aé", '"aé"'),  # issue #65: ASCII-only pattern, even after the first character
        ("日本", '"日本"'),
    ],
)
def test_key_quoting(key: str, expected: str) -> None:
    assert toon.dumps({key: 1}) == f"{expected}: 1"


@pytest.mark.parametrize("value", ["\ud800", {"\udfff": 1}, ["ok", "a\udc80b"]])
def test_unpaired_surrogates_are_rejected(value: Any) -> None:
    with pytest.raises(ValueError, match="surrogate"):
        toon.dumps(value)


# -- host types (§3, Appendix E.3) -------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (datetime(2025, 1, 2, 3, 4, 5), '"2025-01-02T03:04:05"'),
        (datetime(2025, 1, 2, tzinfo=timezone.utc), '"2025-01-02T00:00:00+00:00"'),
        (date(2025, 1, 2), "2025-01-02"),
        (time(13, 45), '"13:45:00"'),
        (uuid.UUID(int=1), "00000000-0000-0000-0000-000000000001"),
        (PurePosixPath("/tmp/data.json"), "/tmp/data.json"),
        (Color.RED, "red"),
        (Color.GREEN, "2"),
        (Size.LARGE, "3"),
        (Mode.FAST, "fast"),
    ],
)
def test_scalar_host_types(value: Any, expected: str) -> None:
    assert toon.dumps({"v": value}) == f"v: {expected}"


def test_collections() -> None:
    data = {
        "tuple": (1, 2),
        "set": {3, 1, 2},
        "frozen": frozenset({"b", "a"}),
        "mixed": {1, "a"},  # not mutually comparable: ordered by repr()
        "mapping": types.MappingProxyType({"k": 1}),
        "ordered": collections.OrderedDict(z=1, a=2),
    }
    assert toon.dumps(data) == (
        "tuple[2]: 1,2\n"
        "set[3]: 1,2,3\n"
        "frozen[2]: a,b\n"
        "mixed[2]: a,1\n"
        "mapping:\n  k: 1\n"
        "ordered:\n  z: 1\n  a: 2"
    )


def test_dataclasses() -> None:
    shape = Shape("tri", [Point(0, 0), Point(1, 0), Point(0, 1)])
    assert toon.dumps(shape) == "name: tri\npoints[3]{x,y}:\n  0,0\n  1,0\n  0,1"
    with pytest.raises(TypeError):
        toon.dumps(Point)  # the class itself is not data


def test_attrs_classes() -> None:
    attrs = pytest.importorskip("attrs")

    @attrs.define
    class Item:
        name: str
        tags: list[str] = attrs.field(factory=list)
        _secret: int = attrs.field(default=0, repr=False)

    assert toon.dumps({"items": [Item("a", ["x"]), Item("b")]}) == (
        "items[2]:\n  - name: a\n    tags[1]: x\n    _secret: 0\n"
        "  - name: b\n    tags: []\n    _secret: 0"
    )
    with pytest.raises(TypeError):
        toon.dumps(Item)  # the class itself is not data


@pytest.mark.parametrize(
    ("key", "expected"),
    [(1, '"1"'), (1.5, '"1.5"'), (True, "true"), (None, "null"), (Size.LARGE, '"3"')],
)
def test_non_string_keys_are_coerced_like_json(key: Any, expected: str) -> None:
    assert toon.dumps({key: "x"}) == f"{expected}: x"


@pytest.mark.parametrize(
    "value", [{1: "a", "1": "b"}, {True: "a", "true": "b"}, {None: 1, "null": 2}]
)
def test_keys_colliding_after_conversion(value: dict[Any, Any]) -> None:
    with pytest.raises(ValueError, match="Duplicate key after conversion"):
        toon.dumps(value)


def test_unsupported_keys() -> None:
    with pytest.raises(TypeError, match="Keys must be"):
        toon.dumps({(1, 2): "x"})


@pytest.mark.parametrize("value", [object(), b"bytes", 1j, iter([1]), print])
def test_unsupported_values_raise_type_error(value: Any) -> None:
    with pytest.raises(TypeError, match="is not TOON serializable"):
        toon.dumps({"v": value})


def test_default_hook() -> None:
    def default(value: Any) -> Any:
        if isinstance(value, complex):
            return {"re": value.real, "im": value.imag}
        raise TypeError(f"cannot encode {type(value).__name__}")

    assert toon.dumps({"z": 1 + 2j}, default=default) == "z:\n  re: 1\n  im: 2"
    with pytest.raises(TypeError, match="cannot encode bytes"):
        toon.dumps(b"x", default=default)


def test_default_hook_is_not_called_for_supported_types() -> None:
    calls = []
    toon.dumps({"a": [1, "x", None]}, default=calls.append)
    assert calls == []


def test_sort_keys() -> None:
    data = {"b": 1, "a": {"d": 2, "c": 3}, "rows": [{"y": 1, "x": 2}]}
    assert (
        toon.dumps(data, sort_keys=True)
        == "a:\n  c: 3\n  d: 2\nb: 1\nrows[1]{x,y}:\n  2,1"
    )


# -- errors ---------------------------------------------------------------------


def test_circular_references() -> None:
    items: list[Any] = [1]
    items.append(items)
    with pytest.raises(ValueError, match="Circular reference"):
        toon.dumps(items)
    obj: dict[str, Any] = {}
    obj["self"] = obj
    with pytest.raises(ValueError, match="Circular reference"):
        toon.dumps(obj)


def test_default_returning_its_argument_is_a_cycle() -> None:
    with pytest.raises(ValueError, match="Circular reference"):
        toon.dumps(object(), default=lambda value: value)


def test_shared_references_are_not_cycles() -> None:
    shared = {"x": 1}
    assert toon.dumps([shared, shared]) == "[2]{x}:\n  1\n  1"


def test_deep_nesting_raises_value_error() -> None:
    value: Any = 0
    for _ in range(sys.getrecursionlimit() + 10):
        value = [value]
    with pytest.raises(ValueError, match="nested too deeply"):
        toon.dumps(value)


# -- forms (§9, §10) and regressions from the issue tracker -------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        # issue #64: an empty key keeps its level
        ({"": {"a": 1}}, '"":\n  a: 1'),
        ({"": [1, 2]}, '""[2]: 1,2'),
        # issue #62: every nested array item carries its marker
        ([[[1]]], "[1]:\n  - [1]:\n    - [1]: 1"),
        ([[[]]], "[1]:\n  - [1]:\n    - [0]:"),
        # issue #63: an empty object as the first field of a list item
        ([{"a": {}, "b": 1}], "[1]:\n  - a:\n    b: 1"),
        # issue #61: the empty root array
        ([], "[]"),
        ({}, ""),
        # keyed tabular form at the root and nested (§9.5)
        ({"a": {"x": 1}, "b": {"x": 2}}, "[2:]{x}:\n  a: 1\n  b: 2"),
        ({"m": {"a": {"x": 1}}}, "m:\n  a:\n    x: 1"),
        # nested field groups (§9.3)
        (
            {
                "o": [
                    {"id": 1, "c": {"n": "a", "k": "x"}},
                    {"id": 2, "c": {"k": "y", "n": "b"}},
                ]
            },
            "o[2]{id,c{n,k}}:\n  1,a,x\n  2,b,y",
        ),
        # a column mixing null with objects is not uniform
        (
            {"o": [{"c": None}, {"c": {"n": 1}}]},
            "o[2]:\n  - c: null\n  - c:\n      n: 1",
        ),
        # a tabular first field of a list-item object (§10)
        (
            [{"rows": [{"a": 1}, {"a": 2}], "ok": True}],
            "[1]:\n  - rows[2]{a}:\n      1\n      2\n    ok: true",
        ),
        # arrays of arrays of objects never use a keyless field list
        ([[{"a": 1}, {"a": 2}]], "[1]:\n  - [2]:\n    - a: 1\n    - a: 2"),
    ],
)
def test_forms(value: Any, expected: str) -> None:
    assert toon.dumps(value) == expected
    assert toon.loads(expected) == value


def test_indent_size() -> None:
    data = {"a": {"b": [{"c": 1, "d": {"e": 2}}, 3]}}
    assert toon.dumps(data, indent_size=4) == (
        "a:\n    b[2]:\n        - c: 1\n            d:\n                e: 2\n        - 3"
    )
    for size in (1, 3, 4, 8):
        assert toon.loads(toon.dumps(data, indent_size=size), indent_size=size) == data


def test_subclasses_of_builtins() -> None:
    class Ratio(float):
        pass

    class Count(int):
        pass

    class Name(str):
        def __str__(self) -> str:
            return "overridden"

    assert (
        toon.dumps([Ratio(0.5), Ratio("inf"), Count(3), Name("ada")])
        == "[4]: 0.5,null,3,ada"
    )


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        (float("nan"), "NaN: 1"),
        (float("inf"), "Infinity: 1"),
        (float("-inf"), '"-Infinity": 1'),
    ],
)
def test_non_finite_float_keys(key: float, expected: str) -> None:
    assert toon.dumps({key: 1}) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("\ufeffabc", '"\ufeffabc"'),
        ({"a": "\ufeffx"}, 'a: "\ufeffx"'),
        (["\ufeffx"], '[1]: "\ufeffx"'),
    ],
)
def test_leading_byte_order_mark_is_quoted(value: Any, expected: str) -> None:
    assert toon.dumps(value) == expected
    assert toon.loads(expected) == value
