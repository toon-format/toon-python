"""Encoders for different value types."""

from typing import List, Optional, cast

from .constants import LIST_ITEM_PREFIX
from .normalize import (
    is_array_of_arrays,
    is_array_of_objects,
    is_array_of_primitives,
    is_json_array,
    is_json_object,
    is_json_primitive,
)
from .primitives import encode_key, encode_primitive, format_header, join_encoded_values
from .types import (
    Depth,
    JsonArray,
    JsonObject,
    JsonPrimitive,
    JsonValue,
    ResolvedEncodeOptions,
)
from .writer import LineWriter


def encode_value(
    value: JsonValue,
    options: ResolvedEncodeOptions,
    writer: LineWriter,
    depth: Depth = 0,
) -> None:
    """Encode a value to TOON format.

    Args:
        value: Normalized JSON value
        options: Resolved encoding options
        writer: Line writer for output
        depth: Current indentation depth
    """
    if is_json_primitive(value):
        writer.push(depth, encode_primitive(cast(JsonPrimitive, value), options.delimiter))
    elif is_json_array(value):
        encode_array(cast(JsonArray, value), options, writer, depth, None)
    elif is_json_object(value):
        encode_object(cast(JsonObject, value), options, writer, depth, None)


def encode_object(
    obj: JsonObject,
    options: ResolvedEncodeOptions,
    writer: LineWriter,
    depth: Depth,
    key: Optional[str],
) -> None:
    """Encode an object to TOON format.

    Args:
        obj: Dictionary object
        options: Resolved encoding options
        writer: Line writer for output
        depth: Current indentation depth
        key: Optional key name
    """
    if key:
        writer.push(depth, f"{encode_key(key)}:")

    for obj_key, obj_value in obj.items():
        encode_key_value_pair(obj_key, obj_value, options, writer, depth if not key else depth + 1)


def encode_key_value_pair(
    key: str,
    value: JsonValue,
    options: ResolvedEncodeOptions,
    writer: LineWriter,
    depth: Depth,
) -> None:
    """Encode a key-value pair.

    Args:
        key: Key name
        value: Value to encode
        options: Resolved encoding options
        writer: Line writer for output
        depth: Current indentation depth
    """
    if is_json_primitive(value):
        primitive_str = encode_primitive(cast(JsonPrimitive, value), options.delimiter)
        writer.push(depth, f"{encode_key(key)}: {primitive_str}")
    elif is_json_array(value):
        encode_array(cast(JsonArray, value), options, writer, depth, key)
    elif is_json_object(value):
        encode_object(cast(JsonObject, value), options, writer, depth, key)


def encode_array(
    arr: JsonArray,
    options: ResolvedEncodeOptions,
    writer: LineWriter,
    depth: Depth,
    key: Optional[str],
) -> None:
    """Encode an array to TOON format.

    Args:
        arr: List array
        options: Resolved encoding options
        writer: Line writer for output
        depth: Current indentation depth
        key: Optional key name
    """
    # Handle empty array
    if not arr:
        header = format_header(key, 0, None, options.delimiter, options.lengthMarker)
        writer.push(depth, header)
        return

    # Check array type and encode accordingly
    if is_array_of_primitives(arr):
        encode_inline_primitive_array(arr, options, writer, depth, key)
    elif is_array_of_arrays(arr):
        encode_array_of_arrays(arr, options, writer, depth, key)
    elif is_array_of_objects(arr):
        tabular_header = detect_tabular_header(arr, options.delimiter)
        if tabular_header:
            encode_array_of_objects_as_tabular(arr, tabular_header, options, writer, depth, key)
        else:
            encode_mixed_array_as_list_items(arr, options, writer, depth, key)
    else:
        encode_mixed_array_as_list_items(arr, options, writer, depth, key)


def encode_inline_primitive_array(
    arr: JsonArray,
    options: ResolvedEncodeOptions,
    writer: LineWriter,
    depth: Depth,
    key: Optional[str],
) -> None:
    """Encode an array of primitives inline.

    Args:
        arr: Array of primitives
        options: Resolved encoding options
        writer: Line writer for output
        depth: Current indentation depth
        key: Optional key name
    """
    encoded_values = [encode_primitive(item, options.delimiter) for item in arr]
    joined = join_encoded_values(encoded_values, options.delimiter)
    header = format_header(key, len(arr), None, options.delimiter, options.lengthMarker)
    writer.push(depth, f"{header} {joined}")


def encode_array_of_arrays(
    arr: JsonArray,
    options: ResolvedEncodeOptions,
    writer: LineWriter,
    depth: Depth,
    key: Optional[str],
) -> None:
    """Encode an array of arrays.

    Args:
        arr: Array of arrays
        options: Resolved encoding options
        writer: Line writer for output
        depth: Current indentation depth
        key: Optional key name
    """
    header = format_header(key, len(arr), None, options.delimiter, options.lengthMarker)
    writer.push(depth, header)

    for item in arr:
        if is_array_of_primitives(item):
            encoded_values = [encode_primitive(v, options.delimiter) for v in item]
            joined = join_encoded_values(encoded_values, options.delimiter)
            length_marker = options.lengthMarker if options.lengthMarker else ""
            writer.push(
                depth + 1,
                f"{LIST_ITEM_PREFIX}[{length_marker}{len(item)}{options.delimiter}]: {joined}",
            )
        else:
            encode_array(item, options, writer, depth + 1, None)


def detect_tabular_header(arr: List[JsonObject], delimiter: str) -> Optional[List[str]]:
    """Detect if array can use tabular format and return header keys.

    Args:
        arr: Array of objects
        delimiter: Delimiter character

    Returns:
        List of keys if tabular, None otherwise
    """
    if not arr:
        return None

    # Get keys from first object
    first_keys = list(arr[0].keys())

    # Check all objects have same keys and all values are primitives
    for obj in arr:
        if list(obj.keys()) != first_keys:
            return None
        if not all(is_json_primitive(value) for value in obj.values()):
            return None

    return first_keys


def is_tabular_array(arr: List[JsonObject], delimiter: str) -> bool:
    """Check if array qualifies for tabular format.

    Args:
        arr: Array to check
        delimiter: Delimiter character

    Returns:
        True if tabular format can be used
    """
    return detect_tabular_header(arr, delimiter) is not None


def encode_array_of_objects_as_tabular(
    arr: List[JsonObject],
    fields: List[str],
    options: ResolvedEncodeOptions,
    writer: LineWriter,
    depth: Depth,
    key: Optional[str],
) -> None:
    """Encode array of uniform objects in tabular format.

    Args:
        arr: Array of uniform objects
        fields: Field names for header
        options: Resolved encoding options
        writer: Line writer for output
        depth: Current indentation depth
        key: Optional key name
    """
    header = format_header(key, len(arr), fields, options.delimiter, options.lengthMarker)
    writer.push(depth, header)

    for obj in arr:
        row_values = [encode_primitive(obj[field], options.delimiter) for field in fields]
        row = join_encoded_values(row_values, options.delimiter)
        writer.push(depth + 1, row)


def encode_mixed_array_as_list_items(
    arr: JsonArray,
    options: ResolvedEncodeOptions,
    writer: LineWriter,
    depth: Depth,
    key: Optional[str],
) -> None:
    """Encode mixed array as list items.

    Args:
        arr: Mixed array
        options: Resolved encoding options
        writer: Line writer for output
        depth: Current indentation depth
        key: Optional key name
    """
    header = format_header(key, len(arr), None, options.delimiter, options.lengthMarker)
    writer.push(depth, header)

    for item in arr:
        if is_json_primitive(item):
            writer.push(
                depth + 1,
                f"{LIST_ITEM_PREFIX}{encode_primitive(item, options.delimiter)}",
            )
        elif is_json_object(item):
            encode_object_as_list_item(item, options, writer, depth + 1)
        elif is_json_array(item):
            encode_array(item, options, writer, depth + 1, None)


def encode_object_as_list_item(
    obj: JsonObject, options: ResolvedEncodeOptions, writer: LineWriter, depth: Depth
) -> None:
    """Encode object as a list item.

    Args:
        obj: Object to encode
        options: Resolved encoding options
        writer: Line writer for output
        depth: Current indentation depth
    """
    # Get all keys
    keys = list(obj.items())
    if not keys:
        writer.push(depth, LIST_ITEM_PREFIX.rstrip())
        return

    # First key-value pair goes on same line as the "-"
    first_key, first_value = keys[0]
    if is_json_primitive(first_value):
        encoded_val = encode_primitive(first_value, options.delimiter)
        writer.push(depth, f"{LIST_ITEM_PREFIX}{encode_key(first_key)}: {encoded_val}")
    else:
        # If first value is not primitive, put "-" alone then encode normally
        writer.push(depth, LIST_ITEM_PREFIX.rstrip())
        encode_key_value_pair(first_key, first_value, options, writer, depth + 1)

    # Rest of the keys go normally indented
    for key, value in keys[1:]:
        encode_key_value_pair(key, value, options, writer, depth + 1)
