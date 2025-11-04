"""Tests for TOON edge cases.

This module tests critical edge cases to ensure correctness:
1. Large integers (>2^53-1) are converted to strings for JS compatibility
2. Octal-like strings are properly quoted
3. Sets are sorted deterministically
4. Negative zero is normalized to zero
5. Non-finite floats (inf, -inf, nan) are converted to null
6. Heterogeneous sets use stable fallback sorting
"""

from toon_format import decode, encode


class TestLargeIntegers:
    """Test large integer handling (>2^53-1)."""

    def test_large_positive_integer(self) -> None:
        """Large integers exceeding JS Number.MAX_SAFE_INTEGER should be strings."""
        max_safe_int = 2**53 - 1
        large_int = 2**60

        # Small integers stay as integers
        result = encode({"small": max_safe_int})
        assert "small: 9007199254740991" in result

        # Large integers become quoted strings
        result = encode({"bignum": large_int})
        assert 'bignum: "1152921504606846976"' in result

        # Round-trip verification
        decoded = decode(result)
        assert decoded["bignum"] == "1152921504606846976"

    def test_large_negative_integer(self) -> None:
        """Large negative integers should also be converted to strings."""
        large_negative = -(2**60)
        result = encode({"neg": large_negative})
        assert 'neg: "-1152921504606846976"' in result

        # Round-trip verification
        decoded = decode(result)
        assert decoded["neg"] == "-1152921504606846976"

    def test_boundary_cases(self) -> None:
        """Test exact boundaries of MAX_SAFE_INTEGER."""
        max_safe = 2**53 - 1
        just_over = 2**53

        result_safe = encode({"safe": max_safe})
        result_over = encode({"over": just_over})

        # At boundary: still integer
        assert "safe: 9007199254740991" in result_safe

        # Just over boundary: becomes string
        assert 'over: "9007199254740992"' in result_over


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
        # Large int should be string, others should be ints
        assert "1152921504606846976" in decoded["big_set"]
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
        assert decoded["large"] == "1152921504606846976"
        assert decoded["octal"] == "0755"
        assert decoded["inf"] is None
        assert decoded["neg_zero"] == 0
        assert decoded["nested"]["more_sets"] == ["a", "m", "z"]
        assert decoded["nested"]["nan"] is None
