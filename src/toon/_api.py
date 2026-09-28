"""The public ``json``-style functions: ``dumps``, ``dump``, ``loads``, ``load``."""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import IO, Any

from . import _decoder, _encoder
from ._errors import ToonDecodeError
from ._text import DELIMITERS

__all__ = ["Delimiter", "dump", "dumps", "load", "loads"]


class Delimiter(str, Enum):
    """The delimiters TOON supports (§11). Members compare equal to their character."""

    COMMA = ","
    TAB = "\t"
    PIPE = "|"

    def __str__(self) -> str:
        return self.value


def _check_indent_size(indent_size: int) -> int:
    if isinstance(indent_size, bool) or not isinstance(indent_size, int):
        raise TypeError(f"indent_size must be an int, not {type(indent_size).__name__}")
    if indent_size < 1:
        raise ValueError(f"indent_size must be at least 1, got {indent_size}")
    return indent_size


def dumps(
    obj: Any,
    *,
    indent_size: int = 2,
    delimiter: str = ",",
    default: Callable[[Any], Any] | None = None,
    sort_keys: bool = False,
) -> str:
    """Serialize ``obj`` to a TOON document.

    Args:
        obj: The value to encode. ``dict``, ``list``, ``tuple``, ``str``,
            ``int``, ``float``, ``bool``, and ``None`` map directly onto the
            JSON data model; see the documentation for other supported types.
        indent_size: Spaces per indentation level.
        delimiter: Document delimiter: ``","``, ``"\\t"``, or ``"|"``
            (or a :class:`Delimiter` member).
        default: Called with any value that has no TOON representation; it
            should return an encodable replacement or raise :class:`TypeError`.
        sort_keys: Sort the keys of every object.

    Returns:
        The TOON document, without a trailing newline.

    Raises:
        TypeError: A value, or a mapping key, cannot be encoded.
        ValueError: An option is invalid, the object contains a reference
            cycle, a string contains an unpaired surrogate, or the object is
            nested too deeply.
    """
    if delimiter not in DELIMITERS:
        raise ValueError(f"delimiter must be ',', '\\t', or '|', got {delimiter!r}")
    return _encoder.encode(
        obj,
        indent_size=_check_indent_size(indent_size),
        delimiter=str.__str__(delimiter),
        default=default,
        sort_keys=sort_keys,
    )


def dump(
    obj: Any,
    fp: IO[str],
    *,
    indent_size: int = 2,
    delimiter: str = ",",
    default: Callable[[Any], Any] | None = None,
    sort_keys: bool = False,
) -> None:
    """Serialize ``obj`` as a TOON document to the text file ``fp``.

    Accepts the same options as :func:`dumps`.
    """
    fp.write(
        dumps(
            obj,
            indent_size=indent_size,
            delimiter=delimiter,
            default=default,
            sort_keys=sort_keys,
        )
    )


def loads(
    s: str | bytes | bytearray,
    *,
    strict: bool = True,
    indent_size: int = 2,
    parse_float: Callable[[str], Any] | None = None,
    parse_int: Callable[[str], Any] | None = None,
    object_hook: Callable[[dict[str, Any]], Any] | None = None,
    object_pairs_hook: Callable[[list[tuple[str, Any]]], Any] | None = None,
) -> Any:
    """Deserialize a TOON document to a Python object.

    Args:
        s: The document. Bytes are decoded as UTF-8; ill-formed UTF-8 is an error.
        strict: Enforce every check of §14. With ``strict=False``, length and
            width mismatches, blank lines inside arrays, irregular
            indentation, and duplicate keys (last one wins) are tolerated.
        indent_size: Spaces per indentation level.
        parse_float: Called with the text of every number that has a fraction
            or an exponent, as in :func:`json.loads`. Use
            :class:`decimal.Decimal` for lossless decoding.
        parse_int: Called with the text of every integer.
        object_hook: Called with every decoded object; its return value is
            used instead of the ``dict``.
        object_pairs_hook: Called with every decoded object as a list of
            ``(key, value)`` pairs; takes priority over ``object_hook``.

    Returns:
        The decoded value.

    Raises:
        ToonDecodeError: The document is not valid TOON.
        ValueError: An option is invalid.
    """
    if isinstance(s, (bytes, bytearray)):
        try:
            s = s.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ToonDecodeError(
                f"Invalid UTF-8: {exc.reason} at byte {exc.start}"
            ) from None
    elif not isinstance(s, str):
        raise TypeError(
            f"the TOON document must be str, bytes or bytearray, not {type(s).__name__}"
        )
    return _decoder.decode(
        s,
        indent_size=_check_indent_size(indent_size),
        strict=strict,
        parse_int=parse_int,
        parse_float=parse_float,
        object_hook=object_hook,
        object_pairs_hook=object_pairs_hook,
    )


def load(
    fp: IO[str] | IO[bytes],
    *,
    strict: bool = True,
    indent_size: int = 2,
    parse_float: Callable[[str], Any] | None = None,
    parse_int: Callable[[str], Any] | None = None,
    object_hook: Callable[[dict[str, Any]], Any] | None = None,
    object_pairs_hook: Callable[[list[tuple[str, Any]]], Any] | None = None,
) -> Any:
    """Deserialize a TOON document read from the file object ``fp``.

    Accepts the same options as :func:`loads`; ``fp`` may be opened in text
    or binary mode.
    """
    return loads(
        fp.read(),
        strict=strict,
        indent_size=indent_size,
        parse_float=parse_float,
        parse_int=parse_int,
        object_hook=object_hook,
        object_pairs_hook=object_pairs_hook,
    )
