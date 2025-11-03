"""Tests for primitive value decoding."""

from toon_format import decode


def test_decode_null():
    """Test decoding null values."""
    toon_data = "value: null"
    result = decode(toon_data)
    expected = {"value": None}
    assert result == expected


def test_decode_boolean_true():
    """Test decoding boolean true."""
    toon_data = "active: true"
    result = decode(toon_data)
    expected = {"active": True}
    assert result == expected


def test_decode_boolean_false():
    """Test decoding boolean false."""
    toon_data = "active: false"
    result = decode(toon_data)
    expected = {"active": False}
    assert result == expected


def test_decode_integer():
    """Test decoding integer."""
    toon_data = "count: 42"
    result = decode(toon_data)
    expected = {"count": 42}
    assert result == expected


def test_decode_float():
    """Test decoding float."""
    toon_data = "price: 9.99"
    result = decode(toon_data)
    expected = {"price": 9.99}
    assert result == expected


def test_decode_negative_number():
    """Test decoding negative number."""
    toon_data = "temp: -10"
    result = decode(toon_data)
    expected = {"temp": -10}
    assert result == expected


def test_decode_scientific_notation():
    """Test decoding scientific notation."""
    toon_data = "value: 1.5e10"
    result = decode(toon_data)
    expected = {"value": 1.5e10}
    assert result == expected


def test_decode_zero():
    """Test decoding zero."""
    toon_data = "count: 0"
    result = decode(toon_data)
    expected = {"count": 0}
    assert result == expected


def test_decode_unquoted_string():
    """Test decoding unquoted string."""
    toon_data = "name: hello"
    result = decode(toon_data)
    expected = {"name": "hello"}
    assert result == expected


def test_decode_quoted_string():
    """Test decoding quoted string."""
    toon_data = 'name: "hello world"'
    result = decode(toon_data)
    expected = {"name": "hello world"}
    assert result == expected


def test_decode_string_with_special_chars():
    """Test decoding string with special characters."""
    toon_data = 'text: "hello, world: test"'
    result = decode(toon_data)
    expected = {"text": "hello, world: test"}
    assert result == expected


def test_decode_escaped_string():
    """Test decoding string with escape sequences."""
    toon_data = 'text: "hello\\nworld"'
    result = decode(toon_data)
    expected = {"text": "hello\nworld"}
    assert result == expected


def test_decode_quoted_key():
    """Test decoding object with quoted key."""
    toon_data = '"key with spaces": value'
    result = decode(toon_data)
    expected = {"key with spaces": "value"}
    assert result == expected


def test_decode_mixed_primitives_in_array():
    """Test decoding array with mixed primitive types."""
    toon_data = "values[5]: 1,2.5,true,false,null"
    result = decode(toon_data)
    expected = {"values": [1, 2.5, True, False, None]}
    assert result == expected
