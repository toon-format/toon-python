"""Main encoding logic for TOON format."""

from typing import cast

from toon_format._constants import LIST_ITEM_MARKER
from toon_format._encode_primitives import (
    encode_and_join_primitives,
    encode_inline_array_line,
    encode_key,
    encode_primitive,
    format_header,
)
from toon_format._normalize import (
    is_array_of_arrays,
    is_array_of_objects,
    is_array_of_primitives,
    is_json_array,
    is_json_object,
    is_json_primitive,
)
from toon_format._writer import LineWriter
from toon_format.types import (
    JsonArray,
    JsonObject,
    JsonPrimitive,
    JsonValue,
    ResolvedEncodeOptions,
)


def encode_value(value: JsonValue, options: ResolvedEncodeOptions) -> str:
    """Encode a normalized JSON value to TOON format.

    Args:
        value: The value to encode
        options: Resolved encode options

    Returns:
        The TOON-formatted string
    """
    if is_json_primitive(value):
        return encode_primitive(cast(JsonPrimitive, value), options.delimiter)

    writer = LineWriter(options.indent)

    if is_json_array(value):
        encode_array(None, cast(JsonArray, value), writer, 0, options)
    elif is_json_object(value):
        encode_object(value, writer, 0, options)

    return str(writer)


def encode_object(
    value: JsonObject,
    writer: LineWriter,
    depth: int,
    options: ResolvedEncodeOptions,
) -> None:
    """Encode an object to TOON format.

    Args:
        value: The object to encode
        writer: The line writer
        depth: The current depth
        options: Encode options
    """
    keys = list(value.keys())

    for key in keys:
        encode_key_value_pair(key, value[key], writer, depth, options)


def encode_key_value_pair(
    key: str,
    value: JsonValue,
    writer: LineWriter,
    depth: int,
    options: ResolvedEncodeOptions,
) -> None:
    """Encode a key-value pair.

    Args:
        key: The key
        value: The value
        writer: The line writer
        depth: The current depth
        options: Encode options
    """
    encoded_key = encode_key(key)

    if is_json_primitive(value):
        primitive_value = encode_primitive(
            cast(JsonPrimitive, value),
            options.delimiter,
        )
        writer.push(depth, f"{encoded_key}: {primitive_value}")
    elif is_json_array(value):
        encode_array(key, cast(JsonArray, value), writer, depth, options)
    elif is_json_object(value):
        nested_keys = list(value.keys())
        if len(nested_keys) == 0:
            # Empty object
            writer.push(depth, f"{encoded_key}:")
        else:
            writer.push(depth, f"{encoded_key}:")
            encode_object(value, writer, depth + 1, options)


def encode_array(
    key: str | None,
    value: JsonArray,
    writer: LineWriter,
    depth: int,
    options: ResolvedEncodeOptions,
) -> None:
    """Encode an array to TOON format.

    Args:
        key: Optional key name
        value: The array to encode
        writer: The line writer
        depth: The current depth
        options: Encode options
    """
    if len(value) == 0:
        header = format_header(
            0,
            key=key,
            delimiter=options.delimiter,
            length_marker=options.length_marker,
        )
        writer.push(depth, header)
        return

    # Primitive array
    if is_array_of_primitives(value):
        # Type narrowing: is_array_of_primitives ensures all items are JsonPrimitive
        primitives = cast(list[JsonPrimitive], value)
        formatted = encode_inline_array_line(
            primitives,
            options.delimiter,
            key,
            options.length_marker,
        )
        writer.push(depth, formatted)
        return

    # Array of arrays (all primitives)
    if is_array_of_arrays(value):
        all_primitive_arrays = all(
            is_array_of_primitives(cast(JsonArray, arr)) for arr in value
        )
        if all_primitive_arrays:
            arrays = cast(list[JsonArray], value)
            encode_array_of_arrays_as_list_items(key, arrays, writer, depth, options)
            return

    # Array of objects
    if is_array_of_objects(value):
        objects = value
        header_fields = extract_tabular_header(objects)
        if header_fields:
            encode_array_of_objects_as_tabular(
                key,
                objects,
                header_fields,
                writer,
                depth,
                options,
            )
        else:
            # Cast list[JsonObject] to JsonArray for the function signature
            encode_mixed_array_as_list_items(
                key,
                cast(JsonArray, value),
                writer,
                depth,
                options,
            )
        return

    # Mixed array: fallback to expanded format
    encode_mixed_array_as_list_items(key, value, writer, depth, options)


def encode_array_of_arrays_as_list_items(
    prefix: str | None,
    values: list[JsonArray],
    writer: LineWriter,
    depth: int,
    options: ResolvedEncodeOptions,
) -> None:
    """Encode an array of arrays as expanded list items.

    Args:
        prefix: Optional key prefix
        values: List of arrays
        writer: The line writer
        depth: The current depth
        options: Encode options
    """
    header = format_header(
        len(values),
        key=prefix,
        delimiter=options.delimiter,
        length_marker=options.length_marker,
    )
    writer.push(depth, header)

    for arr in values:
        if is_array_of_primitives(arr):
            primitives = cast(list[JsonPrimitive], arr)
            inline = encode_inline_array_line(
                primitives,
                options.delimiter,
                None,
                options.length_marker,
            )
            writer.push_list_item(depth + 1, inline)


def encode_array_of_objects_as_tabular(
    prefix: str | None,
    rows: list[JsonObject],
    header: list[str],
    writer: LineWriter,
    depth: int,
    options: ResolvedEncodeOptions,
) -> None:
    """Encode an array of objects in tabular format.

    Args:
        prefix: Optional key prefix
        rows: List of objects (rows)
        header: List of field names
        writer: The line writer
        depth: The current depth
        options: Encode options
    """
    formatted_header = format_header(
        len(rows),
        key=prefix,
        fields=header,
        delimiter=options.delimiter,
        length_marker=options.length_marker,
    )
    writer.push(depth, formatted_header)

    write_tabular_rows(rows, header, writer, depth + 1, options)


def extract_tabular_header(rows: list[JsonObject]) -> list[str] | None:
    """Extract tabular header from rows if all rows match pattern.

    Args:
        rows: List of objects to check

    Returns:
        List of field names if tabular, None otherwise
    """
    if len(rows) == 0:
        return None

    first_row = rows[0]
    first_keys = list(first_row.keys())
    if len(first_keys) == 0:
        return None

    if is_tabular_array(rows, first_keys):
        return first_keys

    return None


def is_tabular_array(rows: list[JsonObject], header: list[str]) -> bool:
    """Check if rows form a valid tabular array.

    Args:
        rows: List of objects
        header: List of expected field names

    Returns:
        True if all rows match the header pattern
    """
    for row in rows:
        keys = list(row.keys())

        # All objects must have the same keys (but order can differ)
        if len(keys) != len(header):
            return False

        # Check that all header keys exist in the row and all values are primitives
        for key in header:
            if key not in row:
                return False
            if not is_json_primitive(row[key]):
                return False

    return True


def write_tabular_rows(
    rows: list[JsonObject],
    header: list[str],
    writer: LineWriter,
    depth: int,
    options: ResolvedEncodeOptions,
) -> None:
    """Write tabular rows.

    Args:
        rows: List of objects
        header: List of field names
        writer: The line writer
        depth: The current depth
        options: Encode options
    """
    for row in rows:
        values = [row[key] for key in header]
        # All values in tabular arrays are primitives by definition
        primitives: list[JsonPrimitive] = [v for v in values if is_json_primitive(v)]  # type: ignore[misc]
        joined_value = encode_and_join_primitives(primitives, options.delimiter)
        writer.push(depth, joined_value)


def encode_mixed_array_as_list_items(
    prefix: str | None,
    items: list[JsonValue],
    writer: LineWriter,
    depth: int,
    options: ResolvedEncodeOptions,
) -> None:
    """Encode a mixed array as expanded list items.

    Args:
        prefix: Optional key prefix
        items: List of values
        writer: The line writer
        depth: The current depth
        options: Encode options
    """
    header = format_header(
        len(items),
        key=prefix,
        delimiter=options.delimiter,
        length_marker=options.length_marker,
    )
    writer.push(depth, header)

    for item in items:
        encode_list_item_value(item, writer, depth + 1, options)


def encode_object_as_list_item(
    obj: JsonObject,
    writer: LineWriter,
    depth: int,
    options: ResolvedEncodeOptions,
) -> None:
    """Encode an object as a list item.

    Args:
        obj: The object to encode
        writer: The line writer
        depth: The current depth
        options: Encode options
    """
    keys = list(obj.keys())
    if len(keys) == 0:
        writer.push(depth, LIST_ITEM_MARKER)
        return

    # First key-value on the same line as "- "
    first_key = keys[0]
    encoded_key = encode_key(first_key)
    first_value = obj[first_key]

    if is_json_primitive(first_value):
        primitive_val = cast(JsonPrimitive, first_value)
        writer.push_list_item(
            depth,
            f"{encoded_key}: {encode_primitive(primitive_val, options.delimiter)}",
        )
    elif is_json_array(first_value):
        array_val = cast(JsonArray, first_value)
        if is_array_of_primitives(array_val):
            # Inline format for primitive arrays
            primitives = cast(list[JsonPrimitive], array_val)
            formatted = encode_inline_array_line(
                primitives,
                options.delimiter,
                first_key,
                options.length_marker,
            )
            writer.push_list_item(depth, formatted)
        elif is_array_of_objects(array_val):
            # Check if array of objects can use tabular format
            objects_list = array_val
            header = extract_tabular_header(objects_list)
            if header:
                # Tabular format for uniform arrays of objects
                formatted_header = format_header(
                    len(array_val),
                    key=first_key,
                    fields=header,
                    delimiter=options.delimiter,
                    length_marker=options.length_marker,
                )
                writer.push_list_item(depth, formatted_header)
                write_tabular_rows(objects_list, header, writer, depth + 1, options)
            else:
                # Fall back to list format for non-uniform arrays of objects
                writer.push_list_item(depth, f"{encoded_key}[{len(array_val)}]:")
                for obj_item in objects_list:
                    encode_object_as_list_item(obj_item, writer, depth + 1, options)
        else:
            # Complex arrays on separate lines (array of arrays, etc.)
            writer.push_list_item(depth, f"{encoded_key}[{len(array_val)}]:")

            # Encode array contents at depth + 1
            for item in array_val:
                encode_list_item_value(item, writer, depth + 1, options)
    elif is_json_object(first_value):
        nested_keys = list(first_value.keys())
        if len(nested_keys) == 0:
            writer.push_list_item(depth, f"{encoded_key}:")
        else:
            writer.push_list_item(depth, f"{encoded_key}:")
            encode_object(first_value, writer, depth + 2, options)

    # Remaining keys on indented lines
    for i in range(1, len(keys)):
        key = keys[i]
        encode_key_value_pair(key, obj[key], writer, depth + 1, options)


def encode_list_item_value(
    value: JsonValue,
    writer: LineWriter,
    depth: int,
    options: ResolvedEncodeOptions,
) -> None:
    """Encode a value as a list item.

    Args:
        value: The value to encode
        writer: The line writer
        depth: The current depth
        options: Encode options
    """
    if is_json_primitive(value):
        primitive_val = cast(JsonPrimitive, value)
        writer.push_list_item(depth, encode_primitive(primitive_val, options.delimiter))
    elif is_json_array(value):
        array_val = cast(JsonArray, value)
        if is_array_of_primitives(array_val):
            primitives = cast(list[JsonPrimitive], array_val)
            inline = encode_inline_array_line(
                primitives,
                options.delimiter,
                None,
                options.length_marker,
            )
            writer.push_list_item(depth, inline)
        else:
            # Complex array - encode as list items
            header = format_header(
                len(array_val),
                key=None,
                delimiter=options.delimiter,
                length_marker=options.length_marker,
            )
            writer.push_list_item(depth, header)
            for item_val in array_val:
                encode_list_item_value(item_val, writer, depth + 1, options)
    elif is_json_object(value):
        encode_object_as_list_item(value, writer, depth, options)
