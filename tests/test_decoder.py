"""Tests for the TOON decoder."""

import pytest

from toon_format import decode


def test_decode_simple_object():
    """Test decoding a simple object."""
    toon_data = "id: 123\nname: Ada\nactive: true"
    result = decode(toon_data)
    expected = {"id": 123, "name": "Ada", "active": True}
    assert result == expected


def test_decode_array_of_objects():
    """Test decoding a tabular array."""
    toon_data = "items[2]{sku,qty,price}:\n  A1,2,9.99\n  B2,1,14.5"
    result = decode(toon_data)
    expected = {
        "items": [
            {"sku": "A1", "qty": 2, "price": 9.99},
            {"sku": "B2", "qty": 1, "price": 14.5},
        ]
    }
    assert result == expected


def test_decode_primitive_array():
    """Test decoding a primitive array."""
    toon_data = "tags[3]: foo,bar,baz"
    result = decode(toon_data)
    expected = {"tags": ["foo", "bar", "baz"]}
    assert result == expected


def test_decode_root_array():
    """Test decoding a root-level array."""
    toon_data = "[3]: 1,2,3"
    result = decode(toon_data)
    expected = [1, 2, 3]
    assert result == expected


def test_decode_strict_mode():
    """Test that strict mode validates input."""
    invalid_toon = "items[3]{id,name}:\n  1,Alice\n  2,Bob"  # Length mismatch
    with pytest.raises(ValueError, match="Expected"):
        decode(invalid_toon, {"strict": True})
