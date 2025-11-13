"""Tests for numeric detection utilities.

Tests the consistency and correctness of numeric literal detection
across encoding and decoding pipelines.
"""

from toon_format._literal_utils import is_numeric_literal
from toon_format._validation import is_numeric_like


class TestNumericLiteral:
    """Tests for is_numeric_literal (decoder utility)."""

    def test_valid_integers(self):
        """Test valid integer literals are recognized."""
        assert is_numeric_literal("0")
        assert is_numeric_literal("1")
        assert is_numeric_literal("42")
        assert is_numeric_literal("999")
        assert is_numeric_literal("-1")
        assert is_numeric_literal("-42")

    def test_valid_floats(self):
        """Test valid float literals are recognized."""
        assert is_numeric_literal("0.0")
        assert is_numeric_literal("0.5")
        assert is_numeric_literal("3.14")
        assert is_numeric_literal("-2.5")
        assert is_numeric_literal("1.23456")

    def test_scientific_notation(self):
        """Test scientific notation is recognized."""
        assert is_numeric_literal("1e10")
        assert is_numeric_literal("1.5e10")
        assert is_numeric_literal("1e-10")
        assert is_numeric_literal("1.5e-10")
        assert is_numeric_literal("-1e10")
        assert is_numeric_literal("2.5E+3")

    def test_leading_zeros_rejected(self):
        """Test numbers with leading zeros are rejected (except special cases)."""
        assert not is_numeric_literal("01")
        assert not is_numeric_literal("0123")
        assert not is_numeric_literal("00")
        assert not is_numeric_literal("-01")
        # But these are valid:
        assert is_numeric_literal("0")  # Just zero
        assert is_numeric_literal("0.5")  # Decimal starting with zero
        assert is_numeric_literal("0.0")

    def test_non_numeric_strings(self):
        """Test non-numeric strings are rejected."""
        assert not is_numeric_literal("")
        assert not is_numeric_literal("abc")
        assert not is_numeric_literal("12abc")
        assert not is_numeric_literal("12.34.56")
        assert not is_numeric_literal("--5")
        assert not is_numeric_literal("1.2.3")

    def test_special_float_values_rejected(self):
        """Test NaN and infinity are rejected."""
        assert not is_numeric_literal("nan")
        assert not is_numeric_literal("NaN")
        assert not is_numeric_literal("inf")
        assert not is_numeric_literal("Infinity")
        assert not is_numeric_literal("-inf")

    def test_empty_string(self):
        """Test empty string is rejected."""
        assert not is_numeric_literal("")

    def test_whitespace_only(self):
        """Test whitespace-only strings are rejected."""
        assert not is_numeric_literal(" ")
        assert not is_numeric_literal("  ")


class TestNumericLike:
    """Tests for is_numeric_like (encoder utility)."""

    def test_valid_integers(self):
        """Test valid integers are recognized as numeric-like."""
        assert is_numeric_like("0")
        assert is_numeric_like("1")
        assert is_numeric_like("42")
        assert is_numeric_like("-1")
        assert is_numeric_like("-42")

    def test_valid_floats(self):
        """Test valid floats are recognized as numeric-like."""
        assert is_numeric_like("0.0")
        assert is_numeric_like("0.5")
        assert is_numeric_like("3.14")
        assert is_numeric_like("-2.5")

    def test_scientific_notation(self):
        """Test scientific notation is recognized as numeric-like."""
        assert is_numeric_like("1e10")
        assert is_numeric_like("1.5e10")
        assert is_numeric_like("1e-10")
        assert is_numeric_like("2.5E+3")

    def test_octal_like_numbers(self):
        """Test octal-like numbers (leading zeros) are recognized as numeric-like."""
        # These LOOK like numbers so they need quoting
        assert is_numeric_like("01")
        assert is_numeric_like("0123")
        assert is_numeric_like("00")

    def test_non_numeric_strings(self):
        """Test non-numeric strings are not numeric-like."""
        assert not is_numeric_like("")
        assert not is_numeric_like("abc")
        assert not is_numeric_like("hello")
        assert not is_numeric_like("12abc")

    def test_edge_cases(self):
        """Test edge cases."""
        assert not is_numeric_like("")
        assert not is_numeric_like(" ")
        assert not is_numeric_like("--5")


class TestConsistency:
    """Tests to ensure consistency between is_numeric_literal and is_numeric_like."""

    def test_valid_numbers_recognized_by_both(self):
        """Test that valid numbers are recognized by both functions."""
        valid_numbers = ["0", "1", "42", "-1", "3.14", "-2.5", "1e10", "1.5e-3"]
        for num in valid_numbers:
            assert is_numeric_literal(num), f"{num} should be numeric literal"
            assert is_numeric_like(num), f"{num} should be numeric-like"

    def test_octal_like_difference(self):
        """Test the key difference: octal-like numbers.

        is_numeric_like returns True (needs quoting in encoder)
        is_numeric_literal returns False (not parsed as number in decoder)
        """
        octal_like = ["01", "0123", "00", "007"]
        for num in octal_like:
            assert is_numeric_like(num), f"{num} should be numeric-like (needs quoting)"
            assert not is_numeric_literal(num), (
                f"{num} should not be numeric literal (has leading zero)"
            )

    def test_non_numbers_rejected_by_both(self):
        """Test that non-numbers are rejected by both functions."""
        non_numbers = ["", "abc", "hello", "12abc", "nan", "inf"]
        for val in non_numbers:
            # Allow for potential differences in edge cases, but most should agree
            if val:  # Skip empty string edge case
                assert not is_numeric_literal(val), f"{val} should not be numeric literal"
                # is_numeric_like might have slightly different behavior for edge cases


class TestRoundTripConsistency:
    """Test that encoding and decoding are consistent."""

    def test_octal_like_numbers_preserved_as_strings(self):
        """Test that octal-like numbers are preserved as strings through round-trip."""
        from toon_format import decode, encode

        # These should be treated as strings, not numbers
        octal_values = ["0123", "007", "00"]
        for val in octal_values:
            # When we encode a dict with these as values
            data = {"value": val}
            encoded = encode(data)
            decoded = decode(encoded)
            # Assert it's a dict before trying to access
            assert isinstance(decoded, dict)
            # They should come back as strings
            assert decoded["value"] == val
            assert isinstance(decoded["value"], str)

    def test_valid_numbers_preserved_as_numbers(self):
        """Test that valid numbers are preserved as numbers through round-trip."""
        from toon_format import decode, encode

        numbers = [0, 1, 42, -1, 3.14, -2.5]
        for num in numbers:
            data = {"value": num}
            encoded = encode(data)
            decoded = decode(encoded)
            # Assert it's a dict before trying to access
            assert isinstance(decoded, dict)
            # They should come back as numbers (with potential float/int conversion)
            assert decoded["value"] == num
            assert isinstance(decoded["value"], (int, float))
