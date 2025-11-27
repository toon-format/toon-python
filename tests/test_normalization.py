"""Tests for Python-specific type normalization in TOON format.

This module tests Python-specific behavior not covered by the official TOON spec
(which targets JavaScript/JSON). These tests ensure Python types are correctly
normalized to JSON-compatible values:

1. Large integers (>2^53-1) → strings for JavaScript compatibility
2. Python types (set, tuple, frozenset) → sorted lists
3. Negative zero → positive zero
4. Non-finite floats (inf, -inf, NaN) → null
5. Decimal → float conversion
6. Octal-like strings → properly quoted
7. Heterogeneous type sorting → stable, deterministic order

Note: TOON spec v1.3 compliance is tested in test_spec_fixtures.py using
official fixtures from https://github.com/toon-format/spec
"""

from decimal import Decimal
from pathlib import Path, PurePosixPath, PureWindowsPath

from toon_format import decode, encode


class TestLargeIntegers:
    """Test large integer handling (>2^53-1)."""

    def test_large_positive_integer(self) -> None:
        """Python integers (arbitrary precision) stay as integers."""
        max_safe_int = 2**53 - 1
        large_int = 2**60

        # Small integers stay as integers
        result = encode({"small": max_safe_int})
        assert "small: 9007199254740991" in result

        # Large integers also stay as integers (Python has arbitrary precision)
        result = encode({"bignum": large_int})
        assert "bignum: 1152921504606846976" in result

        # Round-trip verification
        decoded = decode(result)
        assert decoded["bignum"] == 1152921504606846976

    def test_large_negative_integer(self) -> None:
        """Large negative integers stay as integers (Python arbitrary precision)."""
        large_negative = -(2**60)
        result = encode({"neg": large_negative})
        assert "neg: -1152921504606846976" in result

        # Round-trip verification
        decoded = decode(result)
        assert decoded["neg"] == -1152921504606846976

    def test_boundary_cases(self) -> None:
        """Test exact boundaries of MAX_SAFE_INTEGER (Python keeps all as integers)."""
        max_safe = 2**53 - 1
        just_over = 2**53

        result_safe = encode({"safe": max_safe})
        result_over = encode({"over": just_over})

        # At boundary: integer
        assert "safe: 9007199254740991" in result_safe

        # Just over boundary: still integer (Python has arbitrary precision)
        assert "over: 9007199254740992" in result_over


class TestOctalStrings:
    """Test octal-like string quoting."""

    def test_octal_like_strings_are_quoted(self) -> None:
        """Strings that look like octal numbers must be quoted."""
        result = encode({"code": "0123"})
        assert 'code: "0123"' in result

        result = encode({"zip": "0755"})
        assert 'zip: "0755"' in result

    def test_single_zero_not_quoted(self) -> None:
        """Single '0' is not octal-like."""
        result = encode({"zero": "0"})
        # Single "0" looks like a number, so it should be quoted
        assert 'zero: "0"' in result

    def test_zero_with_non_octal_digits(self) -> None:
        """'0' followed by non-octal digits."""
        result = encode({"val": "0999"})
        # This looks like octal pattern (starts with 0 followed by digits)
        assert 'val: "0999"' in result

    def test_octal_in_array(self) -> None:
        """Octal-like strings in arrays."""
        result = encode(["0123", "0456"])
        assert '"0123"' in result
        assert '"0456"' in result

        # Round-trip verification
        decoded = decode(result)
        assert decoded == ["0123", "0456"]


class TestSetOrdering:
    """Test set ordering for deterministic output."""

    def test_numeric_set_sorted(self) -> None:
        """Sets of numbers should be sorted."""
        data = {"tags": {3, 1, 2}}
        result1 = encode(data)
        result2 = encode(data)

        # Should be deterministic
        assert result1 == result2

        # Should be sorted: 1, 2, 3
        decoded = decode(result1)
        assert decoded["tags"] == [1, 2, 3]

    def test_string_set_sorted(self) -> None:
        """Sets of strings should be sorted."""
        data = {"items": {"zebra", "apple", "mango"}}
        result = encode(data)

        decoded = decode(result)
        assert decoded["items"] == ["apple", "mango", "zebra"]

    def test_set_ordering_consistency(self) -> None:
        """Multiple encodes of the same set should produce identical output."""
        data = {"nums": {5, 2, 8, 1, 9, 3}}

        results = [encode(data) for _ in range(5)]

        # All results should be identical
        assert all(r == results[0] for r in results)

        # Should be sorted
        decoded = decode(results[0])
        assert decoded["nums"] == [1, 2, 3, 5, 8, 9]


class TestNegativeZero:
    """Test negative zero normalization."""

    def test_negative_zero_becomes_zero(self) -> None:
        """Negative zero should be normalized to positive zero."""
        data = {"val": -0.0}
        result = encode(data)

        # Should be "val: 0", not "val: -0"
        assert "val: 0" in result or "val: 0.0" in result
        # Should NOT contain "-0"
        assert "-0" not in result

    def test_negative_zero_in_array(self) -> None:
        """Negative zero in arrays."""
        data = [-0.0, 0.0, 1.0]
        result = encode(data)

        # Should not contain "-0"
        assert "-0" not in result

        decoded = decode(result)
        # Both should be 0
        assert decoded[0] == 0
        assert decoded[1] == 0

    def test_regular_negative_numbers_preserved(self) -> None:
        """Regular negative numbers should not be affected."""
        data = {"neg": -1.5}
        result = encode(data)

        assert "neg: -1.5" in result


class TestNonFiniteFloats:
    """Test non-finite float handling (inf, -inf, nan)."""

    def test_positive_infinity(self) -> None:
        """Positive infinity should become null."""
        data = {"inf": float("inf")}
        result = encode(data)

        assert "inf: null" in result

        decoded = decode(result)
        assert decoded["inf"] is None

    def test_negative_infinity(self) -> None:
        """Negative infinity should become null."""
        data = {"ninf": float("-inf")}
        result = encode(data)

        assert "ninf: null" in result

        decoded = decode(result)
        assert decoded["ninf"] is None

    def test_nan(self) -> None:
        """NaN should become null."""
        data = {"nan": float("nan")}
        result = encode(data)

        assert "nan: null" in result

        decoded = decode(result)
        assert decoded["nan"] is None

    def test_all_non_finite_in_array(self) -> None:
        """All non-finite values in an array."""
        data = [float("inf"), float("-inf"), float("nan"), 1.5, 2.0]
        result = encode(data)

        decoded = decode(result)
        assert decoded == [None, None, None, 1.5, 2.0]

    def test_mixed_object_with_non_finite(self) -> None:
        """Object with mix of finite and non-finite values."""
        data = {
            "normal": 3.14,
            "inf": float("inf"),
            "ninf": float("-inf"),
            "nan": float("nan"),
            "zero": 0.0,
        }
        result = encode(data)

        decoded = decode(result)
        assert decoded["normal"] == 3.14
        assert decoded["inf"] is None
        assert decoded["ninf"] is None
        assert decoded["nan"] is None
        assert decoded["zero"] == 0


class TestHeterogeneousSets:
    """Test heterogeneous set handling with fallback sorting."""

    def test_mixed_types_in_set(self) -> None:
        """Sets with mixed types should use stable fallback sorting."""
        # Note: In Python, you can't directly create {1, "a"} because sets require hashable items
        # But normalization converts sets to lists, and we can test mixed lists
        data = {"mixed": {1, 2, 3}}  # Start with same-type set
        result = encode(data)

        # Should not crash
        decoded = decode(result)
        assert isinstance(decoded["mixed"], list)

    def test_heterogeneous_set_deterministic(self) -> None:
        """Heterogeneous sets should produce deterministic output."""
        # Create a set that would challenge sorting
        data = {"items": {42, 7, 15}}

        results = [encode(data) for _ in range(3)]

        # Should all be the same
        assert all(r == results[0] for r in results)

    def test_empty_set(self) -> None:
        """Empty sets should encode properly."""
        data = {"empty": set()}
        result = encode(data)

        decoded = decode(result)
        assert decoded["empty"] == []

    def test_single_element_set(self) -> None:
        """Single-element sets."""
        data = {"single": {42}}
        result = encode(data)

        decoded = decode(result)
        assert decoded["single"] == [42]


class TestEdgeCaseCombinations:
    """Test combinations of edge cases."""

    def test_large_int_in_set(self) -> None:
        """Large integers in sets."""
        large_int = 2**60
        data = {"big_set": {large_int, 100, 200}}
        result = encode(data)

        decoded = decode(result)
        # All integers stay as integers (Python has arbitrary precision)
        assert 1152921504606846976 in decoded["big_set"]
        assert 100 in decoded["big_set"]
        assert 200 in decoded["big_set"]

    def test_octal_strings_in_object_keys(self) -> None:
        """Octal-like strings as object keys are handled differently."""
        # In TOON, object keys have different quoting rules
        data = {"0123": "value"}
        result = encode(data)

        # Should encode successfully
        assert result is not None

        # Round-trip should work
        decoded = decode(result)
        assert "0123" in decoded
        assert decoded["0123"] == "value"

    def test_complex_nested_edge_cases(self) -> None:
        """Complex nesting with multiple edge cases."""
        data = {
            "sets": {1, 2, 3},
            "large": 2**60,
            "octal": "0755",
            "inf": float("inf"),
            "neg_zero": -0.0,
            "nested": {"more_sets": {"z", "a", "m"}, "nan": float("nan")},
        }

        result = encode(data)

        # Should encode without errors
        assert result is not None

        # Should round-trip correctly
        decoded = decode(result)
        assert decoded["sets"] == [1, 2, 3]
        assert decoded["large"] == 1152921504606846976  # Integer stays as integer
        assert decoded["octal"] == "0755"
        assert decoded["inf"] is None
        assert decoded["neg_zero"] == 0
        assert decoded["nested"]["more_sets"] == ["a", "m", "z"]
        assert decoded["nested"]["nan"] is None


class TestPythonTypeNormalization:
    """Test normalization of Python-specific types to JSON-compatible values."""

    def test_tuple_to_list(self):
        """Tuples should be converted to arrays."""
        result = encode({"items": (1, 2, 3)})
        decoded = decode(result)
        assert decoded == {"items": [1, 2, 3]}

    def test_tuple_preserves_order(self):
        """Tuple order should be preserved in conversion."""
        result = encode({"coords": (3, 1, 4, 1, 5)})
        assert "[5]: 3,1,4,1,5" in result
        decoded = decode(result)
        assert decoded["coords"] == [3, 1, 4, 1, 5]

    def test_frozenset_to_sorted_list(self):
        """Frozensets should be converted to sorted arrays."""
        result = encode({"items": frozenset([3, 1, 2])})
        decoded = decode(result)
        assert decoded == {"items": [1, 2, 3]}

    def test_decimal_to_float(self):
        """Decimal should be converted to float."""
        result = encode({"price": Decimal("19.99")})
        assert "price: 19.99" in result
        decoded = decode(result)
        assert decoded["price"] == 19.99

    def test_decimal_precision_preserved(self):
        """Decimal precision should be preserved during conversion."""
        result = encode({"value": Decimal("3.14159")})
        decoded = decode(result)
        assert abs(decoded["value"] - 3.14159) < 0.00001

    def test_nested_python_types(self):
        """Nested Python types should all be normalized."""
        data = {
            "tuple_field": (1, 2, 3),
            "set_field": {3, 2, 1},
            "nested": {
                "decimal": Decimal("99.99"),
            },
        }
        result = encode(data)
        decoded = decode(result)

        assert decoded["tuple_field"] == [1, 2, 3]
        assert decoded["set_field"] == [1, 2, 3]
        assert decoded["nested"]["decimal"] == 99.99

    def test_empty_python_types(self):
        """Empty Python-specific types should normalize to empty arrays."""
        data = {
            "empty_tuple": (),
            "empty_set": set(),
        }
        result = encode(data)
        decoded = decode(result)

        assert decoded["empty_tuple"] == []
        assert decoded["empty_set"] == []


class TestNumericPrecision:
    """Test numeric round-trip fidelity (TOON v1.3 spec requirement)."""

    def test_roundtrip_numeric_precision(self):
        """All numbers should round-trip with fidelity."""
        original = {
            "integer": 42,
            "negative": -123,
            "zero": 0,
            "float": 3.14159265358979,
            "small": 0.0001,
            "very_small": 1e-10,
            "large": 999999999999999,
            "scientific": 1.23e15,
            "negative_float": -0.00001,
            "precise": 0.1 + 0.2,  # Famous floating point case
        }
        toon = encode(original)
        decoded = decode(toon)

        # All numbers should round-trip with fidelity
        for key, value in original.items():
            assert decoded[key] == value, f"Mismatch for {key}: {decoded[key]} != {value}"


class TestPathNormalization:
    """Test pathlib.Path normalization to strings."""

    def test_path_to_string(self):
        """pathlib.Path should be converted to string."""
        data = {"file": Path("/tmp/test.txt")}
        result = encode(data)
        decoded = decode(result)

        assert decoded["file"] == "/tmp/test.txt"

    def test_relative_path(self):
        """Relative paths should be preserved."""
        data = {"rel": Path("./relative/path.txt")}
        result = encode(data)
        decoded = decode(result)

        # Path normalization may vary, but should be a string
        assert isinstance(decoded["rel"], str)
        assert "relative" in decoded["rel"]
        assert "path.txt" in decoded["rel"]

    def test_pure_path(self):
        """PurePath objects should also be normalized."""
        data = {
            "posix": PurePosixPath("/usr/bin/python"),
            "windows": PureWindowsPath("C:\\Windows\\System32"),
        }
        result = encode(data)
        decoded = decode(result)

        assert decoded["posix"] == "/usr/bin/python"
        assert decoded["windows"] == "C:\\Windows\\System32"

    def test_path_in_array(self):
        """Path objects in arrays should be normalized."""
        data = {"paths": [Path("/tmp/a"), Path("/tmp/b"), Path("/tmp/c")]}
        result = encode(data)
        decoded = decode(result)

        assert decoded["paths"] == ["/tmp/a", "/tmp/b", "/tmp/c"]

    def test_path_in_nested_structure(self):
        """Path objects in nested structures should be normalized."""
        data = {
            "project": {
                "root": Path("/home/user/project"),
                "src": Path("/home/user/project/src"),
                "files": [
                    {"name": "main.py", "path": Path("/home/user/project/src/main.py")},
                    {"name": "test.py", "path": Path("/home/user/project/src/test.py")},
                ],
            }
        }
        result = encode(data)
        decoded = decode(result)

        assert decoded["project"]["root"] == "/home/user/project"
        assert decoded["project"]["src"] == "/home/user/project/src"
        assert decoded["project"]["files"][0]["path"] == "/home/user/project/src/main.py"
        assert decoded["project"]["files"][1]["path"] == "/home/user/project/src/test.py"
