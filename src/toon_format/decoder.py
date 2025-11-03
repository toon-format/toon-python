"""TOON decoder implementation."""

from toon_format._decoders import decode_value_from_lines
from toon_format._scanner import LineCursor, to_parsed_lines
from toon_format.types import DecodeOptions, JsonValue, ResolvedDecodeOptions


def decode(input_str: str, options: DecodeOptions | None = None) -> JsonValue:
    """Convert a TOON-formatted string to a Python value.

    Args:
        input_str: A TOON-formatted string to parse
        options: Optional decoding options:
            - indent: Expected number of spaces per indentation level (default: 2)
            - strict: Enable strict validation (default: True)

    Returns:
        A Python value (dict, list, or primitive) representing the parsed TOON data.

    Raises:
        SyntaxError: If input has syntax errors (invalid escapes, missing colons, etc.)
        ValueError: If input is malformed (when strict=True, e.g., count mismatches)
        TypeError: If input is empty

    Examples:
        >>> decode('items[2]{sku,qty}:\\n  A1,2\\n  B2,1')
        {'items': [{'sku': 'A1', 'qty': 2}, {'sku': 'B2', 'qty': 1}]}

        >>> decode('tags[2]: foo,bar')
        {'tags': ['foo', 'bar']}

        >>> decode('[3]: 1,2,3')
        [1, 2, 3]
    """
    resolved_options = _resolve_decode_options(options)
    scan_result = to_parsed_lines(
        input_str,  # input string
        resolved_options.indent,  # indent
        resolved_options.strict,  # strict
    )

    if len(scan_result[0]) == 0:
        raise TypeError("Cannot decode empty input: input must be a non-empty string")

    cursor = LineCursor(scan_result[0], scan_result[1])
    return decode_value_from_lines(cursor, resolved_options)


def _resolve_decode_options(options: DecodeOptions | None) -> ResolvedDecodeOptions:
    """Resolve decode options with defaults.

    Args:
        options: Optional decode options

    Returns:
        Resolved options with defaults applied
    """
    indent = 2
    strict = True

    if options:
        if "indent" in options:
            indent = options["indent"]
        if "strict" in options:
            strict = options["strict"]

    return ResolvedDecodeOptions(
        indent=indent,
        strict=strict,
    )
