"""Tests for the TOON encoder."""

from toon_format import encode


def test_encode_simple_object():
    """Test encoding a simple object."""
    result = encode({"id": 123, "name": "Ada", "active": True})
    expected = "id: 123\nname: Ada\nactive: true"
    assert result == expected


def test_encode_array_of_objects():
    """Test encoding an array of uniform objects."""
    data = {
        "items": [
            {"sku": "A1", "qty": 2, "price": 9.99},
            {"sku": "B2", "qty": 1, "price": 14.5},
        ]
    }
    result = encode(data)
    expected = "items[2]{sku,qty,price}:\n  A1,2,9.99\n  B2,1,14.5"
    assert result == expected


def test_encode_with_tab_delimiter():
    """Test encoding with tab delimiter."""
    data = {"tags": ["foo", "bar", "baz"]}
    result = encode(data, {"delimiter": "\t"})
    expected = "tags[3\t]: foo\tbar\tbaz"
    assert result == expected


def test_encode_with_length_marker():
    """Test encoding with length marker."""
    data = {"tags": ["foo", "bar"]}
    result = encode(data, {"length_marker": "#"})
    expected = "tags[#2]: foo,bar"
    assert result == expected
