"""Tests for round-trip encoding and decoding."""

from toon_format import decode, encode


def test_roundtrip_simple_object():
    """Test round-trip: encode then decode."""
    data = {"id": 123, "name": "Ada", "active": True}
    encoded = encode(data)
    decoded = decode(encoded)
    assert decoded == data


def test_roundtrip_nested_object():
    """Test round-trip with nested objects."""
    data = {
        "user": {
            "id": 123,
            "name": "Alice",
            "address": {"city": "NYC", "zip": 10001},
        }
    }
    encoded = encode(data)
    decoded = decode(encoded)
    assert decoded == data


def test_roundtrip_tabular_array():
    """Test round-trip with tabular array."""
    data = {
        "items": [
            {"sku": "A1", "qty": 2, "price": 9.99},
            {"sku": "B2", "qty": 1, "price": 14.5},
        ]
    }
    encoded = encode(data)
    decoded = decode(encoded)
    assert decoded == data


def test_roundtrip_primitive_array():
    """Test round-trip with primitive array."""
    data = {"tags": ["foo", "bar", "baz"]}
    encoded = encode(data)
    decoded = decode(encoded)
    assert decoded == data


def test_roundtrip_root_array():
    """Test round-trip with root-level array."""
    data = [1, 2, 3]
    encoded = encode(data)
    decoded = decode(encoded)
    assert decoded == data


def test_roundtrip_mixed_types():
    """Test round-trip with mixed value types."""
    data = {
        "string": "hello",
        "number": 42,
        "float": 3.14,
        "boolean": True,
        "null": None,
        "array": [1, 2, 3],
        "object": {"nested": "value"},
    }
    encoded = encode(data)
    decoded = decode(encoded)
    assert decoded == data


def test_roundtrip_empty_structures():
    """Test round-trip with empty structures."""
    data = {"empty_obj": {}, "empty_arr": []}
    encoded = encode(data)
    decoded = decode(encoded)
    assert decoded == data


def test_roundtrip_array_of_arrays():
    """Test round-trip with array of arrays."""
    data = {"matrix": [[1, 2, 3], [4, 5, 6]]}
    encoded = encode(data)
    decoded = decode(encoded)
    assert decoded == data


def test_roundtrip_with_options():
    """Test round-trip with encoding options."""
    data = {"tags": ["foo", "bar"]}
    encoded = encode(data, {"delimiter": "\t", "length_marker": "#"})
    decoded = decode(encoded, {"strict": False})
    assert decoded == data


def test_roundtrip_complex_nested():
    """Test round-trip with complex nested structure."""
    data = {
        "users": [
            {
                "id": 1,
                "profile": {"name": "Alice", "tags": ["admin"]},
            },
            {
                "id": 2,
                "profile": {"name": "Bob", "tags": ["user"]},
            },
        ]
    }
    encoded = encode(data)
    decoded = decode(encoded)
    assert decoded == data
