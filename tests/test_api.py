"""Tests for Python-specific TOON API behavior.

This module tests the Python implementation's API surface, including:
- Options handling (EncodeOptions, DecodeOptions)
- Error handling and exception types
- Error message quality and clarity
- API edge cases and validation

Spec compliance is tested in test_spec_fixtures.py using official fixtures.
Python type normalization is tested in test_normalization.py.
"""

import pytest

from toon_format import ToonDecodeError, decode, encode
from toon_format.types import DecodeOptions, EncodeOptions


class TestEncodeAPI:
    """Test encode() function API and options handling."""

    def test_encode_accepts_dict_options(self):
        """encode() should accept options as a plain dict."""
        result = encode([1, 2, 3], {"delimiter": "\t"})
        assert result == "[3\t]: 1\t2\t3"

    def test_encode_accepts_encode_options_object(self):
        """encode() should accept EncodeOptions object."""
        options = EncodeOptions(delimiter="|", indent=4)
        result = encode([1, 2, 3], options)
        assert result == "[3|]: 1|2|3"

    def test_encode_default_options(self):
        """encode() should use defaults when no options provided."""
        result = encode({"a": 1, "b": 2})
        # Default: 2-space indent, comma delimiter
        assert result == "a: 1\nb: 2"

    def test_encode_with_comma_delimiter(self):
        """Comma delimiter should work correctly."""
        result = encode([1, 2, 3], {"delimiter": ","})
        assert result == "[3]: 1,2,3"

    def test_encode_with_tab_delimiter(self):
        """Tab delimiter should work correctly."""
        result = encode([1, 2, 3], {"delimiter": "\t"})
        assert result == "[3\t]: 1\t2\t3"

    def test_encode_with_pipe_delimiter(self):
        """Pipe delimiter should work correctly."""
        result = encode([1, 2, 3], {"delimiter": "|"})
        assert result == "[3|]: 1|2|3"

    def test_encode_with_custom_indent(self):
        """Custom indent size should be respected."""
        result = encode({"parent": {"child": 1}}, {"indent": 4})
        lines = result.split("\n")
        assert lines[1].startswith("    ")  # 4-space indent

    def test_encode_with_zero_indent(self):
        """Zero indent should use minimal spacing."""
        result = encode({"parent": {"child": 1}}, {"indent": 0})
        # Should still have some structure
        assert "parent:" in result
        assert "child: 1" in result

    def test_encode_with_length_marker(self):
        """lengthMarker option should add # prefix."""
        result = encode([1, 2, 3], {"lengthMarker": "#"})
        assert "[#3]:" in result

    def test_encode_none_returns_null_string(self):
        """Encoding None should return 'null' as a string."""
        result = encode(None)
        assert result == "null"
        assert isinstance(result, str)

    def test_encode_empty_object_returns_empty_string(self):
        """Encoding empty object should return empty string."""
        result = encode({})
        assert result == ""

    def test_encode_root_array(self):
        """Encoding root-level array should work."""
        result = encode([1, 2, 3])
        assert result == "[3]: 1,2,3"

    def test_encode_root_primitive(self):
        """Encoding root-level primitive should work."""
        result = encode("hello")
        assert result == "hello"


class TestDecodeAPI:
    """Test decode() function API and options handling."""

    def test_decode_with_decode_options(self):
        """decode() requires DecodeOptions object, not plain dict."""
        options = DecodeOptions(strict=False)
        result = decode("id: 123", options)
        assert result == {"id": 123}

    def test_decode_accepts_decode_options_object(self):
        """decode() should accept DecodeOptions object."""
        options = DecodeOptions(strict=True)
        result = decode("id: 123", options)
        assert result == {"id": 123}

    def test_decode_default_options(self):
        """decode() should use defaults when no options provided."""
        result = decode("id: 123\nname: Alice")
        assert result == {"id": 123, "name": "Alice"}

    def test_decode_strict_mode_enabled(self):
        """Strict mode should enforce validation."""
        # Array length mismatch should error in strict mode
        toon = "items[3]: a,b"  # Declared 3, only 2 values
        with pytest.raises(ToonDecodeError, match="Expected 3 values"):
            decode(toon, DecodeOptions(strict=True))

    def test_decode_lenient_mode_allows_mismatch(self):
        """Lenient mode should allow length mismatch."""
        toon = "items[3]: a,b"  # Declared 3, only 2 values
        result = decode(toon, DecodeOptions(strict=False))
        assert result == {"items": ["a", "b"]}

    def test_decode_empty_string_returns_empty_object(self):
        """Decoding empty string returns empty object (per spec Section 8)."""
        result = decode("")
        assert result == {}

    def test_decode_whitespace_only_returns_empty_object(self):
        """Decoding whitespace-only returns empty object (per spec Section 8)."""
        result = decode("   \n  \n   ")
        assert result == {}

    def test_decode_root_array(self):
        """Decoding root-level array should work."""
        result = decode("[3]: a,b,c")
        assert result == ["a", "b", "c"]

    def test_decode_root_primitive(self):
        """Decoding root-level primitive should work."""
        result = decode("hello world")
        assert result == "hello world"


class TestErrorHandling:
    """Test error handling and exception types."""

    def test_decode_invalid_syntax_treated_as_string(self):
        """Invalid TOON syntax for objects is treated as root primitive string."""
        result = decode("[[[ invalid syntax ]]]")
        # This is treated as a root-level primitive string
        assert result == "[[[ invalid syntax ]]]"

    def test_decode_unterminated_string_raises_error(self):
        """Unterminated string should raise ToonDecodeError."""
        toon = 'text: "unterminated'
        with pytest.raises(ToonDecodeError, match="Unterminated"):
            decode(toon)

    def test_decode_invalid_escape_raises_error(self):
        """Invalid escape sequence should raise ToonDecodeError."""
        toon = r'text: "invalid\x"'
        with pytest.raises(ToonDecodeError, match="Invalid escape"):
            decode(toon)

    def test_decode_missing_colon_raises_error(self):
        """Missing colon in key-value pair should raise error in strict mode."""
        toon = "key: value\ninvalid line without colon"
        with pytest.raises(ToonDecodeError, match="Missing colon"):
            decode(toon, DecodeOptions(strict=True))

    def test_decode_indentation_error_in_strict_mode(self):
        """Non-multiple indentation should error in strict mode."""
        toon = "user:\n   id: 1"  # 3 spaces instead of 2
        with pytest.raises(ToonDecodeError, match="exact multiple"):
            decode(toon, DecodeOptions(strict=True))


class TestErrorMessages:
    """Test that error messages are clear and helpful."""

    def test_decode_error_includes_context(self):
        """Decode errors should include helpful context."""
        toon = 'text: "unterminated string'
        try:
            decode(toon)
            pytest.fail("Should have raised ToonDecodeError")
        except ToonDecodeError as e:
            error_msg = str(e).lower()
            # Error should mention the problem
            assert "unterminated" in error_msg or "string" in error_msg

    def test_decode_length_mismatch_shows_expected_vs_actual(self):
        """Length mismatch errors should show expected vs actual."""
        toon = "items[5]: a,b,c"  # Declared 5, only 3 values
        try:
            decode(toon, DecodeOptions(strict=True))
            pytest.fail("Should have raised ToonDecodeError")
        except ToonDecodeError as e:
            error_msg = str(e)
            # Should mention both expected (5) and actual (3)
            assert "5" in error_msg and "3" in error_msg

    def test_decode_indentation_error_shows_line_info(self):
        """Indentation errors should indicate the problematic line."""
        toon = "user:\n   id: 1"  # 3 spaces, not a multiple of 2
        try:
            decode(toon, DecodeOptions(strict=True))
            pytest.fail("Should have raised ToonDecodeError")
        except ToonDecodeError as e:
            error_msg = str(e).lower()
            # Should mention indentation or spacing
            assert "indent" in error_msg or "multiple" in error_msg or "space" in error_msg


class TestOptionsValidation:
    """Test validation of options."""

    def test_encode_invalid_delimiter_type(self):
        """Invalid delimiter type should raise error."""
        with pytest.raises((TypeError, ValueError, AttributeError)):
            encode([1, 2, 3], {"delimiter": 123})  # Number instead of string

    def test_encode_unsupported_delimiter_value(self):
        """Unsupported delimiter should raise error or be handled."""
        # This might raise an error or just use it as-is
        # depending on implementation - test what happens
        try:
            result = encode([1, 2, 3], {"delimiter": ";"})
            # If it doesn't error, it should at least produce output
            assert result is not None
        except (TypeError, ValueError):
            # Also acceptable to reject unsupported delimiters
            pass

    def test_encode_negative_indent_accepted(self):
        """Negative indent is accepted (treated as 0 or minimal)."""
        # Implementation may accept negative indent
        result = encode({"a": 1}, {"indent": -1})
        assert result is not None  # Should produce output

    def test_decode_invalid_strict_type(self):
        """Invalid strict option type should raise error."""
        with pytest.raises((TypeError, ValueError, AttributeError)):
            decode("id: 1", {"strict": "yes"})  # String instead of bool


class TestRoundtrip:
    """Test encode/decode roundtrip with various options."""

    def test_roundtrip_with_comma_delimiter(self):
        """Roundtrip with comma delimiter should preserve data."""
        original = {"items": [1, 2, 3]}
        toon = encode(original, {"delimiter": ","})
        decoded = decode(toon)
        assert decoded == original

    def test_roundtrip_with_tab_delimiter(self):
        """Roundtrip with tab delimiter should preserve data."""
        original = {"items": [1, 2, 3]}
        toon = encode(original, {"delimiter": "\t"})
        decoded = decode(toon)
        assert decoded == original

    def test_roundtrip_with_pipe_delimiter(self):
        """Roundtrip with pipe delimiter should preserve data."""
        original = {"items": [1, 2, 3]}
        toon = encode(original, {"delimiter": "|"})
        decoded = decode(toon)
        assert decoded == original

    def test_roundtrip_with_custom_indent(self):
        """Roundtrip with custom indent should preserve data."""
        original = {"parent": {"child": {"value": 42}}}
        toon = encode(original, {"indent": 4})
        # Need to specify indent size for decoding as well
        decoded = decode(toon, DecodeOptions(indent=4))
        assert decoded == original

    def test_roundtrip_with_length_marker(self):
        """Roundtrip with length marker should preserve data."""
        original = {"items": [1, 2, 3]}
        toon = encode(original, {"lengthMarker": "#"})
        decoded = decode(toon)
        assert decoded == original


class TestDecodeJSONIndentation:
    """Test decode() JSON indentation feature (Issue #10)."""

    def test_decode_with_json_indent_returns_string(self):
        """decode() with json_indent should return JSON string."""
        toon = "id: 123\nname: Alice"
        options = DecodeOptions(json_indent=2)
        result = decode(toon, options)
        assert isinstance(result, str)
        # Verify it's valid JSON
        import json

        parsed = json.loads(result)
        assert parsed == {"id": 123, "name": "Alice"}

    def test_decode_with_json_indent_2(self):
        """decode() with json_indent=2 should format with 2 spaces."""
        toon = "id: 123\nname: Alice"
        result = decode(toon, DecodeOptions(json_indent=2))
        expected = '{\n  "id": 123,\n  "name": "Alice"\n}'
        assert result == expected

    def test_decode_with_json_indent_4(self):
        """decode() with json_indent=4 should format with 4 spaces."""
        toon = "id: 123\nname: Alice"
        result = decode(toon, DecodeOptions(json_indent=4))
        expected = '{\n    "id": 123,\n    "name": "Alice"\n}'
        assert result == expected

    def test_decode_with_json_indent_nested(self):
        """decode() with json_indent should handle nested structures."""
        toon = "user:\n  name: Alice\n  age: 30"
        result = decode(toon, DecodeOptions(json_indent=2))
        expected = '{\n  "user": {\n    "name": "Alice",\n    "age": 30\n  }\n}'
        assert result == expected

    def test_decode_with_json_indent_array(self):
        """decode() with json_indent should handle arrays."""
        toon = "items[2]: apple,banana"
        result = decode(toon, DecodeOptions(json_indent=2))
        expected = '{\n  "items": [\n    "apple",\n    "banana"\n  ]\n}'
        assert result == expected

    def test_decode_with_json_indent_none_returns_object(self):
        """decode() with json_indent=None should return Python object."""
        toon = "id: 123\nname: Alice"
        options = DecodeOptions(json_indent=None)
        result = decode(toon, options)
        assert isinstance(result, dict)
        assert result == {"id": 123, "name": "Alice"}

    def test_decode_with_json_indent_default_returns_object(self):
        """decode() without json_indent should return Python object (default)."""
        toon = "id: 123\nname: Alice"
        result = decode(toon)
        assert isinstance(result, dict)
        assert result == {"id": 123, "name": "Alice"}

    def test_decode_json_indent_with_unicode(self):
        """decode() with json_indent should preserve unicode characters."""
        toon = 'name: "José"'
        result = decode(toon, DecodeOptions(json_indent=2))
        assert "José" in result
        import json

        parsed = json.loads(result)
        assert parsed["name"] == "José"

    def test_decode_json_indent_empty_object(self):
        """decode() with json_indent on empty input should return empty object JSON."""
        result = decode("", DecodeOptions(json_indent=2))
        assert result == "{}"

    def test_decode_json_indent_single_primitive(self):
        """decode() with json_indent on single primitive should return JSON number."""
        result = decode("42", DecodeOptions(json_indent=2))
        assert result == "42"

    def test_decode_json_indent_complex_nested(self):
        """decode() with json_indent should handle complex nested structures."""
        toon = """users[2]{id,name}:
  1,Alice
  2,Bob
metadata:
  version: 1
  active: true"""
        result = decode(toon, DecodeOptions(json_indent=2))
        import json

        parsed = json.loads(result)
        assert parsed["users"][0] == {"id": 1, "name": "Alice"}
        assert parsed["metadata"]["version"] == 1
        assert parsed["metadata"]["active"] is True
