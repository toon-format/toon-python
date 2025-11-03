"""Main decoding logic for TOON format."""

from typing import cast

from toon_format._constants import COLON, DEFAULT_DELIMITER, LIST_ITEM_PREFIX
from toon_format._decode_validation import (
    assert_expected_count,
    validate_no_blank_lines_in_range,
    validate_no_extra_list_items,
    validate_no_extra_tabular_rows,
)
from toon_format._literal_utils import is_boolean_or_null_literal, is_numeric_literal
from toon_format._parser import (
    ArrayHeaderInfo,
    is_array_header_after_hyphen,
    is_object_first_field_after_hyphen,
    map_row_values_to_primitives,
    parse_array_header_line,
    parse_delimited_values,
    parse_key_token,
    parse_primitive_token,
)
from toon_format._scanner import LineCursor, ParsedLine
from toon_format._string_utils import find_closing_quote
from toon_format.types import JsonArray, JsonObject, JsonValue, ResolvedDecodeOptions


def decode_value_from_lines(
    cursor: LineCursor,
    options: ResolvedDecodeOptions,
) -> JsonValue:
    """Decode a value from parsed lines (entry point).

    Args:
        cursor: The line cursor positioned at the start
        options: Resolved decode options

    Returns:
        The decoded JSON value

    Raises:
        ReferenceError: If there's no content to decode
    """
    first = cursor.peek()
    if not first:
        raise ReferenceError("No content to decode")

    if is_array_header_after_hyphen(first.content):
        header_info = parse_array_header_line(first.content, DEFAULT_DELIMITER)
        if header_info:
            cursor.advance()  # Move past the header line
            return decode_array_from_header(
                header_info[0],
                header_info[1],
                cursor,
                0,
                options,
            )

    # Check for single primitive value
    if cursor.length == 1 and not _is_key_value_line(first):
        content = first.content.strip()
        # Check for ambiguous line that looks like key-value but lacks colon
        if (
            (" " in content)
            and not content.startswith('"')
            and not content.startswith("-")
            and "\n" not in content
        ):
            if not (is_boolean_or_null_literal(content) or is_numeric_literal(content)):
                raise SyntaxError(f"Expected colon in key-value pair: {content}")
        return parse_primitive_token(content)

    # Default to object
    return decode_object(cursor, 0, options)


def _is_key_value_line(line: ParsedLine) -> bool:
    """Check if a line is a key-value line.

    Args:
        line: The parsed line

    Returns:
        True if the line is a key-value line
    """
    content = line.content
    # Look for unquoted colon or quoted key followed by colon
    if content.startswith('"'):
        # Quoted key - find the closing quote
        closing_quote_index = find_closing_quote(content, 0)
        if closing_quote_index == -1:
            return False
        # Check if colon exists after quoted key (may have array/brace syntax between)
        return COLON in content[closing_quote_index + 1 :]
    else:
        # Unquoted key - look for first colon not inside quotes
        return COLON in content


def decode_object(
    cursor: LineCursor,
    base_depth: int,
    options: ResolvedDecodeOptions,
) -> JsonObject:
    """Decode an object from the cursor.

    Args:
        cursor: The line cursor
        base_depth: The base depth for object fields
        options: Decode options

    Returns:
        The decoded object

    Raises:
        SyntaxError: If a line doesn't have a colon (required for object fields)
    """
    obj: JsonObject = {}

    # Detect the actual depth of the first field
    computed_depth: int | None = None

    while not cursor.at_end():
        line = cursor.peek()
        if not line or line.depth < base_depth:
            break

        if computed_depth is None and line.depth >= base_depth:
            computed_depth = line.depth

        if line.depth == computed_depth:
            # Validate that object fields have colons
            if not _is_key_value_line(line):
                raise SyntaxError(f"Expected colon in object field: {line.content}")
            key, value = decode_key_value_pair(line, cursor, computed_depth, options)
            obj[key] = value
        else:
            # Different depth (shallower or deeper) - stop object parsing
            break

    return obj


def decode_key_value(
    content: str,
    cursor: LineCursor,
    base_depth: int,
    options: ResolvedDecodeOptions,
) -> tuple[str, JsonValue, int]:
    """Decode a key-value pair from content.

    Args:
        content: The line content
        cursor: The line cursor
        base_depth: The base depth
        options: Decode options

    Returns:
        A Tuple of (key, value, follow_depth)

    Raises:
        SyntaxError: If the content doesn't contain a colon
    """
    # Validate that content has a colon
    if COLON not in content:
        raise SyntaxError(f"Expected colon in key-value pair: {content}")

    # Check for array header first (before parsing key)
    array_header = parse_array_header_line(content, DEFAULT_DELIMITER)
    if array_header and array_header[0].key:
        value = decode_array_from_header(
            array_header[0],
            array_header[1],
            cursor,
            base_depth,
            options,
        )
        return (array_header[0].key, value, base_depth + 1)

    # Regular key-value pair
    key, end = parse_key_token(content, 0)
    rest = content[end:].strip()

    # No value after colon - expect nested object or empty
    if not rest:
        next_line = cursor.peek()
        if next_line and next_line.depth > base_depth:
            nested = decode_object(cursor, base_depth + 1, options)
            return (key, nested, base_depth + 1)
        # Empty object
        return (key, {}, base_depth + 1)

    # Inline primitive value
    primitive_val = parse_primitive_token(rest)
    return (key, primitive_val, base_depth + 1)


def decode_key_value_pair(
    line: ParsedLine,
    cursor: LineCursor,
    base_depth: int,
    options: ResolvedDecodeOptions,
) -> tuple[str, JsonValue]:
    """Decode a key-value pair from a line.

    Args:
        line: The parsed line
        cursor: The line cursor
        base_depth: The base depth
        options: Decode options

    Returns:
        A Tuple of (key, value)
    """
    cursor.advance()
    key, value, _follow_depth = decode_key_value(
        line.content,
        cursor,
        base_depth,
        options,
    )
    return (key, value)


def decode_array_from_header(
    header: ArrayHeaderInfo,
    inline_values: str | None,
    cursor: LineCursor,
    base_depth: int,
    options: ResolvedDecodeOptions,
) -> JsonArray:
    """Decode an array from its header.

    Args:
        header: The array header information
        inline_values: Optional inline values after the header
        cursor: The line cursor
        base_depth: The base depth
        options: Decode options

    Returns:
        The decoded array
    """
    # Inline primitive array
    if inline_values:
        # For inline arrays, cursor should already be advanced or will be by caller
        return decode_inline_primitive_array(header, inline_values, options)

    # Tabular array
    if header.fields and len(header.fields) > 0:
        return decode_tabular_array(header, cursor, base_depth, options)

    # List array
    return decode_list_array(header, cursor, base_depth, options)


def decode_inline_primitive_array(
    header: ArrayHeaderInfo,
    inline_values: str,
    options: ResolvedDecodeOptions,
) -> JsonArray:
    """Decode an inline primitive array.

    Args:
        header: The array header
        inline_values: The inline values string
        options: Decode options

    Returns:
        List of primitives (as JsonArray)
    """
    if not inline_values.strip():
        assert_expected_count(0, header.length, "inline array items", options)
        return []

    values = parse_delimited_values(inline_values, header.delimiter)
    primitives = map_row_values_to_primitives(values)

    assert_expected_count(len(primitives), header.length, "inline array items", options)

    return cast(JsonArray, primitives)


def decode_list_array(
    header: ArrayHeaderInfo,
    cursor: LineCursor,
    base_depth: int,
    options: ResolvedDecodeOptions,
) -> list[JsonValue]:
    """Decode a list array (expanded format).

    Args:
        header: The array header
        cursor: The line cursor
        base_depth: The base depth
        options: Decode options

    Returns:
        List of decoded values
    """
    items: list[JsonValue] = []
    item_depth = base_depth + 1

    # Track line range for blank line validation
    start_line: int | None = None
    end_line: int | None = None

    while not cursor.at_end() and len(items) < header.length:
        line = cursor.peek()
        if not line or line.depth < item_depth:
            break

        # Check for list item (with or without space after hyphen)
        is_list_item = line.content.startswith(LIST_ITEM_PREFIX) or line.content == "-"

        if line.depth == item_depth and is_list_item:
            # Track first and last item line numbers
            if start_line is None:
                start_line = line.line_num
            end_line = line.line_num

            item = decode_list_item(cursor, item_depth, options)
            items.append(item)

            # Update endLine to the current cursor position (after item was decoded)
            current_line = cursor.current()
            if current_line:
                end_line = current_line.line_num
        else:
            break

    assert_expected_count(len(items), header.length, "list array items", options)

    # In strict mode, check for blank lines inside the array
    if options.strict and start_line is not None and end_line is not None:
        validate_no_blank_lines_in_range(
            start_line,
            end_line,
            cursor.get_blank_lines(),
            options.strict,
            "list array",
        )

    # In strict mode, check for extra items
    if options.strict:
        validate_no_extra_list_items(cursor, item_depth, header.length)

    return items


def decode_tabular_array(
    header: ArrayHeaderInfo,
    cursor: LineCursor,
    base_depth: int,
    options: ResolvedDecodeOptions,
) -> JsonArray:
    """Decode a tabular array.

    Args:
        header: The array header with fields
        cursor: The line cursor
        base_depth: The base depth
        options: Decode options

    Returns:
        List of decoded objects
    """
    objects: list[JsonObject] = []
    row_depth = base_depth + 1

    # Track line range for blank line validation
    start_line: int | None = None
    end_line: int | None = None

    while not cursor.at_end() and len(objects) < header.length:
        line = cursor.peek()
        if not line or line.depth < row_depth:
            break

        if line.depth == row_depth:
            # Track first and last row line numbers
            if start_line is None:
                start_line = line.line_num
            end_line = line.line_num

            cursor.advance()
            values = parse_delimited_values(line.content, header.delimiter)
            assert_expected_count(
                len(values),
                len(header.fields) if header.fields else 0,
                "tabular row values",
                options,
            )

            primitives = map_row_values_to_primitives(values)
            obj: JsonObject = {}

            if header.fields:
                for i, field in enumerate(header.fields):
                    if i < len(primitives):
                        obj[field] = primitives[i]

            objects.append(obj)
        else:
            break

    assert_expected_count(len(objects), header.length, "tabular rows", options)

    # In strict mode, check for blank lines inside the array
    if options.strict and start_line is not None and end_line is not None:
        validate_no_blank_lines_in_range(
            start_line,
            end_line,
            cursor.get_blank_lines(),
            options.strict,
            "tabular array",
        )

    # In strict mode, check for extra rows
    if options.strict:
        validate_no_extra_tabular_rows(cursor, row_depth, header)

    return cast(JsonArray, objects)


def decode_list_item(
    cursor: LineCursor,
    base_depth: int,
    options: ResolvedDecodeOptions,
) -> JsonValue:
    """Decode a list item.

    Args:
        cursor: The line cursor
        base_depth: The base depth
        options: Decode options

    Returns:
        The decoded value

    Raises:
        ReferenceError: If no list item is found
        SyntaxError: If the list item is malformed
    """
    line = cursor.next()
    if not line:
        raise ReferenceError("Expected list item")

    # Check for list item (with or without space after hyphen)
    after_hyphen: str

    # Empty list item should be an empty object
    if line.content == "-":
        return {}

    if line.content.startswith(LIST_ITEM_PREFIX):
        after_hyphen = line.content[len(LIST_ITEM_PREFIX) :]
    else:
        raise SyntaxError(f'Expected list item to start with "{LIST_ITEM_PREFIX}"')

    # Empty content after list item should also be an empty object
    if not after_hyphen.strip():
        return {}

    # Check for array header after hyphen
    if is_array_header_after_hyphen(after_hyphen):
        array_header = parse_array_header_line(after_hyphen, DEFAULT_DELIMITER)
        if array_header:
            return decode_array_from_header(
                array_header[0],
                array_header[1],
                cursor,
                base_depth,
                options,
            )

    # Check for object first field after hyphen
    if is_object_first_field_after_hyphen(after_hyphen):
        return decode_object_from_list_item(
            line,
            cursor,
            base_depth,
            options,
        )

    # Check if the content is comma-separated values (should be parsed as inline array)
    if DEFAULT_DELIMITER in after_hyphen:
        # Parse as delimited values and convert to array
        values = parse_delimited_values(after_hyphen, DEFAULT_DELIMITER)
        primitives = map_row_values_to_primitives(values)
        return cast(JsonArray, primitives)

    # Primitive value
    return parse_primitive_token(after_hyphen)


def decode_object_from_list_item(
    first_line: ParsedLine,
    cursor: LineCursor,
    base_depth: int,
    options: ResolvedDecodeOptions,
) -> JsonObject:
    """Decode an object from a list item.

    Args:
        first_line: The first line of the list item
        cursor: The line cursor
        base_depth: The base depth
        options: Decode options

    Returns:
        The decoded object
    """
    after_hyphen = first_line.content[len(LIST_ITEM_PREFIX) :]
    key, value, follow_depth = decode_key_value(
        after_hyphen,
        cursor,
        base_depth,
        options,
    )

    obj: JsonObject = {key: value}

    # Read subsequent fields
    while not cursor.at_end():
        line = cursor.peek()
        if not line or line.depth < follow_depth:
            break

        if line.depth == follow_depth and not line.content.startswith(LIST_ITEM_PREFIX):
            k, v = decode_key_value_pair(line, cursor, follow_depth, options)
            obj[k] = v
        else:
            break

    return obj
