"""Tests for the _string_utils module."""

import pytest

from toon_format._string_utils import (
    escape_string,
    find_closing_quote,
    find_unquoted_char,
    unescape_string,
)


class TestEscapeString:
    """Tests for escape_string function."""

    def test_escape_backslash(self):
        """Test backslashes are escaped correctly."""
        assert escape_string("path\\to\\file") == "path\\\\to\\\\file"

    def test_escape_double_quote(self):
        """Test double quotes are escaped correctly."""
        assert escape_string('say "hello"') == 'say \\"hello\\"'

    def test_escape_newline(self):
        """Test newlines are escaped correctly."""
        assert escape_string("line1\nline2") == "line1\\nline2"

    def test_escape_carriage_return(self):
        """Test carriage returns are escaped correctly."""
        assert escape_string("line1\rline2") == "line1\\rline2"

    def test_escape_tab(self):
        """Test tabs are escaped correctly."""
        assert escape_string("col1\tcol2") == "col1\\tcol2"

    def test_escape_all_special_chars(self):
        """Test all special characters are escaped in one string."""
        input_str = 'test\n\r\t\\"value"'
        expected = 'test\\n\\r\\t\\\\\\"value\\"'
        assert escape_string(input_str) == expected

    def test_escape_empty_string(self):
        """Test empty string remains empty."""
        assert escape_string("") == ""

    def test_escape_no_special_chars(self):
        """Test string without special chars is unchanged."""
        assert escape_string("hello world") == "hello world"


class TestUnescapeString:
    """Tests for unescape_string function."""

    def test_unescape_newline(self):
        """Test \\n is unescaped to newline."""
        assert unescape_string("hello\\nworld") == "hello\nworld"

    def test_unescape_tab(self):
        """Test \\t is unescaped to tab."""
        assert unescape_string("col1\\tcol2") == "col1\tcol2"

    def test_unescape_carriage_return(self):
        """Test \\r is unescaped to carriage return."""
        assert unescape_string("line1\\rline2") == "line1\rline2"

    def test_unescape_backslash(self):
        """Test \\\\ is unescaped to single backslash."""
        assert unescape_string("path\\\\to\\\\file") == "path\\to\\file"

    def test_unescape_double_quote(self):
        """Test \\" is unescaped to double quote."""
        assert unescape_string('say \\"hello\\"') == 'say "hello"'

    def test_unescape_all_sequences(self):
        """Test all escape sequences are unescaped correctly."""
        input_str = 'test\\n\\r\\t\\\\\\"value\\"'
        expected = 'test\n\r\t\\"value"'
        assert unescape_string(input_str) == expected

    def test_unescape_empty_string(self):
        """Test empty string remains empty."""
        assert unescape_string("") == ""

    def test_unescape_no_escapes(self):
        """Test string without escapes is unchanged."""
        assert unescape_string("hello world") == "hello world"

    def test_unescape_backslash_at_end_raises_error(self):
        """Test backslash at end of string raises ValueError."""
        with pytest.raises(ValueError, match="backslash at end of string"):
            unescape_string("test\\")

    def test_unescape_invalid_escape_sequence_raises_error(self):
        """Test invalid escape sequence raises ValueError."""
        with pytest.raises(ValueError, match="Invalid escape sequence"):
            unescape_string("test\\x")

    def test_unescape_preserves_non_escaped_backslash_followed_by_valid_char(self):
        """Test that only valid escape sequences are processed."""
        # Any backslash followed by a non-escape character should raise error
        with pytest.raises(ValueError, match="Invalid escape sequence"):
            unescape_string("test\\a")


class TestFindClosingQuote:
    """Tests for find_closing_quote function."""

    def test_find_simple_quote(self):
        """Test finding closing quote in simple string."""
        assert find_closing_quote('"hello"', 0) == 6

    def test_find_quote_with_escaped_quote_inside(self):
        """Test finding closing quote when escaped quotes are inside."""
        assert find_closing_quote('"hello \\"world\\""', 0) == 16

    def test_find_quote_with_escaped_backslash(self):
        """Test finding closing quote with escaped backslash before quote."""
        assert find_closing_quote('"path\\\\to\\\\file"', 0) == 15

    def test_find_quote_with_multiple_escapes(self):
        """Test finding closing quote with multiple escape sequences."""
        assert find_closing_quote('"test\\n\\t\\r"', 0) == 11

    def test_find_quote_not_found(self):
        """Test returns -1 when closing quote is not found."""
        assert find_closing_quote('"unclosed string', 0) == -1

    def test_find_quote_empty_string(self):
        """Test finding quote in minimal quoted string."""
        assert find_closing_quote('""', 0) == 1

    def test_find_quote_with_escaped_char_at_end(self):
        """Test finding quote when escaped character is at the end."""
        assert find_closing_quote('"test\\n"', 0) == 7

    def test_find_quote_starts_after_opening(self):
        """Test search starts after the opening quote."""
        # The function starts at position+1 internally
        result = find_closing_quote('"hello"extra', 0)
        assert result == 6


class TestFindUnquotedChar:
    """Tests for find_unquoted_char function."""

    def test_find_char_outside_quotes(self):
        """Test finding character that is outside quotes."""
        assert find_unquoted_char('key: "value"', ":", 0) == 3

    def test_find_char_ignores_char_inside_quotes(self):
        """Test character inside quotes is ignored."""
        assert find_unquoted_char('"key: nested": value', ":", 0) == 13

    def test_find_char_with_multiple_quoted_sections(self):
        """Test finding char with multiple quoted sections."""
        # First unquoted : is right after "first"
        assert find_unquoted_char('"first": "second": third', ":", 0) == 7

    def test_find_char_with_escaped_quote_in_string(self):
        """Test finding char when there are escaped quotes."""
        assert find_unquoted_char('"value\\"with\\"quotes": key', ":", 0) == 21

    def test_find_char_not_found(self):
        """Test returns -1 when character is not found outside quotes."""
        assert find_unquoted_char('"all: inside: quotes"', ":", 0) == -1

    def test_find_char_with_start_offset(self):
        """Test finding char starting from a specific offset."""
        result = find_unquoted_char("first: second: third", ":", 6)
        assert result == 13

    def test_find_char_no_quotes_in_string(self):
        """Test finding char when there are no quotes at all."""
        assert find_unquoted_char("key: value", ":", 0) == 3

    def test_find_char_empty_string(self):
        """Test returns -1 for empty string."""
        assert find_unquoted_char("", ":", 0) == -1

    def test_find_char_only_quoted_string(self):
        """Test returns -1 when entire string is quoted."""
        assert find_unquoted_char('"entire:string:quoted"', ":", 0) == -1

    def test_find_char_unclosed_quote(self):
        """Test behavior with unclosed quote (char after unclosed quote)."""
        # If quote is never closed, everything after is considered "in quotes"
        assert find_unquoted_char('"unclosed: value', ":", 0) == -1

    def test_find_char_escaped_backslash_before_quote(self):
        """Test finding char with escaped backslash before closing quote."""
        # String: "test\\" followed by : outside
        assert find_unquoted_char('"test\\\\": value', ":", 0) == 8

    def test_find_char_with_escaped_char_in_quotes(self):
        """Test that escaped characters inside quotes are properly skipped."""
        # The \\n should be skipped as an escape sequence
        assert find_unquoted_char('"test\\nvalue": key', ":", 0) == 13

    def test_find_char_quote_at_start(self):
        """Test finding char when string starts with a quote."""
        assert find_unquoted_char('"quoted": unquoted', ":", 0) == 8

    def test_find_char_quote_at_end(self):
        """Test finding char when quote is at the end."""
        assert find_unquoted_char('unquoted: "quoted"', ":", 0) == 8

    def test_find_multiple_chars_first_match(self):
        """Test returns first match when character appears multiple times."""
        assert find_unquoted_char("a:b:c", ":", 0) == 1
