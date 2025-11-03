"""Tests for complex encoding scenarios."""

from toon_format import encode


def test_encode_nested_object():
    """Test encoding nested objects."""
    data = {
        "user": {
            "id": 123,
            "name": "Alice",
            "address": {"city": "NYC", "zip": 10001},
        }
    }
    result = encode(data)
    expected = (
        "user:\n  id: 123\n  name: Alice\n  address:\n    city: NYC\n    zip: 10001"
    )
    assert result == expected


def test_encode_list_array():
    """Test encoding list array with expanded format."""
    data = {
        "items": [
            {"id": 1, "name": "A1"},
            {"id": 2, "name": "B2"},
        ]
    }
    result = encode(data)
    # Objects have the same structure, so should use tabular format
    assert "items[2]{id,name}:" in result
    assert "1,A1" in result
    assert "2,B2" in result


def test_encode_array_of_arrays():
    """Test encoding arrays of arrays."""
    data = {"matrix": [[1, 2, 3], [4, 5, 6]]}
    result = encode(data)
    assert "matrix[2]:" in result


def test_encode_mixed_array():
    """Test encoding mixed array."""
    data = {"values": [42, "hello", True]}
    result = encode(data)
    assert "values[3]:" in result


def test_encode_empty_object():
    """Test encoding empty object."""
    data = {"empty": {}}
    result = encode(data)
    assert result == "empty:"


def test_encode_empty_array():
    """Test encoding empty array."""
    data = {"items": []}
    result = encode(data)
    assert "items[0]:" in result


def test_encode_with_custom_indent():
    """Test encoding with custom indent."""
    data = {"a": {"b": 1}}
    result = encode(data, {"indent": 4})
    assert "    b: 1" in result


def test_encode_complex_nested():
    """Test encoding complex nested structure."""
    data = {
        "users": [
            {
                "id": 1,
                "profile": {"name": "Alice", "age": 30},
                "tags": ["admin", "user"],
            },
            {
                "id": 2,
                "profile": {"name": "Bob", "age": 25},
                "tags": ["user"],
            },
        ]
    }
    result = encode(data)
    assert "users" in result
    assert "profile" in result
    assert "tags" in result
