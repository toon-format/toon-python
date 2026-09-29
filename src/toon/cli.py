"""The ``toon`` command: convert between JSON and TOON.

Run ``toon --help`` (or ``python -m toon --help``) for usage.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from . import __toon_spec__, __version__
from ._api import dumps, loads
from ._errors import ToonDecodeError

__all__ = ["main"]

_DELIMITERS = {
    "comma": ",",
    ",": ",",
    "tab": "\t",
    "\\t": "\t",
    "\t": "\t",
    "pipe": "|",
    "|": "|",
}


def _delimiter(value: str) -> str:
    try:
        return _DELIMITERS[value]
    except KeyError:
        raise argparse.ArgumentTypeError("choose comma, tab, or pipe") from None


def _positive(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="toon",
        description=(
            "Convert JSON to TOON or TOON to JSON. The direction follows the input "
            "file extension (.json or .toon) and otherwise the content."
        ),
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="-",
        help="input file, or - for standard input (default)",
    )
    parser.add_argument("-o", "--output", help="output file (default: standard output)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "-e", "--encode", action="store_true", help="convert JSON to TOON"
    )
    mode.add_argument(
        "-d", "--decode", action="store_true", help="convert TOON to JSON"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="only validate the input; print nothing and exit with 1 if it is invalid",
    )
    parser.add_argument(
        "--delimiter",
        type=_delimiter,
        default=",",
        metavar="{comma,tab,pipe}",
        help="TOON delimiter when encoding (default: comma)",
    )
    parser.add_argument(
        "--indent-size",
        "--indent",
        type=_positive,
        default=2,
        metavar="N",
        help="spaces per TOON indentation level (default: 2)",
    )
    parser.add_argument(
        "--json-indent",
        type=int,
        default=2,
        metavar="N",
        help=(
            "spaces per JSON indentation level when decoding; "
            "0 for compact output (default: 2)"
        ),
    )
    parser.add_argument(
        "--no-strict",
        action="store_true",
        help="decode leniently instead of enforcing §14",
    )
    parser.add_argument(
        "--length-marker", action="store_true", help=argparse.SUPPRESS
    )  # removed from the specification; accepted for compatibility and ignored
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__} (TOON specification {__toon_spec__})",
    )
    return parser


def _read(source: str) -> tuple[str, str | None]:
    if source == "-":
        return sys.stdin.read(), None
    path = Path(source)
    return path.read_bytes().decode("utf-8"), path.suffix.lower()


def _is_json(text: str) -> bool:
    try:
        json.loads(text)
    except ValueError:
        return False
    return True


def _convert(
    args: argparse.Namespace, text: str, suffix: str | None
) -> tuple[str, bool]:
    """Return the converted text and whether it is TOON."""
    if args.encode:
        encode = True
    elif args.decode:
        encode = False
    elif suffix in (".json", ".toon"):
        encode = suffix == ".json"
    else:
        encode = _is_json(text)
    if encode:
        data: Any = json.loads(text)
        return dumps(data, indent_size=args.indent_size, delimiter=args.delimiter), True
    data = loads(text, strict=not args.no_strict, indent_size=args.indent_size)
    indent = args.json_indent if args.json_indent > 0 else None
    try:
        output = json.dumps(data, indent=indent, ensure_ascii=False, allow_nan=False)
    except ValueError:
        # Non-strict decoding turns out-of-range numbers into ±inf (§4, §14).
        raise ValueError("a number is out of the JSON range") from None
    return output, False


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line interface and return its exit status."""
    parser = _parser()
    args = parser.parse_args(argv)
    # TOON is always UTF-8 with LF line endings (§1.2), whatever the platform.
    for stream in (sys.stdin, sys.stdout):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8", newline="\n")
    if args.check and args.output:
        parser.error("--check cannot be combined with --output")
    if args.length_marker:
        print(
            "toon: --length-marker is no longer part of TOON and is ignored",
            file=sys.stderr,
        )
    try:
        text, suffix = _read(args.input)
    except OSError as exc:
        print(f"toon: cannot read {args.input}: {exc.strerror}", file=sys.stderr)
        return 1
    except UnicodeDecodeError:
        print(f"toon: {args.input} is not valid UTF-8", file=sys.stderr)
        return 1
    try:
        output, is_toon = _convert(args, text, suffix)
    except ToonDecodeError as exc:
        print(f"toon: invalid TOON: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"toon: invalid JSON: {exc}", file=sys.stderr)
        return 1
    except (TypeError, ValueError) as exc:
        print(f"toon: {exc}", file=sys.stderr)
        return 1
    if args.check:
        return 0
    try:
        if args.output:
            # TOON documents end without a newline (§12); JSON files end with one.
            Path(args.output).write_text(
                output if is_toon else output + "\n", encoding="utf-8", newline="\n"
            )
        else:
            sys.stdout.write(output + "\n")
    except OSError as exc:
        print(f"toon: cannot write {args.output}: {exc.strerror}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
