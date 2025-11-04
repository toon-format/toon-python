"""Tests for _parsing_utils module.

These tests verify the quote-aware parsing utilities used throughout
the TOON decoder.
"""

import pytest

from src.toon_format._parsing_utils import (
    find_first_unquoted,
    find_unquoted_char,
    iter_unquoted,
    parse_delimited_values,
    split_at_unquoted_char,
)


class TestIterUnquoted:
    """Tests for iter_unquoted() generator."""

    def test_simple_string_no_quotes(self):
        """Iterate over simple string with no quotes."""
        result = list(iter_unquoted("abc"))
        assert result == [(0, "a", False), (1, "b", False), (2, "c", False)]

    def test_quoted_section(self):
        """Iterate over string with quoted section."""
        result = list(iter_unquoted('a"bc"d'))
        assert result == [
            (0, "a", False),
            (1, '"', False),  # Opening quote
            (2, "b", True),
            (3, "c", True),
            (4, '"', True),  # Closing quote
            (5, "d", False),
        ]

    def test_escaped_char_in_quotes(self):
        """Handle escaped characters within quotes."""
        result = list(iter_unquoted(r'a"b\\"c"d'))
        assert result == [
            (0, "a", False),
            (1, '"', False),
            (2, "b", True),
            (3, "\\", True),  # Backslash
            (4, "\\", True),  # Escaped backslash
            (5, '"', True),
            (6, "c", False),  # Outside quotes
            (7, '"', False),  # Opening quote again
            (8, "d", True),  # Inside quotes
        ]

    def test_start_position(self):
        """Start iteration from specific position."""
        result = list(iter_unquoted("abcde", start=2))
        assert result == [(2, "c", False), (3, "d", False), (4, "e", False)]

    def test_empty_string(self):
        """Handle empty string."""
        result = list(iter_unquoted(""))
        assert result == []

    def test_only_quotes(self):
        """Handle string with only quotes."""
        result = list(iter_unquoted('""'))
        assert result == [(0, '"', False), (1, '"', True)]

    def test_nested_quotes_behavior(self):
        """Quotes toggle state (no true nesting in TOON)."""
        result = list(iter_unquoted('"a"b"c"'))
        expected = [
            (0, '"', False),
            (1, "a", True),
            (2, '"', True),
            (3, "b", False),
            (4, '"', False),
            (5, "c", True),
            (6, '"', True),
        ]
        assert result == expected


class TestFindUnquotedChar:
    """Tests for find_unquoted_char() function."""

    def test_find_colon_simple(self):
        """Find colon in simple string."""
        assert find_unquoted_char("key: value", ":") == 3

    def test_find_colon_with_quoted_colon(self):
        """Ignore colon inside quotes."""
        assert find_unquoted_char('"key:1": value', ":") == 7

    def test_find_bracket_with_quoted_bracket(self):
        """Ignore bracket inside quotes."""
        assert find_unquoted_char('"key[test]"[3]:', "[") == 11

    def test_char_not_found(self):
        """Return -1 when character not found."""
        assert find_unquoted_char("abcdef", ":") == -1

    def test_char_only_in_quotes(self):
        """Return -1 when character only in quotes."""
        assert find_unquoted_char('"a:b"', ":") == -1

    def test_multiple_occurrences(self):
        """Find first occurrence outside quotes."""
        assert find_unquoted_char("a:b:c", ":") == 1

    def test_start_position(self):
        """Start search from specific position."""
        assert find_unquoted_char("a:b:c", ":", start=2) == 3

    def test_escaped_quote_before_target(self):
        """Handle escaped quotes correctly."""
        # "a\"b":value -> colon at position 6
        assert find_unquoted_char(r'"a\"b":value', ":") == 6

    def test_empty_string(self):
        """Handle empty string."""
        assert find_unquoted_char("", ":") == -1

    def test_delimiter_comma(self):
        """Find comma delimiter."""
        assert find_unquoted_char('a,"b,c",d', ",") == 1

    def test_delimiter_pipe(self):
        """Find pipe delimiter."""
        assert find_unquoted_char('a|"b|c"|d', "|") == 1


class TestParseDelimitedValues:
    """Tests for parse_delimited_values() function."""

    def test_simple_comma_separated(self):
        """Parse simple comma-separated values."""
        assert parse_delimited_values("a,b,c", ",") == ["a", "b", "c"]

    def test_values_with_quotes(self):
        """Parse values containing quoted sections."""
        assert parse_delimited_values('a,"b,c",d', ",") == ["a", '"b,c"', "d"]

    def test_tab_delimiter(self):
        """Parse tab-separated values."""
        assert parse_delimited_values("a\tb\tc", "\t") == ["a", "b", "c"]

    def test_pipe_delimiter(self):
        """Parse pipe-separated values."""
        assert parse_delimited_values("a|b|c", "|") == ["a", "b", "c"]

    def test_empty_values(self):
        """Handle empty values between delimiters."""
        assert parse_delimited_values("a,,c", ",") == ["a", "", "c"]

    def test_trailing_delimiter(self):
        """Handle trailing delimiter."""
        assert parse_delimited_values("a,b,", ",") == ["a", "b", ""]

    def test_leading_delimiter(self):
        """Handle leading delimiter."""
        assert parse_delimited_values(",a,b", ",") == ["", "a", "b"]

    def test_only_delimiter(self):
        """Handle string with only delimiter."""
        assert parse_delimited_values(",", ",") == ["", ""]

    def test_no_delimiter(self):
        """Handle string with no delimiter."""
        assert parse_delimited_values("abc", ",") == ["abc"]

    def test_empty_string(self):
        """Handle empty string."""
        assert parse_delimited_values("", ",") == []

    def test_quoted_with_escaped_quote(self):
        """Handle quoted value with escaped quote."""
        result = parse_delimited_values(r'"a\"b",c', ",")
        assert result == [r'"a\"b"', "c"]

    def test_multiple_quoted_sections(self):
        """Handle multiple quoted sections."""
        result = parse_delimited_values('"a,b","c,d","e,f"', ",")
        assert result == ['"a,b"', '"c,d"', '"e,f"']

    def test_spec_example_with_delimiters_in_strings(self):
        """Test spec example: strings with delimiters."""
        result = parse_delimited_values('a,"b,c","d:e"', ",")
        assert result == ["a", '"b,c"', '"d:e"']

    def test_preserves_whitespace(self):
        """Whitespace is preserved (not stripped)."""
        assert parse_delimited_values(" a , b , c ", ",") == [" a ", " b ", " c "]


class TestSplitAtUnquotedChar:
    """Tests for split_at_unquoted_char() function."""

    def test_simple_split_on_colon(self):
        """Split simple string on colon."""
        assert split_at_unquoted_char("key: value", ":") == ("key", " value")

    def test_split_with_quoted_colon(self):
        """Split at unquoted colon, ignoring quoted colon."""
        assert split_at_unquoted_char('"key:1": value', ":") == ('"key:1"', " value")

    def test_split_on_equals(self):
        """Split on equals sign."""
        assert split_at_unquoted_char("key=value", "=") == ("key", "value")

    def test_char_not_found_raises_error(self):
        """Raise ValueError when character not found."""
        with pytest.raises(ValueError, match="not found outside quotes"):
            split_at_unquoted_char("no colon here", ":")

    def test_char_only_in_quotes_raises_error(self):
        """Raise ValueError when character only in quotes."""
        with pytest.raises(ValueError, match="not found outside quotes"):
            split_at_unquoted_char('"a:b"', ":")

    def test_multiple_occurrences(self):
        """Split at first occurrence."""
        assert split_at_unquoted_char("a:b:c", ":") == ("a", "b:c")

    def test_empty_before(self):
        """Handle empty string before delimiter."""
        assert split_at_unquoted_char(":value", ":") == ("", "value")

    def test_empty_after(self):
        """Handle empty string after delimiter."""
        assert split_at_unquoted_char("key:", ":") == ("key", "")


class TestFindFirstUnquoted:
    """Tests for find_first_unquoted() function."""

    def test_find_first_of_multiple_chars(self):
        """Find first occurrence of any character."""
        assert find_first_unquoted("a:b,c", [":", ","]) == (1, ":")

    def test_comma_before_colon(self):
        """Find comma when it appears before colon."""
        assert find_first_unquoted("a,b:c", [":", ","]) == (1, ",")

    def test_ignore_quoted_chars(self):
        """Ignore characters inside quotes."""
        assert find_first_unquoted('a"b:c",d', [":", ","]) == (6, ",")

    def test_no_chars_found(self):
        """Return (-1, '') when none found."""
        assert find_first_unquoted("abcdef", [":", ","]) == (-1, "")

    def test_all_chars_in_quotes(self):
        """Return (-1, '') when all in quotes."""
        assert find_first_unquoted('"a:b,c"', [":", ","]) == (-1, "")

    def test_start_position(self):
        """Start search from specific position."""
        assert find_first_unquoted("a:b,c", [":", ","], start=2) == (3, ",")

    def test_single_char_list(self):
        """Work with single-character list."""
        assert find_first_unquoted("a:b", [":"]) == (1, ":")

    def test_empty_char_list(self):
        """Handle empty character list."""
        assert find_first_unquoted("a:b,c", []) == (-1, "")

    def test_empty_string(self):
        """Handle empty string."""
        assert find_first_unquoted("", [":", ","]) == (-1, "")


class TestEdgeCases:
    """Edge cases and integration scenarios."""

    def test_extremely_long_quoted_section(self):
        """Handle very long quoted sections."""
        long_quoted = '"' + "a" * 1000 + '"'
        result = find_unquoted_char(long_quoted + ":value", ":")
        assert result == 1002  # After the 1000 a's and 2 quotes

    def test_many_escaped_chars(self):
        """Handle many escaped characters."""
        escaped = r'"' + r"\\" * 50 + '"'
        result = list(iter_unquoted(escaped))
        # Should have opening quote + 100 chars (50 pairs) + closing quote
        assert len(result) == 102

    def test_unicode_characters(self):
        """Handle unicode characters correctly."""
        assert find_unquoted_char("café:☕", ":") == 4

    def test_delimiter_at_boundary(self):
        """Handle delimiter at string boundaries."""
        assert parse_delimited_values(",", ",") == ["", ""]
        assert parse_delimited_values(",,", ",") == ["", "", ""]

    def test_mixed_delimiters_in_quotes(self):
        """Multiple different delimiters in quotes."""
        result = parse_delimited_values('"a:b|c,d",e', ",")
        assert result == ['"a:b|c,d"', "e"]

    def test_realistic_toon_header(self):
        """Test with realistic TOON header."""
        # Example: "key[test]"[3]: 1,2,3
        header = '"key[test]"[3]: 1,2,3'
        bracket_pos = find_unquoted_char(header, "[")
        assert bracket_pos == 11  # First [ outside quotes

        colon_pos = find_unquoted_char(header, ":")
        assert colon_pos == 14  # : outside quotes

        values = parse_delimited_values("1,2,3", ",")
        assert values == ["1", "2", "3"]

    def test_realistic_tabular_row_detection(self):
        """Test realistic tabular row vs key-value detection."""
        # Row: values separated by delimiter, no colon or delimiter before colon
        row = "Alice,30,Engineer"
        assert find_unquoted_char(row, ":") == -1  # No colon = row

        # Key-value: colon before delimiter
        kv = "name: Alice,Bob"
        colon = find_unquoted_char(kv, ":")
        comma = find_unquoted_char(kv, ",")
        assert colon < comma  # Colon first = key-value

        # Row with quoted field containing colon
        row_with_quote = 'Alice,"30:manager",Engineer'
        first_comma = find_unquoted_char(row_with_quote, ",")
        first_colon = find_unquoted_char(row_with_quote, ":")
        assert first_colon == -1  # Colon only in quotes = row
