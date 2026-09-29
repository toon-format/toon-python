"""The ``toon`` command: convert between JSON and TOON, validate, count tokens.

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
from ._tokens import stats

__all__ = ["main"]

_COMMANDS = ("encode", "decode", "check", "stats")
_GLOBAL_OPTIONS = ("-h", "--help", "-V", "--version")

_DELIMITERS = {
    "comma": ",",
    ",": ",",
    "tab": "\t",
    "\\t": "\t",
    "\t": "\t",
    "pipe": "|",
    "|": "|",
}


class _Failure(Exception):
    """An error reported as ``toon: <message>`` with exit status 1."""


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


def _add_input(parser: argparse.ArgumentParser, kind: str) -> None:
    parser.add_argument(
        "input",
        nargs="?",
        default="-",
        metavar="FILE",
        help=f"{kind} file, or - for standard input (default)",
    )


def _add_output(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-o", "--output", help="output file (default: standard output)")


def _add_delimiter(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--delimiter",
        type=_delimiter,
        default=",",
        metavar="{comma,tab,pipe}",
        help="TOON delimiter (default: comma)",
    )


def _add_indent(parser: argparse.ArgumentParser, *names: str) -> None:
    parser.add_argument(
        *names,
        dest="indent",
        type=_positive,
        default=2,
        metavar="N",
        help="spaces per TOON indentation level (default: 2)",
    )


def _add_no_strict(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--no-strict",
        action="store_true",
        help="decode leniently instead of enforcing §14",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="toon",
        description="Convert between JSON and TOON, validate TOON, count tokens.",
        epilog=(
            "Without a command, 'toon FILE' converts in the direction given by "
            "the file extension (.json or .toon) and otherwise by the content."
        ),
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__} (TOON specification {__toon_spec__})",
    )
    commands = parser.add_subparsers(title="commands", metavar="COMMAND")

    encode = commands.add_parser("encode", help="convert JSON to TOON")
    _add_input(encode, "JSON")
    _add_output(encode)
    _add_delimiter(encode)
    _add_indent(encode, "--indent")
    encode.set_defaults(run=_encode)

    decode = commands.add_parser("decode", help="convert TOON to JSON")
    _add_input(decode, "TOON")
    _add_output(decode)
    decode.add_argument(
        "--compact", action="store_true", help="write JSON on a single line"
    )
    _add_indent(decode, "--indent")
    _add_no_strict(decode)
    decode.set_defaults(run=_decode)

    check = commands.add_parser(
        "check", help="validate TOON files; exit with 1 if any is invalid"
    )
    check.add_argument(
        "files",
        nargs="*",
        default=["-"],
        metavar="FILE",
        help="TOON files, or - for standard input (default)",
    )
    _add_indent(check, "--indent")
    _add_no_strict(check)
    check.set_defaults(run=_check)

    count = commands.add_parser(
        "stats",
        help="compare token counts of JSON and TOON (needs the tokens extra)",
        description=(
            "Count the tokens of the data as JSON and as TOON with each delimiter. "
            "Counts use tiktoken's o200k_base encoding and are exact for OpenAI "
            "models only."
        ),
    )
    _add_input(count, "JSON or TOON")
    count.set_defaults(run=_stats)
    return parser


def _legacy_parser() -> argparse.ArgumentParser:
    """Parse ``toon FILE [options]``, the interface of 0.9, kept as is."""
    parser = argparse.ArgumentParser(
        prog="toon",
        usage="toon [FILE] [-e | -d] [options]\n       toon COMMAND ...",
        description=(
            "Convert JSON to TOON or TOON to JSON. The direction follows the input "
            "file extension (.json or .toon) and otherwise the content. Run "
            "'toon --help' for the commands."
        ),
    )
    _add_input(parser, "input")
    _add_output(parser)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "-e", "--encode", action="store_true", help="convert JSON to TOON"
    )
    mode.add_argument(
        "-d", "--decode", action="store_true", help="convert TOON to JSON"
    )
    _add_delimiter(parser)
    _add_indent(parser, "--indent-size", "--indent")
    _add_no_strict(parser)
    parser.add_argument(
        "--length-marker", action="store_true", help=argparse.SUPPRESS
    )  # removed from the specification; accepted for compatibility and ignored
    parser.set_defaults(run=_convert)
    return parser


def _read(source: str) -> tuple[str, str | None]:
    """Return the text of ``source`` and its lowercase file extension."""
    if source == "-":
        return sys.stdin.read(), None
    path = Path(source)
    try:
        return path.read_bytes().decode("utf-8"), path.suffix.lower()
    except OSError as exc:
        raise _Failure(f"cannot read {source}: {exc.strerror}") from None
    except UnicodeDecodeError:
        raise _Failure(f"{source} is not valid UTF-8") from None


def _write(target: str | None, text: str, *, is_toon: bool) -> None:
    if target is None:
        sys.stdout.write(text + "\n")
        return
    try:
        # TOON documents end without a newline (§12); JSON files end with one.
        Path(target).write_text(
            text if is_toon else text + "\n", encoding="utf-8", newline="\n"
        )
    except OSError as exc:
        raise _Failure(f"cannot write {target}: {exc.strerror}") from None


def _is_json(text: str, suffix: str | None) -> bool:
    if suffix in (".json", ".toon"):
        return suffix == ".json"
    try:
        json.loads(text)
    except ValueError:
        return False
    return True


def _from_json(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise _Failure(f"invalid JSON: {exc}") from None


def _from_toon(text: str, args: argparse.Namespace | None = None) -> Any:
    strict, indent = (True, 2) if args is None else (not args.no_strict, args.indent)
    try:
        return loads(text, strict=strict, indent_size=indent)
    except ToonDecodeError as exc:
        raise _Failure(f"invalid TOON: {exc}") from None


def _to_toon(data: Any, args: argparse.Namespace) -> str:
    try:
        return dumps(data, indent_size=args.indent, delimiter=args.delimiter)
    except ValueError as exc:
        raise _Failure(str(exc)) from None


def _to_json(data: Any, indent: int | None) -> str:
    try:
        return json.dumps(data, indent=indent, ensure_ascii=False, allow_nan=False)
    except ValueError:
        # Non-strict decoding turns out-of-range numbers into ±inf (§4, §14).
        raise _Failure("a number is out of the JSON range") from None


def _encode(args: argparse.Namespace) -> int:
    text, _ = _read(args.input)
    _write(args.output, _to_toon(_from_json(text), args), is_toon=True)
    return 0


def _decode(args: argparse.Namespace) -> int:
    text, _ = _read(args.input)
    data = _from_toon(text, args)
    _write(args.output, _to_json(data, None if args.compact else 2), is_toon=False)
    return 0


def _check(args: argparse.Namespace) -> int:
    status = 0
    for source in args.files:
        try:
            text, _ = _read(source)
            loads(text, strict=not args.no_strict, indent_size=args.indent)
        except _Failure as exc:
            print(f"toon: {exc}", file=sys.stderr)
            status = 1
        except ToonDecodeError as exc:
            # file:line: message, the format editors and CI annotations link.
            name = "<stdin>" if source == "-" else source
            where = name if exc.line is None else f"{name}:{exc.line}"
            print(f"{where}: {exc.msg}", file=sys.stderr)
            status = 1
    return status


def _stats(args: argparse.Namespace) -> int:
    text, suffix = _read(args.input)
    data = _from_json(text) if _is_json(text, suffix) else _from_toon(text)
    try:
        table = stats(data)
    except (RuntimeError, ValueError) as exc:
        raise _Failure(str(exc)) from None
    sys.stdout.write(table + "\n")
    return 0


def _convert(args: argparse.Namespace) -> int:
    if args.length_marker:
        print(
            "toon: --length-marker is no longer part of TOON and is ignored",
            file=sys.stderr,
        )
    text, suffix = _read(args.input)
    encode = args.encode or (not args.decode and _is_json(text, suffix))
    if encode:
        _write(args.output, _to_toon(_from_json(text), args), is_toon=True)
    else:
        # As in 0.9, --indent sets both the TOON and the JSON indentation.
        data = _from_toon(text, args)
        _write(args.output, _to_json(data, args.indent), is_toon=False)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line interface and return its exit status."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    # TOON is always UTF-8 with LF line endings (§1.2), whatever the platform.
    for stream in (sys.stdin, sys.stdout):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8", newline="\n")
    if not arguments and sys.stdin.isatty():
        _parser().print_help(sys.stderr)
        return 2
    if arguments and arguments[0] in _COMMANDS + _GLOBAL_OPTIONS:
        args = _parser().parse_args(arguments)
    else:
        args = _legacy_parser().parse_args(arguments)
    try:
        status: int = args.run(args)
    except _Failure as exc:
        print(f"toon: {exc}", file=sys.stderr)
        return 1
    return status


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
