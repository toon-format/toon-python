"""Option types of the deprecated ``toon_format`` 0.9 API."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

__all__ = ["DecodeOptions", "Delimiter", "DelimiterKey", "EncodeOptions", "JsonValue"]

JsonValue = Any
Delimiter = str
DelimiterKey = Literal["comma", "tab", "pipe"]


class EncodeOptions(TypedDict, total=False):
    """Options for :func:`toon_format.encode`."""

    indent: int
    delimiter: Delimiter
    lengthMarker: Literal["#"] | Literal[False]


class DecodeOptions:
    """Options for :func:`toon_format.decode`."""

    def __init__(self, indent: int = 2, strict: bool = True) -> None:
        self.indent = indent
        self.strict = strict
