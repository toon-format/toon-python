"""Direct unit tests for normalize.py functions.

This module tests the normalize module's functions directly to ensure
full coverage of edge cases and error paths.
"""

import sys
from collections import OrderedDict, UserDict
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from toon_format.normalize import (
    is_array_of_arrays,
    is_array_of_objects,
    is_array_of_primitives,
    is_json_array,
    is_json_object,
    is_json_primitive,
    normalize_value,
)


class TestNormalizeValue:
    """Tests for normalize_value function."""

    def test_none_value(self):
        """Test None is returned as-is."""
        assert normalize_value(None) is None

    def test_bool_value(self):
        """Test bool values are returned as-is."""
        assert normalize_value(True) is True
        assert normalize_value(False) is False

    def test_str_value(self):
        """Test string values are returned as-is."""
        assert normalize_value("hello") == "hello"
        assert normalize_value("") == ""

    def test_int_value(self):
        """Test integers are returned as-is."""
        assert normalize_value(42) == 42
        assert normalize_value(-100) == -100
        assert normalize_value(0) == 0

    def test_float_value(self):
        """Test normal floats are returned as-is."""
        assert normalize_value(3.14) == 3.14
        assert normalize_value(-2.5) == -2.5

    def test_non_finite_float_inf(self):
        """Test infinity is converted to null."""
        assert normalize_value(float("inf")) is None
        assert normalize_value(float("-inf")) is None

    def test_non_finite_float_nan(self):
        """Test NaN is converted to null."""
        assert normalize_value(float("nan")) is None

    def test_negative_zero_normalized(self):
        """Test negative zero is normalized to positive zero."""
        assert normalize_value(-0.0) == 0

    def test_decimal_to_float(self):
        """Test Decimal is converted to float."""
        assert normalize_value(Decimal("19.99")) == 19.99
        assert normalize_value(Decimal("3.14159")) == 3.14159

    def test_decimal_non_finite_to_null(self):
        """Test non-finite Decimal values are converted to null."""
        inf_decimal = Decimal("Infinity")
        neg_inf_decimal = Decimal("-Infinity")
        nan_decimal = Decimal("NaN")

        assert normalize_value(inf_decimal) is None
        assert normalize_value(neg_inf_decimal) is None
        assert normalize_value(nan_decimal) is None

    def test_datetime_to_iso_string(self):
        """Test datetime is converted to ISO 8601 string."""
        dt = datetime(2024, 1, 15, 10, 30, 45)
        result = normalize_value(dt)
        assert result == "2024-01-15T10:30:45"

    def test_date_to_iso_string(self):
        """Test date is converted to ISO 8601 string."""
        d = date(2024, 1, 15)
        result = normalize_value(d)
        assert result == "2024-01-15"

    def test_list_normalization(self):
        """Test lists are recursively normalized."""
        data = [1, 2.5, "text", None]
        result = normalize_value(data)
        assert result == [1, 2.5, "text", None]

    def test_empty_list(self):
        """Test empty list is handled correctly."""
        assert normalize_value([]) == []

    def test_nested_list(self):
        """Test nested lists are recursively normalized."""
        data = [1, [2, [3, 4]], 5]
        result = normalize_value(data)
        assert result == [1, [2, [3, 4]], 5]

    def test_tuple_to_list(self):
        """Test tuples are converted to lists."""
        result = normalize_value((1, 2, 3))
        assert result == [1, 2, 3]

    def test_empty_tuple(self):
        """Test empty tuple is converted to empty list."""
        result = normalize_value(())
        assert result == []

    def test_set_to_sorted_list(self):
        """Test sets are converted to sorted lists."""
        result = normalize_value({3, 1, 2})
        assert result == [1, 2, 3]

    def test_frozenset_to_sorted_list(self):
        """Test frozensets are converted to sorted lists."""
        result = normalize_value(frozenset({3, 1, 2}))
        assert result == [1, 2, 3]

    def test_heterogeneous_set_uses_repr_sorting(self):
        """Test heterogeneous sets use repr() for stable sorting."""

        # Create a set with objects that can't be naturally sorted
        class CustomObj:
            def __init__(self, val):
                self.val = val

            def __repr__(self):
                return f"CustomObj({self.val})"

            def __hash__(self):
                return hash(self.val)

            def __eq__(self, other):
                return self.val == other.val

        obj1 = CustomObj("a")
        obj2 = CustomObj("b")
        data = {obj1, obj2}

        # Should not raise TypeError
        result = normalize_value(data)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_dict_normalization(self):
        """Test dicts are recursively normalized."""
        data = {"a": 1, "b": 2.5}
        result = normalize_value(data)
        assert result == {"a": 1, "b": 2.5}

    def test_mapping_with_non_string_keys(self):
        """Test Mapping types with non-string keys are converted."""
        data = OrderedDict([(1, "one"), (2, "two")])
        result = normalize_value(data)
        assert result == {"1": "one", "2": "two"}

    def test_callable_to_null(self):
        """Test callable objects are converted to null."""

        def my_func():
            pass

        assert normalize_value(my_func) is None
        assert normalize_value(lambda x: x) is None

    def test_unsupported_type_to_null(self):
        """Test unsupported types are converted to null with warning."""

        class CustomClass:
            pass

        obj = CustomClass()
        result = normalize_value(obj)
        assert result is None


class TestTypeGuards:
    """Tests for type guard functions."""

    def test_is_json_primitive(self):
        """Test is_json_primitive correctly identifies primitives."""
        assert is_json_primitive(None) is True
        assert is_json_primitive("text") is True
        assert is_json_primitive(42) is True
        assert is_json_primitive(3.14) is True
        assert is_json_primitive(True) is True
        assert is_json_primitive(False) is True

        assert is_json_primitive([]) is False
        assert is_json_primitive({}) is False
        assert is_json_primitive(object()) is False

    def test_is_json_array(self):
        """Test is_json_array correctly identifies lists."""
        assert is_json_array([]) is True
        assert is_json_array([1, 2, 3]) is True
        assert is_json_array([None, "text"]) is True

        assert is_json_array(None) is False
        assert is_json_array({}) is False
        assert is_json_array((1, 2)) is False
        assert is_json_array("text") is False

    def test_is_json_object(self):
        """Test is_json_object correctly identifies dicts."""
        assert is_json_object({}) is True
        assert is_json_object({"a": 1}) is True

        assert is_json_object(None) is False
        assert is_json_object([]) is False
        assert is_json_object("text") is False

    def test_is_array_of_primitives(self):
        """Test is_array_of_primitives identifies arrays of primitives."""
        assert is_array_of_primitives([]) is True
        assert is_array_of_primitives([1, 2, 3]) is True
        assert is_array_of_primitives(["a", "b", "c"]) is True
        assert is_array_of_primitives([None, 1, "text", True]) is True

        assert is_array_of_primitives([1, [2, 3]]) is False
        assert is_array_of_primitives([{"a": 1}]) is False

    def test_is_array_of_arrays(self):
        """Test is_array_of_arrays identifies arrays of arrays."""
        assert is_array_of_arrays([]) is True
        assert is_array_of_arrays([[1, 2], [3, 4]]) is True
        assert is_array_of_arrays([[], []]) is True

        assert is_array_of_arrays([1, 2]) is False
        assert is_array_of_arrays([[1], 2]) is False
        assert is_array_of_arrays([{"a": 1}]) is False

    def test_is_array_of_objects(self):
        """Test is_array_of_objects identifies arrays of objects."""
        assert is_array_of_objects([]) is True
        assert is_array_of_objects([{"a": 1}, {"b": 2}]) is True
        assert is_array_of_objects([{}, {}]) is True

        assert is_array_of_objects([1, 2]) is False
        assert is_array_of_objects([[1, 2]]) is False
        assert is_array_of_objects([{"a": 1}, 2]) is False


class TestErrorHandling:
    """Tests for error handling paths."""

    def test_mapping_conversion_error(self):
        """Test error handling when mapping conversion fails."""

        class BadMapping(dict):
            """A mapping that raises error during items()."""

            def items(self):
                raise RuntimeError("items() failed")

        bad_map = BadMapping({"a": 1})
        # Should raise ValueError wrapping the RuntimeError
        with pytest.raises(ValueError, match="Failed to convert mapping"):
            normalize_value(bad_map)


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_list_with_non_finite_floats(self):
        """Test lists containing non-finite floats."""
        data = [1, float("inf"), 2, float("nan"), 3]
        result = normalize_value(data)
        assert result == [1, None, 2, None, 3]

    def test_nested_dict_with_decimals(self):
        """Test nested dicts with Decimal values."""
        data = {"outer": {"price": Decimal("19.99"), "tax": Decimal("2.00")}}
        result = normalize_value(data)
        assert result == {"outer": {"price": 19.99, "tax": 2.0}}

    def test_complex_nested_structure(self):
        """Test complex nested structure normalization."""
        data = {
            "users": [
                {"name": "Alice", "scores": (95, 87, 92)},
                {"name": "Bob", "scores": (88, 91, 85)},
            ],
            "stats": {"count": 2, "average": Decimal("89.67")},
            "tags": {"python", "testing", "toon"},
        }
        result = normalize_value(data)

        assert result["users"][0]["scores"] == [95, 87, 92]
        assert result["users"][1]["scores"] == [88, 91, 85]
        assert result["stats"]["average"] == 89.67
        assert result["tags"] == ["python", "testing", "toon"]

    def test_empty_structures(self):
        """Test various empty structures."""
        assert normalize_value({}) == {}
        assert normalize_value([]) == []
        assert normalize_value(set()) == []
        assert normalize_value(frozenset()) == []
        assert normalize_value(()) == []

    def test_list_of_tuples(self):
        """Test list containing tuples."""
        data = [(1, 2), (3, 4), (5, 6)]
        result = normalize_value(data)
        assert result == [[1, 2], [3, 4], [5, 6]]

    def test_dict_of_sets(self):
        """Test dict containing sets."""
        data = {"a": {3, 1, 2}, "b": {6, 4, 5}}
        result = normalize_value(data)
        assert result == {"a": [1, 2, 3], "b": [4, 5, 6]}
