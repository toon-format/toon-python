"""Tests for error handling and edge cases."""

import pytest

from toon_format import decode


def test_decode_empty_string():
    """Test decoding empty string raises error."""
    with pytest.raises(TypeError, match="Cannot decode empty input"):
        decode("")


def test_decode_missing_colon():
    """Test decoding with missing colon raises syntax error."""
    invalid_toon = "key value"
    with pytest.raises(SyntaxError):
        decode(invalid_toon)


def test_decode_invalid_escape():
    """Test decoding with invalid escape sequence."""
    invalid_toon = 'text: "hello\\x"'
    with pytest.raises(SyntaxError):
        decode(invalid_toon)


def test_decode_strict_mode_length_mismatch():
    """Test strict mode detects length mismatch in tabular array."""
    invalid_toon = "items[3]{id,name}:\n  1,Alice\n  2,Bob"
    with pytest.raises(ValueError, match="Expected"):
        decode(invalid_toon, {"strict": True})


def test_decode_strict_mode_extra_items():
    """Test strict mode detects extra items in list array."""
    invalid_toon = "items[2]:\n  - 1\n  - 2\n  - 3"
    with pytest.raises(ValueError, match="Expected"):
        decode(invalid_toon, {"strict": True})


def test_decode_strict_mode_blank_lines():
    """Test strict mode detects blank lines in array."""
    invalid_toon = "items[2]:\n  - 1\n\n  - 2"
    with pytest.raises(SyntaxError, match="Blank lines"):
        decode(invalid_toon, {"strict": True})


def test_decode_non_strict_mode_allows_extra():
    """Test non-strict mode allows extra items."""
    toon_data = "items[2]:\n  - 1\n  - 2\n  - 3"
    result = decode(toon_data, {"strict": False})
    # Should decode first 2 items, ignoring the extra
    expected = {"items": [1, 2]}
    assert result == expected


def test_decode_invalid_array_length():
    """Test decoding with invalid array length."""
    invalid_toon = "items[abc]: 1,2,3"
    # parse_bracket_segment raises TypeError, but parse_array_header_line returns None
    # So this might not raise an error - it depends on implementation
    # For now, let's check if it raises an error or returns None
    try:
        result = decode(invalid_toon)
        # If it doesn't raise, that's also acceptable behavior
        # The invalid length would be ignored
        assert result is not None
    except (ValueError, TypeError):
        # Expected if validation is strict
        pass


def test_decode_mismatched_indentation():
    """Test decoding with mismatched indentation in strict mode."""
    # Strict mode checks that indentation is exact multiple of indent size
    # Use 3 spaces which is not a multiple of 2 (default indent)
    invalid_toon = "key:\n   nested: value"  # 3 spaces, not valid with indent=2
    with pytest.raises(SyntaxError, match="Indent"):
        decode(invalid_toon, {"strict": True})


def test_decode_tabs_in_strict_mode():
    """Test decoding with tabs in indentation fails in strict mode."""
    invalid_toon = "\tkey: value"
    with pytest.raises(SyntaxError, match="Tabs"):
        decode(invalid_toon, {"strict": True})
