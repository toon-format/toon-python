"""
Tests for TOON spec fixtures.

This test module loads and runs all official TOON specification test fixtures
from https://github.com/toon-format/spec/tree/main/tests/fixtures
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from toon_format import ToonDecodeError, decode, encode
from toon_format.types import DecodeOptions, EncodeOptions


FIXTURES_DIR = Path(__file__).parent / "fixtures"
DECODE_DIR = FIXTURES_DIR / "decode"
ENCODE_DIR = FIXTURES_DIR / "encode"


def load_fixture_file(filepath: Path) -> Dict[str, Any]:
    """Load a fixture JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def get_all_decode_fixtures() -> List[tuple]:
    """
    Get all decode test cases from fixture files.

    Returns:
        List of tuples (fixture_name, test_case_name, test_data)
    """
    test_cases = []

    for fixture_file in sorted(DECODE_DIR.glob("*.json")):
        fixture_data = load_fixture_file(fixture_file)
        fixture_name = fixture_file.stem

        for test in fixture_data.get("tests", []):
            test_id = f"{fixture_name}::{test['name']}"
            test_cases.append((test_id, test, fixture_name))

    return test_cases


def get_all_encode_fixtures() -> List[tuple]:
    """
    Get all encode test cases from fixture files.

    Returns:
        List of tuples (fixture_name, test_case_name, test_data)
    """
    test_cases = []

    for fixture_file in sorted(ENCODE_DIR.glob("*.json")):
        fixture_data = load_fixture_file(fixture_file)
        fixture_name = fixture_file.stem

        for test in fixture_data.get("tests", []):
            test_id = f"{fixture_name}::{test['name']}"
            test_cases.append((test_id, test, fixture_name))

    return test_cases


class TestDecodeFixtures:
    """Test all decode fixtures from the TOON specification."""

    @pytest.mark.parametrize("test_id,test_data,fixture_name", get_all_decode_fixtures())
    def test_decode(self, test_id: str, test_data: Dict[str, Any], fixture_name: str):
        """Test decoding TOON input to expected output."""
        input_str = test_data["input"]
        expected = test_data.get("expected")
        should_error = test_data.get("shouldError", False)
        options_dict = test_data.get("options", {})

        # Build decode options
        options = DecodeOptions(
            strict=options_dict.get("strict", True), indent=options_dict.get("indent", 2)
        )

        if should_error:
            # Test should raise an error
            with pytest.raises((ToonDecodeError, ValueError, Exception)):
                decode(input_str, options=options)
        else:
            # Test should succeed
            result = decode(input_str, options=options)
            assert result == expected, (
                f"Decode mismatch in {test_id}\n"
                f"Input: {input_str!r}\n"
                f"Expected: {expected!r}\n"
                f"Got: {result!r}"
            )


class TestEncodeFixtures:
    """Test all encode fixtures from the TOON specification."""

    @pytest.mark.parametrize("test_id,test_data,fixture_name", get_all_encode_fixtures())
    def test_encode(self, test_id: str, test_data: Dict[str, Any], fixture_name: str):
        """Test encoding input data to expected TOON string."""
        input_data = test_data["input"]
        expected = test_data["expected"]
        options_dict = test_data.get("options", {})

        # Build encode options
        options = EncodeOptions(
            indent=options_dict.get("indent", 2),
            delimiter=options_dict.get("delimiter", ","),
            lengthMarker=options_dict.get("lengthMarker", ""),
        )

        # Encode and compare
        result = encode(input_data, options=options)
        assert result == expected, (
            f"Encode mismatch in {test_id}\n"
            f"Input: {input_data!r}\n"
            f"Expected: {expected!r}\n"
            f"Got: {result!r}"
        )


class TestRoundTrip:
    """Test that encode -> decode produces the original value."""

    @pytest.mark.parametrize("test_id,test_data,fixture_name", get_all_encode_fixtures())
    def test_roundtrip(self, test_id: str, test_data: Dict[str, Any], fixture_name: str):
        """Test that encoding then decoding returns the original input."""
        # Skip normalization tests since they intentionally change data types
        if fixture_name == "normalization":
            pytest.skip("Normalization tests don't roundtrip by design")

        input_data = test_data["input"]
        options_dict = test_data.get("options", {})

        # Build options
        encode_opts = EncodeOptions(
            indent=options_dict.get("indent", 2),
            delimiter=options_dict.get("delimiter", ","),
            lengthMarker=options_dict.get("lengthMarker", ""),
        )
        decode_opts = DecodeOptions(strict=True, indent=options_dict.get("indent", 2))

        # Encode then decode
        encoded = encode(input_data, options=encode_opts)
        decoded = decode(encoded, options=decode_opts)

        assert decoded == input_data, (
            f"Roundtrip mismatch in {test_id}\n"
            f"Original: {input_data!r}\n"
            f"Encoded: {encoded!r}\n"
            f"Decoded: {decoded!r}"
        )


# Statistics functions for reporting
def count_tests_in_fixture(fixture_path: Path) -> int:
    """Count the number of test cases in a fixture file."""
    fixture_data = load_fixture_file(fixture_path)
    return len(fixture_data.get("tests", []))


def get_fixture_stats() -> Dict[str, Any]:
    """Get statistics about the loaded fixtures."""
    decode_files = sorted(DECODE_DIR.glob("*.json"))
    encode_files = sorted(ENCODE_DIR.glob("*.json"))

    decode_stats = {
        "files": len(decode_files),
        "tests": sum(count_tests_in_fixture(f) for f in decode_files),
        "by_file": {f.stem: count_tests_in_fixture(f) for f in decode_files},
    }

    encode_stats = {
        "files": len(encode_files),
        "tests": sum(count_tests_in_fixture(f) for f in encode_files),
        "by_file": {f.stem: count_tests_in_fixture(f) for f in encode_files},
    }

    return {
        "decode": decode_stats,
        "encode": encode_stats,
        "total_files": decode_stats["files"] + encode_stats["files"],
        "total_tests": decode_stats["tests"] + encode_stats["tests"],
    }


if __name__ == "__main__":
    # Print fixture statistics when run directly
    stats = get_fixture_stats()
    print("TOON Spec Fixture Statistics")
    print("=" * 50)
    print(f"\nDecode Fixtures: {stats['decode']['files']} files, {stats['decode']['tests']} tests")
    for name, count in stats["decode"]["by_file"].items():
        print(f"  - {name}: {count} tests")

    print(f"\nEncode Fixtures: {stats['encode']['files']} files, {stats['encode']['tests']} tests")
    for name, count in stats["encode"]["by_file"].items():
        print(f"  - {name}: {count} tests")

    print(f"\nTotal: {stats['total_files']} fixture files, {stats['total_tests']} test cases")
