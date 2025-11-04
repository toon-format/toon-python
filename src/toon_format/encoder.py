# Copyright (c) 2025 TOON Format Organization
# SPDX-License-Identifier: MIT
"""Core TOON encoding functionality.

This module provides the main `encode()` function for converting Python values
to TOON format strings. Handles option resolution and coordinates the encoding
pipeline: normalization → encoding → writing.
"""

from typing import Any, Optional

from .constants import DEFAULT_DELIMITER, DELIMITERS
from .encoders import encode_value
from .normalize import normalize_value
from .types import EncodeOptions, ResolvedEncodeOptions
from .writer import LineWriter


def encode(value: Any, options: Optional[EncodeOptions] = None) -> str:
    """Encode a value into TOON format.

    Args:
        value: The value to encode (must be JSON-serializable)
        options: Optional encoding options

    Returns:
        TOON-formatted string
    """
    normalized = normalize_value(value)
    resolved_options = resolve_options(options)
    writer = LineWriter(resolved_options.indent)
    encode_value(normalized, resolved_options, writer, 0)
    return writer.to_string()


def resolve_options(options: Optional[EncodeOptions]) -> ResolvedEncodeOptions:
    """Resolve encoding options with defaults.

    Args:
        options: Optional user-provided options

    Returns:
        Resolved options with defaults applied
    """
    if options is None:
        return ResolvedEncodeOptions()

    indent = options.get("indent", 2)
    delimiter = options.get("delimiter", DEFAULT_DELIMITER)
    length_marker = options.get("lengthMarker", False)

    # Resolve delimiter if it's a key
    if delimiter in DELIMITERS:
        delimiter = DELIMITERS[delimiter]

    return ResolvedEncodeOptions(indent=indent, delimiter=delimiter, length_marker=length_marker)
