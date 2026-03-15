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

class TestNestedStructures:
    """Test cases - complex nested structures."""

    def test_nested_object_with_array(self):
        """Test decoding nested object containing arrays."""
        toon = """a:
  b: "123"
  c[3]: 1,2,3"""
        result = decode(toon)
        assert result == {
            "a": {
                "b": "123",
                "c": [1, 2, 3],
            }
        }

    def test_root_array_with_nested_objects(self):
        """Test decoding root-level array with nested objects."""
        toon = """[1]:
  -
    a: "123" """
        result = decode(toon)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == {"a": "123"}

    def test_tabular_array_with_pipe_delimiter(self):
        """Test tabular array using pipe delimiter."""
        toon = '''translations[1|]{id|translation}:
  1|"Stop your grinning, I shouted"'''
        result = decode(toon)
        expected = {
            "translations": [
                {
                    "id": 1,
                    "translation": "Stop your grinning, I shouted",
                }
            ]
        }
        assert result == expected

    def test_tabular_array_comma_delimiter(self):
        """Test tabular array with comma delimiter."""
        toon = """users[2]{id,name}:
  1,Alice
  2,Bob"""
        result = decode(toon)
        assert result == {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
            ]
        }

    def test_tabular_array_mixed_types(self):
        """Test tabular array with mixed data types in rows."""
        toon = """data[3]{id,active,score}:
  1,true,95.5
  2,false,-42
  3,true,0.0"""
        result = decode(toon)
        assert result == {
            "data": [
                {"id": 1, "active": True, "score": 95.5},
                {"id": 2, "active": False, "score": -42},
                {"id": 3, "active": True, "score": 0.0},
            ]
        }

    def test_simple_object_with_primitives(self):
        """Test simple object with various primitive types."""
        toon = """name: Alice
age: 30
active: true
score: 95.5"""
        result = decode(toon)
        assert result == {
            "name": "Alice",
            "age": 30,
            "active": True,
            "score": 95.5,
        }

    def test_empty_input_returns_empty_object(self):
        """Empty or whitespace-only input should return empty object."""
        assert decode("") == {}
        assert decode("   ") == {}
        assert decode("\n\n") == {}

    def test_single_primitive_value(self):
        """Single primitive on one line should decode as that primitive."""
        assert decode("42") == 42
        assert decode('"hello"') == "hello"
        assert decode("true") is True
        assert decode("false") is False
        assert decode("null") is None

    def test_inline_primitive_array(self):
        """Inline primitive arrays decode correctly."""
        toon = "[3]: 1,2,3"
        result = decode(toon)
        assert result == [1, 2, 3]

    def test_inline_primitive_array_with_strings(self):
        """Inline primitive array with quoted strings."""
        toon = '[3]: "apple","banana","cherry"'
        result = decode(toon)
        assert result == ["apple", "banana", "cherry"]

    def test_string_with_escaped_quotes(self):
        """Strings with escaped quotes should be unescaped."""
        toon = r'text: "She said \"hello\""'
        result = decode(toon)
        assert result == {"text": 'She said "hello"'}

    def test_deeply_nested_objects(self):
        """Test deeply nested object structures."""
        toon = """level1:
  level2:
    level3:
      level4:
        value: 42"""
        result = decode(toon)
        assert result == {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {"value": 42}
                    }
                }
            }
        }

    def test_array_in_nested_object(self):
        """Array nested inside objects at various levels."""
        toon = """config:
  items[2]: first,second
  nested:
    ids[3]: 1,2,3"""
        result = decode(toon)
        assert result == {
            "config": {
                "items": ["first", "second"],
                "nested": {
                    "ids": [1, 2, 3]
                },
            }
        }

    def test_multiple_arrays_in_object(self):
        """Object with multiple array fields."""
        toon = """data:
  names[2]: Alice,Bob
  ages[2]: 30,25
  scores[2]: 95.5,87.0"""
        result = decode(toon)
        assert result == {
            "data": {
                "names": ["Alice", "Bob"],
                "ages": [30, 25],
                "scores": [95.5, 87.0],
            }
        }

    def test_quoted_keys(self):
        """Keys can be quoted to allow special characters."""
        toon = '''"special-key": value1
"another.key": value2'''
        result = decode(toon)
        assert result == {
            "special-key": "value1",
            "another.key": "value2",
        }

    def test_lenient_mode_allows_length_mismatch(self):
        """Lenient mode should allow declared length mismatches."""
        toon = "items[10]: a,b,c"  # Declared 10, got 3
        result = decode(toon, DecodeOptions(strict=False))
        assert result == {"items": ["a", "b", "c"]}

    def test_strict_mode_rejects_length_mismatch(self):
        """Strict mode should reject declared length mismatches."""
        toon = "items[10]: a,b,c"  # Declared 10, got 3
        with pytest.raises(ToonDecodeError):
            decode(toon, DecodeOptions(strict=True))

    def test_list_format_array_with_mixed_items(self):
        """List format arrays with mixed primitive and object items."""
        toon = """items[3]:
  - first
  - 42
  - true"""
        result = decode(toon)
        assert result == {
            "items": ["first", 42, True]
        }

    def test_list_format_array_with_objects(self):
        """List format array with object items."""
        toon = """users[2]:
  -
    name: Alice
    age: 30
  -
    name: Bob
    age: 25"""
        result = decode(toon)
        assert result == {
            "users": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25},
            ]
        }