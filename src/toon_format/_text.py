"""Lexical rules shared by the encoder and the decoder.

Quoting (§7.2), key encoding (§7.3), escaping (§7.1), and the number grammars
of §2 and §4 live here so that both directions agree on them.
"""

from __future__ import annotations

import re
from decimal import Decimal

__all__ = [
    "COMMA",
    "DELIMITERS",
    "PIPE",
    "TAB",
    "encode_key",
    "encode_string",
    "format_decimal",
    "format_float",
    "is_number_token",
    "quote",
]

COMMA = ","
TAB = "\t"
PIPE = "|"
DELIMITERS = (COMMA, TAB, PIPE)

# §7.3: keys and field names that may be written without quotes. ASCII only:
# Python's `\w` would also accept letters such as "é" (issue #65).
_UNQUOTED_KEY = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*")

# §7.2: strings that look numeric must be quoted. This is wider than the
# decoder grammar on purpose: "05" and "+1" are quoted too.
_NUMERIC_LIKE = re.compile(r"[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?")

# §4: the only unquoted tokens that decode as numbers. Leading zeros in the
# integer part ("05", "-007") are excluded, so those tokens stay strings.
_NUMBER = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?")

# Characters that force quoting wherever they appear in a string (§7.2).
_STRUCTURAL = re.compile(r'[:"\\\[\]{}\x00-\x1f]')

_ESCAPES = {"\\": "\\\\", '"': '\\"', "\n": "\\n", "\r": "\\r", "\t": "\\t"}
_NEEDS_ESCAPE = re.compile(r'[\\"\x00-\x1f]')

_CANONICAL_MIN = Decimal("1e-6")
_CANONICAL_MAX = Decimal("1e21")


def is_number_token(token: str) -> bool:
    """Return whether an unquoted token decodes as a number (§4)."""
    return _NUMBER.fullmatch(token) is not None


def _escape_char(match: re.Match[str]) -> str:
    char = match.group()
    return _ESCAPES.get(char) or f"\\u{ord(char):04x}"


def quote(value: str) -> str:
    """Return ``value`` as a quoted token, escaped per §7.1."""
    return '"' + _NEEDS_ESCAPE.sub(_escape_char, value) + '"'


def _needs_quotes(value: str, delimiter: str) -> bool:
    return (
        not value
        or value[0] in " \t-#\ufeff"  # a leading U+FEFF reads as a BOM (§12)
        or value[-1] in " \t"
        or value in ("true", "false", "null")
        or delimiter in value
        or _STRUCTURAL.search(value) is not None
        or _NUMERIC_LIKE.fullmatch(value) is not None
    )


def encode_string(value: str, delimiter: str) -> str:
    """Encode a string value, quoting it only when §7.2 requires it."""
    return quote(value) if _needs_quotes(value, delimiter) else value


def encode_key(key: str) -> str:
    """Encode an object key, entry key, or field name (§7.3)."""
    return key if _UNQUOTED_KEY.fullmatch(key) else quote(key)


def format_decimal(value: Decimal) -> str:
    """Format a finite decimal in the canonical number form of §2.

    Magnitudes in ``[1e-6, 1e21)`` use plain decimal notation without
    trailing zeros. Other magnitudes use JSON exponent notation with a
    lowercase ``e`` and an explicit exponent sign.
    """
    if not value:
        return "0"
    magnitude = abs(value)
    if _CANONICAL_MIN <= magnitude < _CANONICAL_MAX:
        text = f"{value:f}"
        if "." in text:
            text = text.rstrip("0").rstrip(".")
        return text
    # Decimal.normalize() would round to the context precision, so strip
    # trailing zeros by hand to keep every significant digit.
    sign, digits, exponent = value.as_tuple()
    assert isinstance(exponent, int)
    mantissa = "".join(map(str, digits)).rstrip("0")
    exponent += len(digits) - 1
    if len(mantissa) > 1:
        mantissa = f"{mantissa[0]}.{mantissa[1:]}"
    exponent_sign = "+" if exponent >= 0 else "-"
    return f"{'-' if sign else ''}{mantissa}e{exponent_sign}{abs(exponent)}"


def format_float(value: float) -> str:
    """Format a finite float in the canonical number form of §2.

    ``repr`` yields the shortest digit string that round-trips, so the output
    decodes back to the same float. Integral floats of 2**53 and beyond are
    written with their exact digits instead: they decode as ``int``, and the
    shortest digits would not equal the float (``float(2**60) == 2**60`` but
    ``1152921504606847000 != 2**60``).
    """
    if value.is_integer() and abs(value) < 1e21:
        return str(int(value))
    return format_decimal(Decimal(repr(value)))
