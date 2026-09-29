"""Encoder: Python objects to TOON text.

Encoding runs in two passes. :func:`normalize` maps host values onto the JSON
data model (§3), and :class:`_Encoder` renders that model, choosing each
value's form from its shape and position (§1.4, §8-§10).
"""

from __future__ import annotations

import dataclasses
import math
import re
import sys
from collections.abc import Callable, Iterator, Mapping
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from pathlib import PurePath
from typing import Any, TypeAlias
from uuid import UUID

from ._text import encode_key, encode_string, format_decimal, format_float

__all__ = ["encode"]

Json: TypeAlias = (
    "bool | int | float | Decimal | str | list[Json] | dict[str, Json] | None"
)

# An ordered field list: each field is a leaf (``None``) or a nested field group.
Shape: TypeAlias = "tuple[tuple[str, Shape | None], ...]"

_SURROGATE = re.compile("[\ud800-\udfff]")


def encode(
    obj: Any,
    *,
    indent_size: int,
    delimiter: str,
    default: Callable[[Any], Any] | None,
    sort_keys: bool,
) -> str:
    """Encode ``obj`` as a TOON document. Options are already validated."""
    try:
        value = _Normalizer(default, sort_keys).normalize(obj)
        encoder = _Encoder(indent_size, delimiter)
        encoder.root(value)
    except RecursionError:
        raise ValueError("Object is nested too deeply to encode") from None
    return "\n".join(encoder.lines)


# --------------------------------------------------------------------------
# Normalization (§3)
# --------------------------------------------------------------------------


def _check_string(value: str) -> str:
    if _SURROGATE.search(value):
        # §3: an unpaired surrogate has no TOON representation.
        raise ValueError(f"String contains an unpaired surrogate: {value!r}")
    return value


class _Normalizer:
    def __init__(self, default: Callable[[Any], Any] | None, sort_keys: bool) -> None:
        self.default = default
        self.sort_keys = sort_keys
        self.active: set[int] = set()

    def normalize(self, value: Any) -> Json:
        cls = type(value)
        if cls is str:
            return _check_string(value)
        if value is None or cls is bool or cls is int:
            return value  # type: ignore[no-any-return]
        if cls is float:
            return value if math.isfinite(value) else None
        if cls is dict or cls is list or cls is tuple:
            return self._container(value)
        return self._other(value)

    def _container(self, value: Any) -> Json:
        marker = id(value)
        if marker in self.active:
            raise ValueError("Circular reference detected")
        self.active.add(marker)
        try:
            if isinstance(value, Mapping):
                return self._mapping(value)
            items = value
            if isinstance(value, (set, frozenset)):
                items = _sorted_members(value)
            return [self.normalize(item) for item in items]
        finally:
            self.active.discard(marker)

    def _mapping(self, value: Mapping[Any, Any]) -> dict[str, Json]:
        pairs = [(_convert_key(key), item) for key, item in value.items()]
        if self.sort_keys:
            pairs.sort(key=lambda pair: pair[0])
        result: dict[str, Json] = {}
        for key, item in pairs:
            # Keys such as 1 and "1" collide once converted; keeping one value
            # would lose data, and a duplicate key is invalid TOON (§14).
            if key in result:
                raise ValueError(f"Duplicate key after conversion: {key!r}")
            result[key] = self.normalize(item)
        return result

    def _other(self, value: Any) -> Json:
        # Order matters: bool before int, str/int subclasses (StrEnum, IntEnum)
        # before Enum, datetime before date.
        if isinstance(value, str):
            return _check_string(str.__str__(value))
        if isinstance(value, bool):
            return bool(value)
        if isinstance(value, int):
            return int(value)
        if isinstance(value, float):
            number = float(value)
            return number if math.isfinite(number) else None
        if isinstance(value, Decimal):
            return value if value.is_finite() else None
        if isinstance(value, (Mapping, list, tuple, set, frozenset)):
            return self._container(value)
        if isinstance(value, (datetime, date, time)):
            return value.isoformat()
        if isinstance(value, (UUID, PurePath)):
            return str(value)
        if isinstance(value, Enum):
            return self._converted(value, value.value)
        if dataclasses.is_dataclass(value) and not isinstance(value, type):
            fields = {
                field.name: getattr(value, field.name)
                for field in dataclasses.fields(value)
            }
            return self._converted(value, fields)
        pydantic = sys.modules.get("pydantic")
        if pydantic is not None and isinstance(value, pydantic.BaseModel):
            return self._converted(value, value.model_dump(mode="json"))
        if self.default is not None:
            return self._converted(value, self.default(value))
        raise TypeError(
            f"Object of type {type(value).__name__} is not TOON serializable"
        )

    def _converted(self, original: Any, replacement: Any) -> Json:
        """Normalize ``replacement``, which must not lead back to ``original``."""
        marker = id(original)
        if marker in self.active:
            raise ValueError("Circular reference detected")
        self.active.add(marker)
        try:
            return self.normalize(replacement)
        finally:
            self.active.discard(marker)


def _sorted_members(value: set[Any] | frozenset[Any]) -> list[Any]:
    """Order set members deterministically (Appendix E.6)."""
    try:
        return sorted(value)
    except TypeError:
        return sorted(value, key=repr)


def _convert_key(key: Any) -> str:
    """Coerce a mapping key to a string, following :func:`json.dumps`."""
    if isinstance(key, str):
        return _check_string(str.__str__(key))
    if key is None or isinstance(key, bool):
        return "null" if key is None else ("true" if key else "false")
    if isinstance(key, int):
        return str(int(key))
    if isinstance(key, float):
        if math.isfinite(key):
            return format_float(key)
        return "NaN" if math.isnan(key) else ("Infinity" if key > 0 else "-Infinity")
    raise TypeError(
        f"Keys must be str, int, float, bool or None, not {type(key).__name__}"
    )


# --------------------------------------------------------------------------
# Form detection (§9.3, §9.5)
# --------------------------------------------------------------------------


def _is_primitive(value: Json) -> bool:
    return not isinstance(value, (dict, list))


def _shape(objects: list[Json]) -> Shape | None:
    """Return the shared field list of ``objects``, or ``None`` if they are not uniform.

    Objects are uniform when all are non-empty objects with the same set of
    keys and every column is uniform-primitive or nested-uniform (§9.3).
    """
    first = objects[0]
    if not isinstance(first, dict) or not first:
        return None
    keys = first.keys()
    for obj in objects:
        if not isinstance(obj, dict) or len(obj) != len(keys) or obj.keys() != keys:
            return None
    fields: list[tuple[str, Shape | None]] = []
    for key in keys:
        column = [obj[key] for obj in objects if isinstance(obj, dict)]
        if all(map(_is_primitive, column)):
            fields.append((key, None))
            continue
        nested = _shape(column)
        if nested is None:
            return None
        fields.append((key, nested))
    return tuple(fields)


def _keyed_shape(obj: dict[str, Json]) -> Shape | None:
    """Field list for the keyed tabular form of an object (§9.5)."""
    if len(obj) < 2:
        return None
    return _shape(list(obj.values()))


def _leaves(obj: Json, shape: Shape) -> Iterator[Json]:
    """Yield the leaf values of ``obj`` in depth-first header order."""
    assert isinstance(obj, dict)
    for key, nested in shape:
        if nested is None:
            yield obj[key]
        else:
            yield from _leaves(obj[key], nested)


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------


class _Encoder:
    def __init__(self, indent_size: int, delimiter: str) -> None:
        self.unit = " " * indent_size
        self.delimiter = delimiter
        # §11.1: every header declares the document delimiter; comma is implicit.
        self.symbol = "" if delimiter == "," else delimiter
        self.lines: list[str] = []

    def emit(self, depth: int, text: str) -> None:
        self.lines.append(self.unit * depth + text)

    def root(self, value: Json) -> None:
        if isinstance(value, dict):
            shape = _keyed_shape(value)
            if shape is not None:
                self.keyed("", value, shape, 0)
            else:
                self.fields(value, 0)  # an empty object is an empty document (§8)
        elif isinstance(value, list):
            if value:
                self.array("", value, 0, tabular=True)
            else:
                self.emit(0, "[]")
        else:
            self.emit(0, self.primitive(value))

    def primitive(self, value: Json) -> str:
        if value is None:
            return "null"
        if value is True:
            return "true"
        if value is False:
            return "false"
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            return format_float(value)
        if isinstance(value, Decimal):
            return format_decimal(value)
        assert isinstance(value, str)
        return encode_string(value, self.delimiter)

    def join(self, values: Iterator[Json] | list[Json]) -> str:
        return self.delimiter.join(map(self.primitive, values))

    def field_list(self, shape: Shape) -> str:
        entries = (
            encode_key(key) + ("" if nested is None else self.field_list(nested))
            for key, nested in shape
        )
        return "{" + self.delimiter.join(entries) + "}"

    def fields(self, obj: dict[str, Json], depth: int) -> None:
        for key, value in obj.items():
            self.field(encode_key(key), value, depth)

    def field(self, key: str, value: Json, depth: int) -> None:
        """Emit one object field; ``key`` is already encoded (§8)."""
        if isinstance(value, dict):
            shape = _keyed_shape(value)
            if shape is not None:
                self.keyed(key, value, shape, depth)
            else:
                self.emit(depth, key + ":")
                self.fields(value, depth + 1)
        elif isinstance(value, list):
            if value:
                self.array(key, value, depth, tabular=True)
            else:
                self.emit(depth, key + ": []")
        else:
            self.emit(depth, f"{key}: {self.primitive(value)}")

    def array(
        self, prefix: str, array: list[Json], depth: int, *, tabular: bool
    ) -> None:
        """Emit a non-empty array whose header starts with ``prefix``.

        ``tabular`` is false for a keyless array that is itself a list item,
        where a field list is not allowed (§9.4).
        """
        head = f"{prefix}[{len(array)}{self.symbol}]"
        if all(map(_is_primitive, array)):
            self.emit(depth, f"{head}: {self.join(array)}")  # §9.1
            return
        shape = _shape(array) if tabular else None
        if shape is not None:
            self.emit(depth, f"{head}{self.field_list(shape)}:")  # §9.3
            for element in array:
                self.emit(depth + 1, self.join(_leaves(element, shape)))
            return
        self.emit(depth, head + ":")  # §9.2, §9.4
        for element in array:
            self.item(element, depth + 1)

    def keyed(self, key: str, obj: dict[str, Json], shape: Shape, depth: int) -> None:
        """Emit an object of uniform objects in keyed tabular form (§9.5)."""
        self.emit(depth, f"{key}[{len(obj)}:{self.symbol}]{self.field_list(shape)}:")
        for entry, value in obj.items():
            self.emit(
                depth + 1, f"{encode_key(entry)}: {self.join(_leaves(value, shape))}"
            )

    def item(self, value: Json, depth: int) -> None:
        """Emit one list item at ``depth`` (§9.4, §10)."""
        if isinstance(value, dict):
            if not value:
                self.emit(depth, "-")
                return
            # The object's fields stand at depth + 1; the first one moves onto
            # the hyphen line, so whatever scope it opens lands at depth + 2.
            first = len(self.lines)
            self.fields(value, depth + 1)
            indent = self.unit * depth
            self.lines[first] = (
                indent + "- " + self.lines[first][len(indent + self.unit) :]
            )
        elif isinstance(value, list):
            if value:
                self.array("- ", value, depth, tabular=False)
            else:
                self.emit(depth, f"- [0{self.symbol}]:")  # never "- []" (§9.2)
        else:
            self.emit(depth, "- " + self.primitive(value))
