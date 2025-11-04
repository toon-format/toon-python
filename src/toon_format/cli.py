# Copyright (c) 2025 TOON Format Organization
# SPDX-License-Identifier: MIT
"""Command-line interface for TOON encoding/decoding.

Provides the `toon` command-line tool for converting between JSON and TOON formats.
Supports auto-detection based on file extensions and content, with options for
delimiters, indentation, and validation modes.
"""

import argparse
import json
import sys
from pathlib import Path

from . import decode, encode
from .types import DecodeOptions, EncodeOptions


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="toon",
        description="Convert between JSON and TOON formats",
    )

    parser.add_argument(
        "input",
        type=str,
        help="Input file path (or - for stdin)",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file path (prints to stdout if omitted)",
    )

    parser.add_argument(
        "-e",
        "--encode",
        action="store_true",
        help="Force encode mode (overrides auto-detection)",
    )

    parser.add_argument(
        "-d",
        "--decode",
        action="store_true",
        help="Force decode mode (overrides auto-detection)",
    )

    parser.add_argument(
        "--delimiter",
        type=str,
        choices=[",", "\t", "|"],
        default=",",
        help='Array delimiter: , (comma), \\t (tab), | (pipe) (default: ",")',
    )

    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Indentation size (default: 2)",
    )

    parser.add_argument(
        "--length-marker",
        action="store_true",
        help="Add # prefix to array lengths (e.g., items[#3])",
    )

    parser.add_argument(
        "--no-strict",
        action="store_true",
        help="Disable strict validation when decoding",
    )

    args = parser.parse_args()

    # Read input
    try:
        if args.input == "-":
            input_text = sys.stdin.read()
            input_path = None
        else:
            input_path = Path(args.input)
            if not input_path.exists():
                print(f"Error: Input file not found: {args.input}", file=sys.stderr)
                return 1
            input_text = input_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        return 1

    # Determine operation mode
    if args.encode and args.decode:
        print("Error: Cannot specify both --encode and --decode", file=sys.stderr)
        return 1

    if args.encode:
        mode = "encode"
    elif args.decode:
        mode = "decode"
    else:
        # Auto-detect based on file extension
        if input_path:
            if input_path.suffix.lower() == ".json":
                mode = "encode"
            elif input_path.suffix.lower() == ".toon":
                mode = "decode"
            else:
                # Try to detect by content
                try:
                    json.loads(input_text)
                    mode = "encode"
                except json.JSONDecodeError:
                    mode = "decode"
        else:
            # No file path, try to detect by content
            try:
                json.loads(input_text)
                mode = "encode"
            except json.JSONDecodeError:
                mode = "decode"

    # Process
    try:
        if mode == "encode":
            output_text = encode_json_to_toon(
                input_text,
                delimiter=args.delimiter,
                indent=args.indent,
                length_marker=args.length_marker,
            )
        else:
            output_text = decode_toon_to_json(
                input_text,
                indent=args.indent,
                strict=not args.no_strict,
            )
    except Exception as e:
        print(f"Error during {mode}: {e}", file=sys.stderr)
        return 1

    # Write output
    try:
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(output_text, encoding="utf-8")
        else:
            print(output_text)
    except Exception as e:
        print(f"Error writing output: {e}", file=sys.stderr)
        return 1

    return 0


def encode_json_to_toon(
    json_text: str,
    delimiter: str = ",",
    indent: int = 2,
    length_marker: bool = False,
) -> str:
    """Encode JSON text to TOON format.

    Args:
        json_text: JSON input string
        delimiter: Delimiter character
        indent: Indentation size
        length_marker: Whether to add # prefix

    Returns:
        TOON-formatted string

    Raises:
        json.JSONDecodeError: If JSON is invalid
    """
    data = json.loads(json_text)

    options: EncodeOptions = {
        "indent": indent,
        "delimiter": delimiter,
        "lengthMarker": "#" if length_marker else False,
    }

    return encode(data, options)


def decode_toon_to_json(
    toon_text: str,
    indent: int = 2,
    strict: bool = True,
) -> str:
    """Decode TOON text to JSON format.

    Args:
        toon_text: TOON input string
        indent: Indentation size
        strict: Whether to use strict validation

    Returns:
        JSON-formatted string

    Raises:
        ToonDecodeError: If TOON is invalid
    """
    options = DecodeOptions(indent=indent, strict=strict)
    data = decode(toon_text, options)

    return json.dumps(data, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    sys.exit(main())
