"""Tests for Python-specific TOON decoder behavior.

This file contains ONLY Python-specific decoder tests that are not covered
by the official spec fixtures in test_spec_fixtures.py.

For spec compliance testing, see test_spec_fixtures.py (306 official tests).
For Python type normalization, see test_normalization.py.
For API testing, see test_api.py.
"""

import pytest

from toon_format import ToonDecodeError, decode
from toon_format.types import DecodeOptions


class TestPythonDecoderAPI:
    """Test Python-specific decoder API behavior."""

    def test_decode_with_lenient_mode(self):
        """Test that lenient mode allows spec violations (Python-specific option)."""
        toon = "items[5]: a,b,c"  # Declared 5, only 3 values
        options = DecodeOptions(strict=False)
        result = decode(toon, options)
        # Lenient mode accepts the mismatch
        assert result == {"items": ["a", "b", "c"]}

    def test_decode_with_custom_indent_size(self):
        """Test Python API accepts custom indent size."""
        toon = """parent:
    child:
        value: 42"""  # 4-space indent
        options = DecodeOptions(indent=4)
        result = decode(toon, options)
        assert result == {"parent": {"child": {"value": 42}}}

    def test_decode_returns_python_dict(self):
        """Ensure decode returns native Python dict, not custom type."""
        toon = "id: 123"
        result = decode(toon)
        assert isinstance(result, dict)
        assert type(result) is dict  # Not a subclass

    def test_decode_returns_python_list(self):
        """Ensure decode returns native Python list for arrays."""
        toon = "[3]: 1,2,3"
        result = decode(toon)
        assert isinstance(result, list)
        assert type(result) is list  # Not a subclass


class TestPythonErrorHandling:
    """Test Python-specific error handling behavior."""

    def test_error_type_is_toon_decode_error(self):
        """Verify errors raise ToonDecodeError, not generic exceptions."""
        toon = 'text: "unterminated'
        with pytest.raises(ToonDecodeError):
            decode(toon)

    def test_error_is_exception_subclass(self):
        """ToonDecodeError should be catchable as Exception."""
        toon = 'text: "unterminated'
        with pytest.raises(Exception):  # Should also catch as base Exception
            decode(toon)

    def test_strict_mode_default_is_true(self):
        """Default strict mode should be True (fail on violations)."""
        toon = "items[5]: a,b,c"  # Length mismatch
        # Without options, should use strict=True by default
        with pytest.raises(ToonDecodeError):
            decode(toon)


class TestSpecEdgeCases:
    """Tests for spec edge cases that must be handled correctly."""

    def test_leading_zero_treated_as_string(self):
        """Leading zeros like '05', '0001' should decode as strings (Section 4)."""
        toon = "code: 05"
        result = decode(toon)
        assert result == {"code": "05"}
        assert isinstance(result["code"], str)

    def test_leading_zero_in_array(self):
        """Leading zeros in arrays should be strings."""
        toon = "codes[3]: 01,02,03"
        result = decode(toon)
        assert result == {"codes": ["01", "02", "03"]}
        assert all(isinstance(v, str) for v in result["codes"])

    def test_single_zero_is_number(self):
        """Single '0' is a valid number, not a leading zero case."""
        toon = "value: 0"
        result = decode(toon)
        assert result == {"value": 0}
        assert isinstance(result["value"], int)

    def test_zero_point_zero_is_number(self):
        """'0.0' is a valid number."""
        toon = "value: 0.0"
        result = decode(toon)
        assert result == {"value": 0.0}
        assert isinstance(result["value"], (int, float))

    def test_exponent_notation_accepted(self):
        """Decoder MUST accept exponent forms like 1e-6, -1E+9 (Section 4)."""
        toon = """a: 1e-6
b: -1E+9
c: 2.5e3
d: -3.14E-2"""
        result = decode(toon)
        assert result["a"] == 1e-6
        assert result["b"] == -1e9
        assert result["c"] == 2.5e3
        assert result["d"] == -3.14e-2

    def test_exponent_notation_in_array(self):
        """Exponent notation in arrays."""
        toon = "values[3]: 1e2,2e-1,3E+4"
        result = decode(toon)
        assert result["values"] == [1e2, 2e-1, 3e4]

    def test_array_order_preserved(self):
        """Array order MUST be preserved (Section 2)."""
        toon = "items[5]: 5,1,9,2,7"
        result = decode(toon)
        assert result["items"] == [5, 1, 9, 2, 7]
        # Verify order is exact, not sorted
        assert result["items"] != [1, 2, 5, 7, 9]

    def test_object_key_order_preserved(self):
        """Object key order MUST be preserved (Section 2)."""
        toon = """z: 1
a: 2
m: 3
b: 4"""
        result = decode(toon)
        keys = list(result.keys())
        assert keys == ["z", "a", "m", "b"]
        # Verify order is not alphabetical
        assert keys != ["a", "b", "m", "z"]


class TestCRLFDecoding:
    """Test CRLF (Windows) line ending handling in decoder."""

    def test_decode_object_with_crlf(self):
        """Test decoding objects with CRLF line endings."""
        toon = "name: Alice\r\nage: 30\r\n"
        result = decode(toon)
        assert result == {"name": "Alice", "age": 30}

    def test_decode_nested_object_with_crlf(self):
        """Test decoding nested objects with CRLF line endings."""
        toon = "person:\r\n  name: Alice\r\n  age: 30\r\n"
        result = decode(toon)
        assert result == {"person": {"name": "Alice", "age": 30}}

    def test_decode_array_with_crlf(self):
        """Test decoding arrays with CRLF line endings."""
        toon = "items[3]:\r\n  - apple\r\n  - banana\r\n  - cherry\r\n"
        result = decode(toon)
        assert result == {"items": ["apple", "banana", "cherry"]}

    def test_decode_delimited_array_with_crlf(self):
        """Test decoding delimited arrays with CRLF line endings."""
        toon = "items[3]: apple,banana,cherry\r\n"
        result = decode(toon)
        assert result == {"items": ["apple", "banana", "cherry"]}

    def test_decode_with_old_mac_cr(self):
        """Test decoding with old Mac CR line endings."""
        toon = "name: Alice\rage: 30\r"
        result = decode(toon)
        assert result == {"name": "Alice", "age": 30}

    def test_decode_with_mixed_line_endings(self):
        """Test decoding with mixed line endings."""
        toon = "name: Alice\r\nage: 30\ncity: NYC\r"
        result = decode(toon)
        assert result == {"name": "Alice", "age": 30, "city": "NYC"}

    def test_crlf_does_not_affect_quoted_strings(self):
        """Test that CRLF normalization doesn't affect escaped \\r in strings."""
        toon = 'text: "line1\\r\\nline2"\r\n'
        result = decode(toon)
        # The string should contain the escaped sequences
        assert result == {"text": "line1\r\nline2"}

    def test_crlf_in_strict_mode(self):
        """Test CRLF works correctly in strict mode."""
        toon = "name:\r\n  first: Alice\r\n  age: 30\r\n"
        options = DecodeOptions(strict=True)
        result = decode(toon, options)
        assert result == {"name": {"first": "Alice", "age": 30}}

