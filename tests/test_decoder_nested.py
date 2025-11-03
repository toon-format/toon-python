"""Tests for nested structures and complex decoding scenarios."""

from toon_format import decode


def test_decode_nested_object():
    """Test decoding nested objects."""
    toon_data = (
        "user:\n  id: 123\n  name: Alice\n  address:\n    city: NYC\n    zip: 10001"
    )
    result = decode(toon_data)
    expected = {
        "user": {
            "id": 123,
            "name": "Alice",
            "address": {"city": "NYC", "zip": 10001},
        }
    }
    assert result == expected


def test_decode_list_array_expanded():
    """Test decoding list array with expanded format (- markers)."""
    toon_data = "items[2]:\n  - id: 1\n    name: A1\n  - id: 2\n    name: B2"
    result = decode(toon_data)
    expected = {
        "items": [
            {"id": 1, "name": "A1"},
            {"id": 2, "name": "B2"},
        ]
    }
    assert result == expected


def test_decode_list_array_primitives():
    """Test decoding list array with primitive values."""
    toon_data = "tags[3]:\n  - foo\n  - bar\n  - baz"
    result = decode(toon_data)
    expected = {"tags": ["foo", "bar", "baz"]}
    assert result == expected


def test_decode_array_of_arrays():
    """Test decoding arrays of arrays."""
    toon_data = "matrix[2]:\n  - 1,2,3\n  - 4,5,6"
    result = decode(toon_data)
    expected = {"matrix": [[1, 2, 3], [4, 5, 6]]}
    assert result == expected


def test_decode_mixed_array():
    """Test decoding mixed array with different value types."""
    toon_data = 'values[3]:\n  - 42\n  - "hello"\n  - true'
    result = decode(toon_data)
    expected = {"values": [42, "hello", True]}
    assert result == expected


def test_decode_empty_object():
    """Test decoding empty object."""
    toon_data = "empty:"
    result = decode(toon_data)
    expected = {"empty": {}}
    assert result == expected


def test_decode_empty_array():
    """Test decoding empty array."""
    toon_data = "items[0]:"
    result = decode(toon_data)
    expected = {"items": []}
    assert result == expected


def test_decode_root_object():
    """Test decoding root-level object."""
    toon_data = "id: 123\nname: Alice"
    result = decode(toon_data)
    expected = {"id": 123, "name": "Alice"}
    assert result == expected


def test_decode_deeply_nested():
    """Test decoding deeply nested structures."""
    toon_data = "level1:\n  level2:\n    level3:\n      value: deep"
    result = decode(toon_data)
    expected = {"level1": {"level2": {"level3": {"value": "deep"}}}}
    assert result == expected


def test_decode_array_with_nested_objects():
    """Test decoding array containing nested objects."""
    toon_data = (
        "users[2]:\n"
        "  - id: 1\n"
        "    profile:\n"
        "      name: Alice\n"
        "  - id: 2\n"
        "    profile:\n"
        "      name: Bob"
    )
    result = decode(toon_data)
    expected = {
        "users": [
            {"id": 1, "profile": {"name": "Alice"}},
            {"id": 2, "profile": {"name": "Bob"}},
        ]
    }
    assert result == expected
