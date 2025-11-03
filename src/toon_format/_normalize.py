"""Normalization of Python types to JSON-compatible types."""

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from typing import Any, TypeGuard

from toon_format.types import JsonArray, JsonObject, JsonValue


def normalize_value(value: Any) -> JsonValue:
    """Normalize a Python value to a JSON-compatible type.

    Per Section 3 of the TOON specification (Encoding Normalization).

    Args:
        value: The value to normalize

    Returns:
        A normalized JSON-compatible value
    """
    # null
    if value is None:
        return None

    # Primitives
    if isinstance(value, (str, bool)):
        return value

    # Numbers: canonicalize -0 to 0, handle NaN and Infinity
    if isinstance(value, (int, float)):
        # Check for -0 (can't use == for this)
        if isinstance(value, float) and value == 0.0 and str(value)[0] == "-":
            return 0
        # Check for NaN or Infinity
        if isinstance(value, float) and not (-float("inf") < value < float("inf")):
            return None
        return value

    # Decimal → float or string
    if isinstance(value, Decimal):
        try:
            # Try to convert to float if it's in a reasonable range
            float_val = float(value)
            if -float("inf") < float_val < float("inf"):
                return float_val
        except (OverflowError, ValueError):
            pass
        # Otherwise convert to string (will be unquoted as it looks numeric)
        return str(value)

    # datetime → ISO string
    if isinstance(value, datetime):
        return value.isoformat()

    # Array
    if isinstance(value, (list, tuple)):
        return [normalize_value(item) for item in value]

    # Set/frozenset → array
    if isinstance(value, (set, frozenset)):
        return [normalize_value(item) for item in value]

    # Mapping (dict, etc.) → object
    if isinstance(value, Mapping):
        result: dict[str, JsonValue] = {}
        for key, val in value.items():
            result[str(key)] = normalize_value(val)
        return result

    # Fallback: other types → null
    return None


def is_json_primitive(value: Any) -> bool:
    """Check if a value is a JSON primitive.

    Args:
        value: The value to check

    Returns:
        True if the value is a JSON primitive
    """
    return value is None or isinstance(value, (str, int, float, bool))


def is_json_array(value: Any) -> bool:
    """Check if a value is a JSON array.

    Args:
        value: The value to check

    Returns:
        True if the value is a JSON array
    """
    return isinstance(value, list)


def is_json_object(value: Any) -> TypeGuard[JsonObject]:
    """Check if a value is a JSON object.

    Args:
        value: The value to check

    Returns:
        True if the value is a JSON object
    """
    return value is not None and isinstance(value, dict) and not isinstance(value, type)


def is_plain_dict(value: Any) -> bool:
    """Check if a value is a plain dict (not a custom dict subclass).

    Args:
        value: The value to check

    Returns:
        True if the value is a plain dict
    """
    if value is None or not isinstance(value, dict):
        return False
    return type(value) is dict


def is_array_of_primitives(value: JsonArray) -> bool:
    """Check if an array contains only primitives.

    Args:
        value: The array to check

    Returns:
        True if all items are primitives
    """
    return all(is_json_primitive(item) for item in value)


def is_array_of_arrays(value: JsonArray) -> bool:
    """Check if an array contains only arrays.

    Args:
        value: The array to check

    Returns:
        True if all items are arrays
    """
    return all(is_json_array(item) for item in value)


def is_array_of_objects(value: JsonArray) -> TypeGuard[list[JsonObject]]:
    """Check if an array contains only objects.

    Args:
        value: The array to check

    Returns:
        True if all items are objects
    """
    return all(is_json_object(item) for item in value)
