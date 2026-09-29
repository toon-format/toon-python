"""Deprecated compatibility layer for the ``toon_format`` 0.9 API.

New code should ``import toon`` and use :func:`toon.dumps` and
:func:`toon.loads`. This module keeps the old names working by delegating to
them; see ``docs/migration.md`` for the differences.
"""

from __future__ import annotations

import warnings
from collections.abc import Mapping
from typing import Any

import toon

from .types import DecodeOptions, Delimiter, DelimiterKey, EncodeOptions
from .utils import compare_formats, count_tokens, estimate_savings

__all__ = [
    "DecodeOptions",
    "Delimiter",
    "DelimiterKey",
    "EncodeOptions",
    "ToonDecodeError",
    "compare_formats",
    "count_tokens",
    "decode",
    "encode",
    "estimate_savings",
]

__version__ = toon.__version__

ToonDecodeError = toon.ToonDecodeError

warnings.warn(
    "The toon_format module is deprecated; "
    "use 'import toon' with toon.dumps() and toon.loads()",
    DeprecationWarning,
    stacklevel=2,
)

_DELIMITER_KEYS = {"comma": ",", "tab": "\t", "pipe": "|"}


def _to_null(value: Any) -> None:
    """The 0.9 encoder replaced unsupported values with null."""
    return None


def encode(value: Any, options: EncodeOptions | None = None) -> str:
    """Encode ``value`` as TOON. Deprecated: use :func:`toon.dumps`.

    Options: ``indent`` (spaces per level) and ``delimiter`` (``","``,
    ``"\\t"``, ``"|"``, or ``"comma"``/``"tab"``/``"pipe"``). ``lengthMarker``
    is no longer part of TOON and is ignored.
    """
    options = options or {}
    if options.get("lengthMarker"):
        warnings.warn(
            "lengthMarker is no longer part of TOON and is ignored",
            DeprecationWarning,
            stacklevel=2,
        )
    delimiter = options.get("delimiter", ",")
    return toon.dumps(
        value,
        indent_size=options.get("indent", 2),
        delimiter=_DELIMITER_KEYS.get(delimiter, delimiter),
        default=_to_null,
    )


def decode(input: str, options: DecodeOptions | Mapping[str, Any] | None = None) -> Any:
    """Decode a TOON document. Deprecated: use :func:`toon.loads`."""
    if options is None:
        options = DecodeOptions()
    elif isinstance(options, Mapping):
        options = DecodeOptions(**options)
    return toon.loads(input, indent_size=options.indent, strict=options.strict)
