"""Security tests for TOON format (Section 15 of spec).

Tests resource exhaustion, malicious input handling, and security considerations
from the TOON specification Section 15.
"""

import pytest

from toon_format import decode, encode
from toon_format.types import DecodeOptions


class TestResourceExhaustion:
    """Tests for resource exhaustion scenarios."""

    def test_deeply_nested_objects_handled(self):
        """Test that deeply nested objects are handled without stack overflow."""
        # Create a deeply nested structure (100 levels)
        data = {"level": 0}
        current = data
        for i in range(1, 100):
            current["nested"] = {"level": i}
            current = current["nested"]

        # Should encode without stack overflow
        result = encode(data)
        assert "level: 0" in result

        # Should decode without stack overflow
        decoded = decode(result)
        assert decoded["level"] == 0

    def test_deeply_nested_mixed_structures(self):
        """Test that deeply nested mixed structures don't cause stack overflow."""
        # Create a mixed nested structure with objects and arrays
        data = {"items": [{"nested": [{"deep": [1, 2, 3]}]}]}

        # Nest it further
        for _ in range(10):
            data = {"level": data}

        # Should encode without stack overflow
        result = encode(data)
        assert "level:" in result

        # Should decode without stack overflow
        decoded = decode(result)
        assert "level" in decoded
        assert isinstance(decoded, dict)

    def test_very_long_string_handled(self):
        """Test that very long strings are handled efficiently."""
        # Create a 1MB string
        long_string = "a" * (1024 * 1024)
        data = {"text": long_string}

        # Should encode without memory issues
        result = encode(data)
        assert "text:" in result

        # Should decode without memory issues
        decoded = decode(result)
        assert len(decoded["text"]) == 1024 * 1024

    def test_large_array_handled(self):
        """Test that large arrays are handled efficiently."""
        # Create an array with 10,000 elements
        data = {"items": list(range(10000))}

        # Should encode without memory issues
        result = encode(data)
        assert "items[10000]:" in result

        # Should decode without memory issues
        decoded = decode(result)
        assert len(decoded["items"]) == 10000

    def test_large_tabular_array_handled(self):
        """Test that large tabular arrays are handled efficiently."""
        # Create a tabular array with 1000 rows
        data = {"users": [{"id": i, "name": f"user{i}"} for i in range(1000)]}

        # Should encode without memory issues
        result = encode(data)
        assert "users[1000]" in result

        # Should decode without memory issues
        decoded = decode(result)
        assert len(decoded["users"]) == 1000

    def test_many_object_keys_handled(self):
        """Test that objects with many keys are handled."""
        # Create object with 1000 keys
        data = {f"key{i}": i for i in range(1000)}

        # Should encode without issues
        result = encode(data)
        assert "key0:" in result
        assert "key999:" in result

        # Should decode without issues
        decoded = decode(result)
        assert len(decoded) == 1000


class TestMaliciousInput:
    """Tests for malicious or malformed input handling."""

    def test_unterminated_string_raises_error(self):
        """Test that unterminated strings are rejected."""
        malformed = 'name: "unterminated'

        with pytest.raises(Exception):  # Should raise decode error
            decode(malformed)

    def test_invalid_escape_sequence_raises_error(self):
        """Test that invalid escape sequences are rejected."""
        malformed = 'text: "bad\\xescape"'

        with pytest.raises(Exception):  # Should raise decode error
            decode(malformed)

    def test_circular_reference_in_encoding(self):
        """Test that circular references are handled (Python-specific)."""
        # Python allows circular references
        data = {"self": None}
        data["self"] = data  # Circular reference

        # Should detect and handle circular reference gracefully
        # (normalize_value should convert to null or handle it)
        try:
            result = encode(data)
            # If it succeeds, it should have normalized the circular ref
            # This is implementation-specific behavior
            assert result is not None
        except (RecursionError, ValueError):
            # It's acceptable to raise an error for circular refs
            pass

    def test_injection_via_delimiter_in_value(self):
        """Test that delimiter injection is prevented by quoting."""
        # Try to inject extra array values via unquoted delimiter
        data = {"items": ["a,b", "c"]}  # Comma in first value

        result = encode(data)
        # The comma should be quoted to prevent injection
        assert '"a,b"' in result or "a\\,b" in result or result.count(",") == 1

        decoded = decode(result)
        assert decoded["items"] == ["a,b", "c"]
        assert len(decoded["items"]) == 2  # Should be 2, not 3

    def test_injection_via_colon_in_value(self):
        """Test that colon injection is prevented by quoting."""
        # Try to inject a key-value pair via unquoted colon
        data = {"text": "fake: value"}

        result = encode(data)
        # The colon should be quoted
        assert '"fake: value"' in result

        decoded = decode(result)
        assert decoded == {"text": "fake: value"}
        assert "fake" not in decoded  # Should not create separate key

    def test_injection_via_hyphen_in_list(self):
        """Test that hyphen injection is prevented."""
        # Try to inject list items via hyphen at start
        data = ["- injected"]

        result = encode(data)
        # The hyphen should be quoted
        assert '"- injected"' in result

        decoded = decode(result)
        assert decoded == ["- injected"]

    def test_injection_via_brackets_in_value(self):
        """Test that bracket injection is prevented."""
        # Try to inject array header via brackets
        data = {"text": "[10]: fake,array"}

        result = encode(data)
        # Brackets should be quoted
        assert '"[10]: fake,array"' in result

        decoded = decode(result)
        assert decoded == {"text": "[10]: fake,array"}

    def test_tab_in_indentation_rejected_strict_mode(self):
        """Test that tabs in indentation are rejected in strict mode."""
        # Malicious input with tab instead of spaces
        malformed = "name: Alice\n\tage: 30"  # Tab used for indentation

        with pytest.raises(Exception):  # Should raise error
            decode(malformed, DecodeOptions(strict=True))

    def test_invalid_indentation_rejected_strict_mode(self):
        """Test that invalid indentation multiples are rejected."""
        # Indentation not a multiple of indent size
        malformed = "name: Alice\n   age: 30"  # 3 spaces, not multiple of 2

        with pytest.raises(Exception):
            decode(malformed, DecodeOptions(strict=True, indent=2))

    def test_count_mismatch_detected_strict_mode(self):
        """Test that array count mismatches are detected (security via validation)."""
        # Declare 5 items but only provide 3 (potential truncation attack)
        malformed = "items[5]: 1,2,3"

        with pytest.raises(Exception):
            decode(malformed, DecodeOptions(strict=True))

    def test_tabular_width_mismatch_detected(self):
        """Test that tabular width mismatches are detected."""
        # Declare 3 fields but provide 2 values (injection or truncation)
        malformed = "users[2]{id,name,age}:\n  1,Alice\n  2,Bob"

        with pytest.raises(Exception):
            decode(malformed, DecodeOptions(strict=True))

    def test_blank_line_in_array_rejected_strict_mode(self):
        """Test that blank lines in arrays are rejected (prevents injection)."""
        malformed = "items[3]:\n  - a\n\n  - b\n  - c"  # Blank line in array

        with pytest.raises(Exception):
            decode(malformed, DecodeOptions(strict=True))


class TestQuotingSecurityInvariants:
    """Test that quoting rules prevent ambiguity and injection."""

    def test_reserved_literals_quoted(self):
        """Test that reserved literals are quoted when used as strings."""
        data = {"values": ["true", "false", "null"]}

        result = encode(data)
        # These should be quoted to avoid ambiguity
        assert '"true"' in result
        assert '"false"' in result
        assert '"null"' in result

        decoded = decode(result)
        assert decoded["values"] == ["true", "false", "null"]
        assert all(isinstance(v, str) for v in decoded["values"])

    def test_numeric_strings_quoted(self):
        """Test that numeric-looking strings are quoted."""
        data = {"codes": ["123", "3.14", "1e5", "-42"]}

        result = encode(data)
        # All should be quoted to preserve string type
        for code in ["123", "3.14", "1e5", "-42"]:
            assert f'"{code}"' in result

        decoded = decode(result)
        assert decoded["codes"] == ["123", "3.14", "1e5", "-42"]
        assert all(isinstance(v, str) for v in decoded["codes"])

    def test_octal_like_strings_quoted(self):
        """Test that octal-like strings are quoted (leading zeros)."""
        data = {"codes": ["0123", "0755"]}

        result = encode(data)
        assert '"0123"' in result
        assert '"0755"' in result

        decoded = decode(result)
        assert decoded["codes"] == ["0123", "0755"]

    def test_empty_string_quoted(self):
        """Test that empty strings are quoted."""
        data = {"empty": ""}

        result = encode(data)
        assert 'empty: ""' in result

        decoded = decode(result)
        assert decoded["empty"] == ""

    def test_whitespace_strings_quoted(self):
        """Test that strings with leading/trailing whitespace are quoted."""
        data = {"values": [" space", "space ", " both "]}

        result = encode(data)
        assert '" space"' in result
        assert '"space "' in result
        assert '" both "' in result

        decoded = decode(result)
        assert decoded["values"] == [" space", "space ", " both "]

    def test_control_characters_escaped(self):
        """Test that control characters are properly escaped."""
        data = {"text": "line1\nline2\ttab\rreturn"}

        result = encode(data)
        # Should contain escaped sequences
        assert "\\n" in result
        assert "\\t" in result
        assert "\\r" in result

        decoded = decode(result)
        assert decoded["text"] == "line1\nline2\ttab\rreturn"
