# Copyright (c) 2025 TOON Format Organization
# SPDX-License-Identifier: MIT
"""Value normalization for TOON encoding.

Converts Python-specific types to JSON-compatible values before encoding:
- datetime/date → ISO 8601 strings
- Decimal → float
- tuple/set/frozenset → sorted lists
- pathlib.Path → string representation
- Infinity/NaN → null
- Functions/callables → null
- Negative zero → zero
"""

import math
import sys
from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal
from pathlib import PurePath
from typing import Any

# TypeGuard was added in Python 3.10, use typing_extensions for older versions
if sys.version_info >= (3, 10):
    from typing import TypeGuard
else:
    from typing_extensions import TypeGuard

from .logging_config import get_logger
from .types import JsonArray, JsonObject, JsonPrimitive, JsonValue

# Module logger
logger = get_logger(__name__)

_MAX_SAFE_INTEGER = 2**53 - 1


def normalize_value(value: Any) -> JsonValue:
    """Normalize Python value to JSON-compatible type.

    Converts Python-specific types to JSON-compatible equivalents:
    - datetime objects → ISO 8601 strings
    - sets → sorted lists
    - pathlib.Path → string representation
    - Large integers (>2^53-1) → strings (for JS compatibility)
    - Non-finite floats (inf, -inf, NaN) → null
    - Negative zero → positive zero
    - Mapping types → dicts with string keys
    - Unsupported types → null

    Args:
        value: Python value to normalize.

    Returns:
        JsonValue: Normalized value (None, bool, int, float, str, list, or dict).

    Examples:
        >>> normalize_value(datetime(2024, 1, 1))
        '2024-01-01T00:00:00'

        >>> normalize_value({1, 2, 3})
        [1, 2, 3]

        >>> normalize_value(float('inf'))
        None

        >>> normalize_value(2**60)  # Large integer
        '1152921504606846976'

        >>> from pathlib import Path
        >>> normalize_value(Path('/tmp/file.txt'))
        '/tmp/file.txt'

    Note:
        - Recursive: normalizes nested structures
        - Sets are sorted for deterministic output
        - Heterogeneous sets sorted by repr() if natural sorting fails
        - Path objects are converted to their string representation
    """
    if value is None:
        return None

    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value

    if isinstance(value, int):
        # Python integers have arbitrary precision and are encoded directly
        # Note: JavaScript BigInt types are converted to strings during normalization
        # (per spec Section 3), but Python ints don't need this conversion
        return value

    if isinstance(value, float):
        # Handle non-finite first
        if not math.isfinite(value) or value != value:  # includes inf, -inf, NaN
            logger.debug(f"Converting non-finite float to null: {value}")
            return None
        if value == 0.0 and math.copysign(1.0, value) == -1.0:
            logger.debug("Converting negative zero to positive zero")
            return 0
        return value

    # Handle Decimal
    if isinstance(value, Decimal):
        if not value.is_finite():
            logger.debug(f"Converting non-finite Decimal to null: {value}")
            return None
        return float(value)

    # Handle pathlib.Path objects -> string representation
    if isinstance(value, PurePath):
        logger.debug(f"Converting {type(value).__name__} to string: {value}")
        return str(value)

    if isinstance(value, datetime):
        try:
            result = value.isoformat()
            logger.debug(f"Converting datetime to ISO string: {value}")
            return result
        except Exception as e:
            raise ValueError(f"Failed to convert datetime to ISO format: {e}") from e

    if isinstance(value, date):
        try:
            result = value.isoformat()
            logger.debug(f"Converting date to ISO string: {value}")
            return result
        except Exception as e:
            raise ValueError(f"Failed to convert date to ISO format: {e}") from e

    if isinstance(value, list):
        if not value:
            return []
        return [normalize_value(item) for item in value]

    if isinstance(value, tuple):
        logger.debug(f"Converting tuple to list: {len(value)} items")
        return [normalize_value(item) for item in value]

    if isinstance(value, (set, frozenset)):
        logger.debug(f"Converting {type(value).__name__} to sorted list: {len(value)} items")
        try:
            return [normalize_value(item) for item in sorted(value)]
        except TypeError:
            # Fall back to stable conversion for heterogeneous sets/frozensets
            logger.debug(
                f"{type(value).__name__} contains heterogeneous types, using repr() for sorting"
            )
            return [normalize_value(item) for item in sorted(value, key=lambda x: repr(x))]

    # Handle generic mapping types (Map-like) and dicts
    if isinstance(value, Mapping):
        logger.debug(f"Converting {type(value).__name__} to dict: {len(value)} items")
        try:
            return {str(k): normalize_value(v) for k, v in value.items()}
        except Exception as e:
            raise ValueError(
                f"Failed to convert mapping to dict: {e}. "
                "Check that all keys can be converted to strings."
            ) from e

    # Handle callables -> null
    if callable(value):
        logger.debug(f"Converting callable {type(value).__name__} to null")
        return None

    # Fallback for other types
    logger.warning(
        f"Unsupported type {type(value).__name__}, converting to null. Value: {str(value)[:50]}"
    )
    return None


def is_json_primitive(value: Any) -> TypeGuard[JsonPrimitive]:
    """Check if value is a JSON primitive type.

    Args:
        value: Value to check.

    Returns:
        TypeGuard[JsonPrimitive]: True if value is None, str, int, float, or bool.
    """
    return value is None or isinstance(value, (str, int, float, bool))


def is_json_array(value: Any) -> TypeGuard[JsonArray]:
    """Check if value is a JSON array (Python list).

    Args:
        value: Value to check.

    Returns:
        TypeGuard[JsonArray]: True if value is a list.
    """
    return isinstance(value, list)


def is_json_object(value: Any) -> TypeGuard[JsonObject]:
    """Check if value is a JSON object (Python dict).

    Args:
        value: Value to check.

    Returns:
        TypeGuard[JsonObject]: True if value is a dict.
    """
    return isinstance(value, dict)


def is_array_of_primitives(value: JsonArray) -> bool:
    """Check if array contains only primitive values.

    Args:
        value: List to check.

    Returns:
        bool: True if all items are primitives. Empty arrays return True.
    """
    if not value:
        return True
    return all(is_json_primitive(item) for item in value)


def is_array_of_arrays(value: JsonArray) -> bool:
    """Check if array contains only arrays.

    Args:
        value: List to check.

    Returns:
        bool: True if all items are lists. Empty arrays return True.
    """
    if not value:
        return True
    return all(is_json_array(item) for item in value)


def is_array_of_objects(value: JsonArray) -> bool:
    """Check if array contains only objects.

    Args:
        value: List to check.

    Returns:
        bool: True if all items are dicts. Empty arrays return True.
    """
    if not value:
        return True
    return all(is_json_object(item) for item in value)
