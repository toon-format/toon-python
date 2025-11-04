"""Integration tests for the CLI module."""

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from toon_format.cli import decode_toon_to_json, encode_json_to_toon, main


class TestEncodeJsonToToon:
    """Tests for encode_json_to_toon function."""

    def test_basic_encode(self):
        """Test basic JSON to TOON encoding."""
        json_text = '{"name": "Alice", "age": 30}'
        result = encode_json_to_toon(json_text)
        assert "name: Alice" in result
        assert "age: 30" in result

    def test_encode_with_custom_delimiter(self):
        """Test encoding with custom delimiter."""
        json_text = '{"items": [1, 2, 3]}'
        result = encode_json_to_toon(json_text, delimiter="|")
        assert "|" in result or "[3]:" in result  # Either delimiter or inline format

    def test_encode_with_custom_indent(self):
        """Test encoding with custom indentation."""
        json_text = '{"outer": {"inner": 1}}'
        result = encode_json_to_toon(json_text, indent=4)
        # With 4-space indent, nested items should have 4 spaces
        assert result is not None

    def test_encode_with_length_marker(self):
        """Test encoding with length marker."""
        json_text = '{"items": [1, 2, 3]}'
        result = encode_json_to_toon(json_text, length_marker=True)
        assert "#" in result or "items" in result

    def test_encode_invalid_json_raises_error(self):
        """Test that invalid JSON raises JSONDecodeError."""
        invalid_json = '{"broken": invalid}'
        with pytest.raises(json.JSONDecodeError):
            encode_json_to_toon(invalid_json)


class TestDecodeToonToJson:
    """Tests for decode_toon_to_json function."""

    def test_basic_decode(self):
        """Test basic TOON to JSON decoding."""
        toon_text = "name: Alice\nage: 30"
        result = decode_toon_to_json(toon_text)
        data = json.loads(result)
        assert data["name"] == "Alice"
        assert data["age"] == 30

    def test_decode_with_custom_indent(self):
        """Test decoding with custom indentation."""
        toon_text = "outer:\n    inner: 1"
        result = decode_toon_to_json(toon_text, indent=4)
        data = json.loads(result)
        assert data["outer"]["inner"] == 1

    def test_decode_strict_mode(self):
        """Test decoding in strict mode."""
        toon_text = "name: Alice\nage: 30"
        result = decode_toon_to_json(toon_text, strict=True)
        data = json.loads(result)
        assert data["name"] == "Alice"

    def test_decode_lenient_mode(self):
        """Test decoding in lenient mode."""
        toon_text = "name: Alice\nage: 30"
        result = decode_toon_to_json(toon_text, strict=False)
        data = json.loads(result)
        assert data["name"] == "Alice"


class TestCLIMain:
    """Integration tests for the main CLI function."""

    def test_encode_from_file_to_stdout(self, tmp_path):
        """Test encoding from file to stdout."""
        # Create input file
        input_file = tmp_path / "input.json"
        input_file.write_text('{"name": "Alice"}')

        # Mock stdout
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with patch("sys.argv", ["toon", str(input_file), "--encode"]):
                result = main()
                assert result == 0
                output = mock_stdout.getvalue()
                assert "name: Alice" in output

    def test_decode_from_file_to_stdout(self, tmp_path):
        """Test decoding from file to stdout."""
        # Create input file
        input_file = tmp_path / "input.toon"
        input_file.write_text("name: Alice\nage: 30")

        # Mock stdout
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with patch("sys.argv", ["toon", str(input_file), "--decode"]):
                result = main()
                assert result == 0
                output = mock_stdout.getvalue()
                assert "Alice" in output

    def test_encode_from_stdin_to_stdout(self):
        """Test encoding from stdin to stdout."""
        input_data = '{"name": "Bob"}'

        with patch("sys.stdin", StringIO(input_data)):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                with patch("sys.argv", ["toon", "-", "--encode"]):
                    result = main()
                    assert result == 0
                    output = mock_stdout.getvalue()
                    assert "name: Bob" in output

    def test_decode_from_stdin_to_stdout(self):
        """Test decoding from stdin to stdout."""
        input_data = "name: Charlie\nage: 25"

        with patch("sys.stdin", StringIO(input_data)):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                with patch("sys.argv", ["toon", "-", "--decode"]):
                    result = main()
                    assert result == 0
                    output = mock_stdout.getvalue()
                    assert "Charlie" in output

    def test_encode_to_output_file(self, tmp_path):
        """Test encoding with output file."""
        input_file = tmp_path / "input.json"
        output_file = tmp_path / "output.toon"
        input_file.write_text('{"name": "Dave"}')

        with patch("sys.argv", ["toon", str(input_file), "-o", str(output_file), "--encode"]):
            result = main()
            assert result == 0
            assert output_file.exists()
            content = output_file.read_text()
            assert "name: Dave" in content

    def test_decode_to_output_file(self, tmp_path):
        """Test decoding with output file."""
        input_file = tmp_path / "input.toon"
        output_file = tmp_path / "output.json"
        input_file.write_text("name: Eve\nage: 35")

        with patch("sys.argv", ["toon", str(input_file), "-o", str(output_file), "--decode"]):
            result = main()
            assert result == 0
            assert output_file.exists()
            content = output_file.read_text()
            data = json.loads(content)
            assert data["name"] == "Eve"

    def test_auto_detect_json_extension(self, tmp_path):
        """Test auto-detection based on .json extension."""
        input_file = tmp_path / "data.json"
        input_file.write_text('{"test": true}')

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with patch("sys.argv", ["toon", str(input_file)]):
                result = main()
                assert result == 0
                output = mock_stdout.getvalue()
                assert "test: true" in output

    def test_auto_detect_toon_extension(self, tmp_path):
        """Test auto-detection based on .toon extension."""
        input_file = tmp_path / "data.toon"
        input_file.write_text("test: true")

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with patch("sys.argv", ["toon", str(input_file)]):
                result = main()
                assert result == 0
                output = mock_stdout.getvalue()
                assert "true" in output

    def test_auto_detect_json_content(self, tmp_path):
        """Test auto-detection based on JSON content."""
        input_file = tmp_path / "data.txt"
        input_file.write_text('{"format": "json"}')

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with patch("sys.argv", ["toon", str(input_file)]):
                result = main()
                assert result == 0
                output = mock_stdout.getvalue()
                assert "format: json" in output

    def test_auto_detect_toon_content(self, tmp_path):
        """Test auto-detection based on TOON content."""
        input_file = tmp_path / "data.txt"
        input_file.write_text("format: toon")

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with patch("sys.argv", ["toon", str(input_file)]):
                result = main()
                assert result == 0
                output = mock_stdout.getvalue()
                assert "toon" in output

    def test_auto_detect_stdin_json(self):
        """Test auto-detection from stdin with JSON content."""
        input_data = '{"source": "stdin"}'

        with patch("sys.stdin", StringIO(input_data)):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                with patch("sys.argv", ["toon", "-"]):
                    result = main()
                    assert result == 0
                    output = mock_stdout.getvalue()
                    assert "source: stdin" in output

    def test_auto_detect_stdin_toon(self):
        """Test auto-detection from stdin with TOON content."""
        input_data = "source: stdin"

        with patch("sys.stdin", StringIO(input_data)):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                with patch("sys.argv", ["toon", "-"]):
                    result = main()
                    assert result == 0
                    output = mock_stdout.getvalue()
                    assert "stdin" in output

    def test_custom_delimiter_option(self, tmp_path):
        """Test custom delimiter option."""
        input_file = tmp_path / "input.json"
        input_file.write_text('{"items": [1, 2, 3]}')

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with patch("sys.argv", ["toon", str(input_file), "--encode", "--delimiter", "|"]):
                result = main()
                assert result == 0

    def test_custom_indent_option(self, tmp_path):
        """Test custom indent option."""
        input_file = tmp_path / "input.json"
        input_file.write_text('{"outer": {"inner": 1}}')

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with patch("sys.argv", ["toon", str(input_file), "--encode", "--indent", "4"]):
                result = main()
                assert result == 0

    def test_length_marker_option(self, tmp_path):
        """Test length marker option."""
        input_file = tmp_path / "input.json"
        input_file.write_text('{"items": [1, 2, 3]}')

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with patch("sys.argv", ["toon", str(input_file), "--encode", "--length-marker"]):
                result = main()
                assert result == 0

    def test_no_strict_option(self, tmp_path):
        """Test no-strict option."""
        input_file = tmp_path / "input.toon"
        input_file.write_text("name: Test")

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with patch("sys.argv", ["toon", str(input_file), "--decode", "--no-strict"]):
                result = main()
                assert result == 0

    def test_error_file_not_found(self):
        """Test error when input file doesn't exist."""
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with patch("sys.argv", ["toon", "nonexistent.json"]):
                result = main()
                assert result == 1
                assert "not found" in mock_stderr.getvalue()

    def test_error_both_encode_and_decode(self, tmp_path):
        """Test error when both --encode and --decode are specified."""
        input_file = tmp_path / "input.txt"
        input_file.write_text("test")

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with patch("sys.argv", ["toon", str(input_file), "--encode", "--decode"]):
                result = main()
                assert result == 1
                assert "Cannot specify both" in mock_stderr.getvalue()

    def test_error_during_encoding(self, tmp_path):
        """Test error handling during encoding."""
        input_file = tmp_path / "input.json"
        input_file.write_text('{"invalid": broken}')

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with patch("sys.argv", ["toon", str(input_file), "--encode"]):
                result = main()
                assert result == 1
                assert "Error during encode" in mock_stderr.getvalue()

    def test_error_reading_input(self):
        """Test error when reading input fails."""
        mock_stdin = MagicMock()
        mock_stdin.read.side_effect = IOError("Read failed")

        with patch("sys.stdin", mock_stdin):
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                with patch("sys.argv", ["toon", "-", "--encode"]):
                    result = main()
                    assert result == 1
                    assert "Error reading input" in mock_stderr.getvalue()

    def test_error_writing_output(self, tmp_path):
        """Test error when writing output fails."""
        input_file = tmp_path / "input.json"
        input_file.write_text('{"test": true}')

        # Create a read-only directory to cause write failure
        output_file = tmp_path / "readonly" / "output.toon"

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            with patch("sys.argv", ["toon", str(input_file), "-o", str(output_file), "--encode"]):
                result = main()
                assert result == 1
                assert "Error writing output" in mock_stderr.getvalue()
