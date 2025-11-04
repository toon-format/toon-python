"""Tests for the _scanner module."""

import pytest

from toon_format._scanner import (
    BlankLineInfo,
    LineCursor,
    ParsedLine,
    to_parsed_lines,
)


class TestParsedLine:
    """Tests for ParsedLine dataclass."""

    def test_is_blank_with_empty_content(self):
        """Test is_blank returns True for empty content."""
        line = ParsedLine(raw="    ", depth=0, indent=4, content="", line_num=1)
        assert line.is_blank is True

    def test_is_blank_with_whitespace_content(self):
        """Test is_blank returns True for whitespace-only content."""
        line = ParsedLine(raw="    \t  ", depth=0, indent=4, content="\t  ", line_num=1)
        assert line.is_blank is True

    def test_is_blank_with_actual_content(self):
        """Test is_blank returns False for non-blank content."""
        line = ParsedLine(raw="name: Alice", depth=0, indent=0, content="name: Alice", line_num=1)
        assert line.is_blank is False


class TestLineCursor:
    """Tests for LineCursor class."""

    def test_get_blank_lines_with_empty_list(self):
        """Test get_blank_lines returns empty list when none provided."""
        cursor = LineCursor([])
        assert cursor.get_blank_lines() == []

    def test_get_blank_lines_with_provided_blanks(self):
        """Test get_blank_lines returns the provided blank lines."""
        blanks = [BlankLineInfo(line_num=2, indent=0, depth=0)]
        cursor = LineCursor([], blank_lines=blanks)
        assert cursor.get_blank_lines() == blanks

    def test_peek_when_at_end(self):
        """Test peek returns None when cursor is at end."""
        line = ParsedLine(raw="test", depth=0, indent=0, content="test", line_num=1)
        cursor = LineCursor([line])
        cursor.advance()
        assert cursor.peek() is None

    def test_next_when_at_end(self):
        """Test next returns None when cursor is at end."""
        line = ParsedLine(raw="test", depth=0, indent=0, content="test", line_num=1)
        cursor = LineCursor([line])
        cursor.next()  # Consume the only line
        assert cursor.next() is None

    def test_current_when_no_line_consumed(self):
        """Test current returns None when no line has been consumed yet."""
        line = ParsedLine(raw="test", depth=0, indent=0, content="test", line_num=1)
        cursor = LineCursor([line])
        assert cursor.current() is None

    def test_current_after_consuming_line(self):
        """Test current returns the last consumed line."""
        line = ParsedLine(raw="test", depth=0, indent=0, content="test", line_num=1)
        cursor = LineCursor([line])
        cursor.next()
        assert cursor.current() == line

    def test_advance(self):
        """Test advance moves cursor forward."""
        lines = [
            ParsedLine(raw="line1", depth=0, indent=0, content="line1", line_num=1),
            ParsedLine(raw="line2", depth=0, indent=0, content="line2", line_num=2),
        ]
        cursor = LineCursor(lines)
        assert cursor.peek() == lines[0]
        cursor.advance()
        assert cursor.peek() == lines[1]

    def test_at_end_when_not_at_end(self):
        """Test at_end returns False when not at end."""
        line = ParsedLine(raw="test", depth=0, indent=0, content="test", line_num=1)
        cursor = LineCursor([line])
        assert cursor.at_end() is False

    def test_at_end_when_at_end(self):
        """Test at_end returns True when at end."""
        line = ParsedLine(raw="test", depth=0, indent=0, content="test", line_num=1)
        cursor = LineCursor([line])
        cursor.advance()
        assert cursor.at_end() is True

    def test_length_property(self):
        """Test length property returns total number of lines."""
        lines = [
            ParsedLine(raw="line1", depth=0, indent=0, content="line1", line_num=1),
            ParsedLine(raw="line2", depth=0, indent=0, content="line2", line_num=2),
            ParsedLine(raw="line3", depth=0, indent=0, content="line3", line_num=3),
        ]
        cursor = LineCursor(lines)
        assert cursor.length == 3

    def test_peek_at_depth_matching_depth(self):
        """Test peek_at_depth returns line when depth matches."""
        line = ParsedLine(raw="  test", depth=1, indent=2, content="test", line_num=1)
        cursor = LineCursor([line])
        assert cursor.peek_at_depth(1) == line

    def test_peek_at_depth_when_depth_too_shallow(self):
        """Test peek_at_depth returns None when line depth is too shallow."""
        line = ParsedLine(raw="test", depth=0, indent=0, content="test", line_num=1)
        cursor = LineCursor([line])
        assert cursor.peek_at_depth(1) is None

    def test_peek_at_depth_when_depth_too_deep(self):
        """Test peek_at_depth returns None when line depth is too deep."""
        line = ParsedLine(raw="    test", depth=2, indent=4, content="test", line_num=1)
        cursor = LineCursor([line])
        assert cursor.peek_at_depth(1) is None

    def test_peek_at_depth_when_no_line(self):
        """Test peek_at_depth returns None when no line available."""
        cursor = LineCursor([])
        assert cursor.peek_at_depth(0) is None

    def test_has_more_at_depth_when_true(self):
        """Test has_more_at_depth returns True when line exists at depth."""
        line = ParsedLine(raw="  test", depth=1, indent=2, content="test", line_num=1)
        cursor = LineCursor([line])
        assert cursor.has_more_at_depth(1) is True

    def test_has_more_at_depth_when_false(self):
        """Test has_more_at_depth returns False when no line at depth."""
        line = ParsedLine(raw="test", depth=0, indent=0, content="test", line_num=1)
        cursor = LineCursor([line])
        assert cursor.has_more_at_depth(1) is False

    def test_skip_deeper_than(self):
        """Test skip_deeper_than skips all deeper lines."""
        lines = [
            ParsedLine(raw="line1", depth=1, indent=2, content="line1", line_num=1),
            ParsedLine(raw="line2", depth=2, indent=4, content="line2", line_num=2),
            ParsedLine(raw="line3", depth=2, indent=4, content="line3", line_num=3),
            ParsedLine(raw="line4", depth=1, indent=2, content="line4", line_num=4),
        ]
        cursor = LineCursor(lines)
        cursor.next()  # Consume first line at depth 1
        cursor.skip_deeper_than(1)
        # Should skip lines 2 and 3 (depth 2) and stop at line 4 (depth 1)
        assert cursor.peek() == lines[3]

    def test_skip_deeper_than_when_all_deeper(self):
        """Test skip_deeper_than skips all remaining lines when all are deeper."""
        lines = [
            ParsedLine(raw="line1", depth=1, indent=2, content="line1", line_num=1),
            ParsedLine(raw="line2", depth=2, indent=4, content="line2", line_num=2),
            ParsedLine(raw="line3", depth=3, indent=6, content="line3", line_num=3),
        ]
        cursor = LineCursor(lines)
        cursor.next()  # Consume first line
        cursor.skip_deeper_than(1)
        assert cursor.at_end() is True


class TestToParsedLines:
    """Tests for to_parsed_lines function."""

    def test_empty_source(self):
        """Test empty source returns empty lists."""
        lines, blanks = to_parsed_lines("", 2, True)
        assert lines == []
        assert blanks == []

    def test_whitespace_only_source(self):
        """Test whitespace-only source returns empty lists."""
        lines, blanks = to_parsed_lines("   \n  \n", 2, True)
        assert lines == []
        assert blanks == []

    def test_blank_line_tracking(self):
        """Test blank lines are tracked correctly."""
        source = "name: Alice\n\n  age: 30"
        lines, blanks = to_parsed_lines(source, 2, False)
        assert len(blanks) == 1
        assert blanks[0].line_num == 2
        assert blanks[0].indent == 0
        assert blanks[0].depth == 0

    def test_strict_mode_tabs_in_indentation(self):
        """Test strict mode rejects tabs in indentation."""
        source = "\tname: Alice"
        with pytest.raises(SyntaxError, match="Tabs not allowed"):
            to_parsed_lines(source, 2, True)

    def test_strict_mode_invalid_indent_multiple(self):
        """Test strict mode rejects invalid indent multiples."""
        source = "name: Alice\n   age: 30"  # 3 spaces, not multiple of 2
        with pytest.raises(SyntaxError, match="exact multiple"):
            to_parsed_lines(source, 2, True)

    def test_lenient_mode_accepts_tabs(self):
        """Test lenient mode accepts tabs in indentation."""
        source = "\tname: Alice"
        lines, blanks = to_parsed_lines(source, 2, False)
        # Should not raise error
        assert len(lines) == 1

    def test_lenient_mode_accepts_invalid_multiples(self):
        """Test lenient mode accepts invalid indent multiples."""
        source = "name: Alice\n   age: 30"  # 3 spaces
        lines, blanks = to_parsed_lines(source, 2, False)
        # Should not raise error
        assert len(lines) == 2
        assert lines[1].depth == 1  # 3 // 2 = 1

    def test_depth_calculation(self):
        """Test depth is calculated correctly from indentation."""
        source = "level0\n  level1\n    level2\n      level3"
        lines, blanks = to_parsed_lines(source, 2, True)
        assert lines[0].depth == 0
        assert lines[1].depth == 1
        assert lines[2].depth == 2
        assert lines[3].depth == 3

    def test_line_numbers_are_one_based(self):
        """Test line numbers start at 1."""
        source = "line1\nline2\nline3"
        lines, blanks = to_parsed_lines(source, 2, True)
        assert lines[0].line_num == 1
        assert lines[1].line_num == 2
        assert lines[2].line_num == 3

    def test_blank_lines_not_validated_in_strict_mode(self):
        """Test blank lines are not validated for indentation in strict mode."""
        source = "name: Alice\n   \n  age: 30"  # Blank line with 3 spaces
        lines, blanks = to_parsed_lines(source, 2, True)
        # Should not raise error for blank line with invalid indentation
        assert len(blanks) == 1
        assert blanks[0].line_num == 2
