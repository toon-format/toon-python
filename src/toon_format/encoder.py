"""TOON encoder implementation."""

from typing import Any

from toon_format._constants import DEFAULT_DELIMITER
from toon_format._encoders import encode_value
from toon_format._normalize import normalize_value
from toon_format.types import EncodeOptions, ResolvedEncodeOptions


def encode(value: Any, options: EncodeOptions | None = None) -> str:
    """Convert a value to TOON format.

    Args:
        value: Any JSON-serializable value (object, array, primitive, or nested).
               Non-JSON-serializable values (functions, undefined, non-finite numbers)
               are converted to null. Dates are converted to ISO strings, and BigInts
               are emitted as decimal integers.
        options: Optional encoding options:
            - indent: Number of spaces per indentation level (default: 2)
            - delimiter: Delimiter for array values and tabular rows (default: ',')
            - length_marker: Optional marker to prefix array lengths (default: False)

    Returns:
        A TOON-formatted string with no trailing newline or spaces.

    Examples:
        >>> encode({"items": [{"sku": "A1", "qty": 2}, {"sku": "B2", "qty": 1}]})
        'items[2]{sku,qty}:\\n  A1,2\\n  B2,1'

        >>> encode({"tags": ["foo", "bar"]}, {"delimiter": "\\t"})
        'tags[2\\t]: foo\\tbar'

        >>> encode([1, 2, 3], {"length_marker": "#"})
        '[#3]: 1,2,3'
    """
    normalized_value = normalize_value(value)
    resolved_options = _resolve_encode_options(options)
    return encode_value(normalized_value, resolved_options)


def _resolve_encode_options(options: EncodeOptions | None) -> ResolvedEncodeOptions:
    """Resolve encode options with defaults.

    Args:
        options: Optional encode options

    Returns:
        Resolved options with defaults applied
    """
    indent = 2
    delimiter = DEFAULT_DELIMITER
    length_marker: str | bool = False

    if options:
        if "indent" in options:
            indent = options["indent"]
        if "delimiter" in options:
            delimiter = options["delimiter"]
        if "length_marker" in options:
            length_marker = options["length_marker"]

    return ResolvedEncodeOptions(
        indent=indent,
        delimiter=delimiter,
        length_marker=length_marker,
    )
