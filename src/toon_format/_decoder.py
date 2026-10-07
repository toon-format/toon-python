"""Decoder: TOON text to Python objects.

The document is first split into lines, with comment lines removed, blank
lines folded into a flag on the following line, and indentation converted to
depths (§5.1, §12). A recursive-descent parser then walks those lines,
dispatching on the line classes of §5.2.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any, TypeAlias

from ._errors import ToonDecodeError
from ._text import DELIMITERS, is_number_token

__all__ = ["decode"]

ObjectHook: TypeAlias = Callable[[dict[str, Any]], Any]
PairsHook: TypeAlias = Callable[[list[tuple[str, Any]]], Any]

# A parsed field list: each field is a leaf (``None``) or a nested field group.
Fields: TypeAlias = "tuple[tuple[str, Fields | None], ...]"

_BRACKET = re.compile(r"\[(0|[1-9][0-9]*)(:?)([\t|]?)\]")
_QUOTED = re.compile(r'"(?:[^"\\]|\\.)*"', re.DOTALL)
_HEX4 = re.compile(r"[0-9A-Fa-f]{4}")
_SIMPLE_ESCAPES = {"\\": "\\", '"': '"', "n": "\n", "r": "\r", "t": "\t"}


def decode(
    text: str,
    *,
    indent_size: int,
    strict: bool,
    parse_int: Callable[[str], Any] | None,
    parse_float: Callable[[str], Any] | None,
    object_hook: ObjectHook | None,
    object_pairs_hook: PairsHook | None,
) -> Any:
    """Decode a TOON document. Options are already validated."""
    lines = _split_lines(text, indent_size, strict)
    parser = _Parser(
        lines, strict, parse_int, parse_float, object_hook, object_pairs_hook
    )
    try:
        return parser.document()
    except RecursionError:
        raise ToonDecodeError("Document is nested too deeply to decode") from None


# --------------------------------------------------------------------------
# Lines (§5.1, §12)
# --------------------------------------------------------------------------


@dataclass(slots=True)
class _Line:
    number: int
    """1-based line number in the original document."""
    depth: int
    content: str
    """The line without indentation and trailing spaces."""
    source: str
    """The line as written, for error messages."""
    blank_before: int | None
    """Number of the first blank line directly above this one, if any."""


def _split_lines(text: str, indent_size: int, strict: bool) -> list[_Line]:
    if text.startswith("\ufeff"):
        text = text[1:]  # byte-order mark (§12)
    lines: list[_Line] = []
    blank: int | None = None
    for number, source in enumerate(text.split("\n"), 1):
        if source.endswith("\r"):
            source = source[:-1]  # CRLF input (§12)
        stripped = source.lstrip(" ")
        if stripped.startswith("#"):
            continue  # comment line (§5.1); lines are adjacent across it
        content = stripped.rstrip(" ")
        # Tabs make a line blank only where they may indent it (§12).
        if not content or (not strict and not content.strip(" \t")):
            blank = blank or number
            continue
        spaces = len(source) - len(stripped)
        if content[0] == "\t":
            if strict:
                raise ToonDecodeError(
                    "Tabs are not allowed in indentation", number, source
                )
            # Non-strict: a tab counts as one level, spaces as usual (§12).
            run = len(content) - len(content.lstrip(" \t"))
            spaces += content.count(" ", 0, run)
            depth = content.count("\t", 0, run) + spaces // indent_size
            content = content[run:]
        else:
            if strict and spaces % indent_size:
                raise ToonDecodeError(
                    f"Indentation of {spaces} spaces is not a multiple of "
                    f"{indent_size}",
                    number,
                    source,
                )
            depth = spaces // indent_size
        lines.append(_Line(number, depth, content, source, blank))
        blank = None
    return lines


# --------------------------------------------------------------------------
# Line classes (§5.2)
# --------------------------------------------------------------------------


@dataclass(slots=True)
class _Header:
    key: str | None
    length: int
    keyed: bool
    delimiter: str
    fields: Fields | None
    rest: str
    """Inline content after the colon, trimmed."""


@dataclass(slots=True)
class _KeyValue:
    key: str
    rest: str


@dataclass(slots=True)
class _Scalar:
    token: str


def _is_list_item(content: str) -> bool:
    return content == "-" or content.startswith("- ")


def _quoted_end(text: str, start: int) -> int:
    """Index just past the quoted token at ``start``, or -1 if it is unterminated."""
    match = _QUOTED.match(text, start)
    return match.end() if match else -1


def _find_unquoted(text: str, char: str, start: int = 0) -> int:
    """Index of the first ``char`` outside double quotes, or -1."""
    if '"' not in text:
        return text.find(char, start)
    in_quotes = False
    i, n = start, len(text)
    while i < n:
        c = text[i]
        if in_quotes:
            if c == "\\":
                i += 1
            elif c == '"':
                in_quotes = False
        elif c == '"':
            in_quotes = True
        elif c == char:
            return i
        i += 1
    return -1


def _split(text: str, delimiter: str) -> list[str]:
    """Split on unquoted delimiters and trim each token (§11.2, Appendix B.3)."""
    if '"' not in text:
        return [token.strip(" ") for token in text.split(delimiter)]
    tokens: list[str] = []
    in_quotes = False
    start = i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if in_quotes:
            if c == "\\":
                i += 1
            elif c == '"':
                in_quotes = False
        elif c == '"':
            in_quotes = True
        elif c == delimiter:
            tokens.append(text[start:i].strip(" "))
            start = i + 1
        i += 1
    tokens.append(text[start:].strip(" "))
    return tokens


def _leaf_count(fields: Fields) -> int:
    return sum(1 if nested is None else _leaf_count(nested) for _, nested in fields)


# --------------------------------------------------------------------------
# Parser
# --------------------------------------------------------------------------


class _Parser:
    def __init__(
        self,
        lines: list[_Line],
        strict: bool,
        parse_int: Callable[[str], Any] | None,
        parse_float: Callable[[str], Any] | None,
        object_hook: ObjectHook | None,
        object_pairs_hook: PairsHook | None,
    ) -> None:
        self.lines = lines
        self.pos = 0
        self.strict = strict
        self.parse_int = parse_int or int
        self.parse_float = parse_float
        self.object_hook = object_hook
        self.object_pairs_hook = object_pairs_hook
        # Number of enclosing header scopes that have consumed their first
        # item, row, or entry: a blank line inside any of them is a header span.
        self.spans = 0

    # -- infrastructure -----------------------------------------------------

    def error(self, msg: str, line: _Line) -> ToonDecodeError:
        return ToonDecodeError(msg, line.number, line.source)

    def peek(self) -> _Line | None:
        return self.lines[self.pos] if self.pos < len(self.lines) else None

    def take(self) -> _Line:
        line = self.lines[self.pos]
        if line.blank_before is not None and self.spans and self.strict:
            raise ToonDecodeError(
                "Blank line inside an array or keyed object", line.blank_before, ""
            )
        self.pos += 1
        return line

    def finish(self, obj: dict[str, Any]) -> Any:
        """Apply the object hooks to a fully decoded object."""
        if self.object_pairs_hook is not None:
            return self.object_pairs_hook(list(obj.items()))
        if self.object_hook is not None:
            return self.object_hook(obj)
        return obj

    def assign(self, obj: dict[str, Any], key: str, value: Any, line: _Line) -> None:
        if self.strict and key in obj:
            raise self.error(f"Duplicate key {key!r}", line)
        # Non-strict: last write wins (§14.3); like json.loads, the key keeps
        # the position of its first occurrence.
        obj[key] = value

    def scope_depth(self, expected: int) -> int:
        """Content depth of a scope; non-strict mode tolerates a deeper first line."""
        line = self.peek()
        if line is not None and not self.strict and line.depth > expected:
            return line.depth
        return expected

    # -- tokens (§4, §7) ----------------------------------------------------

    def unescape(self, body: str, line: _Line) -> str:
        if "\\" not in body:
            return body
        parts: list[str] = []
        i = 0
        while (j := body.find("\\", i)) >= 0:
            parts.append(body[i:j])
            c = body[j + 1] if j + 1 < len(body) else ""
            if c in _SIMPLE_ESCAPES:
                parts.append(_SIMPLE_ESCAPES[c])
                i = j + 2
            elif c == "u" and _HEX4.fullmatch(body, j + 2, j + 6):
                code = int(body[j + 2 : j + 6], 16)
                if 0xD800 <= code <= 0xDFFF:
                    raise self.error(f"Surrogate escape \\u{body[j + 2 : j + 6]}", line)
                parts.append(chr(code))
                i = j + 6
            else:
                raise self.error(f"Invalid escape sequence {body[j : j + 6]!r}", line)
        parts.append(body[i:])
        return "".join(parts)

    def quoted(self, token: str, line: _Line) -> str:
        """Decode a token that starts with a quote (§7.4 quoted-token boundary)."""
        end = _quoted_end(token, 0)
        if end < 0:
            raise self.error("Unterminated string", line)
        if end != len(token):
            raise self.error("Unexpected characters after closing quote", line)
        return self.unescape(token[1:-1], line)

    def key(self, token: str, line: _Line) -> str:
        token = token.strip(" ")
        return self.quoted(token, line) if token.startswith('"') else token

    def primitive(self, token: str, line: _Line) -> Any:
        if not token:
            return ""
        if token[0] == '"':
            return self.quoted(token, line)
        if token == "true":
            return True
        if token == "false":
            return False
        if token == "null":
            return None
        if is_number_token(token):
            return self.number(token, line)
        return token

    def number(self, token: str, line: _Line) -> Any:
        if "." not in token and "e" not in token and "E" not in token:
            try:
                return self.parse_int(token)
            except ValueError as exc:
                raise self.error(str(exc), line) from None
        if self.parse_float is not None:
            return self.parse_float(token)
        value = float(token)
        if math.isinf(value):
            raise self.error(f"Number {token} is out of range", line)
        return value or 0.0  # -0 decodes to 0 (§4)

    def values(self, text: str, delimiter: str, line: _Line) -> list[Any]:
        """Decode a delimited cell sequence; empty text is zero cells (§11.2)."""
        if not text:
            return []
        return [self.primitive(token, line) for token in _split(text, delimiter)]

    # -- headers (§6) -------------------------------------------------------

    def classify(self, content: str, line: _Line) -> _Header | _KeyValue | _Scalar:
        """Classify a line body as a header, a key-value line, or a scalar (§5.2)."""
        colon = _find_unquoted(content, ":")
        if content.startswith('"'):
            end = _quoted_end(content, 0)
            if end < 0:
                raise self.error("Unterminated string", line)
            if colon >= 0 and content.startswith("[", end):
                return self.header(content, end, line)
            after = content[end:].lstrip(" ")
            if not after:
                return _Scalar(content)
            if after[0] != ":":
                raise self.error("Unexpected characters after closing quote", line)
            return _KeyValue(self.quoted(content[:end], line), after[1:].strip(" "))
        bracket = _find_unquoted(content, "[")
        if 0 <= bracket < colon:
            return self.header(content, bracket, line)
        if colon >= 0:
            return _KeyValue(
                content[:colon].strip(" "), content[colon + 1 :].strip(" ")
            )
        return _Scalar(content)

    def header(self, content: str, bracket: int, line: _Line) -> _Header:
        """Parse a header whose bracket segment starts at ``bracket`` (§6)."""
        match = _BRACKET.match(content, bracket)
        if match is None:
            raise self.error("Malformed bracket segment", line)
        if content[bracket - 1 : bracket] in (" ", "\t"):  # SP and HTAB only (§1.2)
            raise self.error("Whitespace between a key and its bracket segment", line)
        delimiter = match.group(3) or ","
        pos = match.end()
        fields = None
        if content.startswith("{", pos):
            fields, pos = self.field_list(content, pos, delimiter, line)
        if not content.startswith(":", pos):
            raise self.error("Expected ':' after the array header", line)
        rest = content[pos + 1 :].strip(" ")
        keyed = bool(match.group(2))
        if keyed and fields is None:
            raise self.error("A keyed header requires a field list", line)
        if fields is not None and rest:
            raise self.error(
                "Unexpected content after a header with a field list", line
            )
        key_text = content[:bracket]
        key = self.key(key_text, line) if key_text else None
        return _Header(key, int(match.group(1)), keyed, delimiter, fields, rest)

    def field_list(
        self, text: str, pos: int, delimiter: str, line: _Line
    ) -> tuple[Fields, int]:
        """Parse the ``{...}`` at ``pos``; return the fields and the index past it."""
        fields: list[tuple[str, Fields | None]] = []
        seen: set[str] = set()
        n = len(text)
        pos += 1
        while True:
            while pos < n and text[pos] == " ":
                pos += 1
            if text.startswith('"', pos):
                end = _quoted_end(text, pos)
                if end < 0:
                    raise self.error("Unterminated field name", line)
                name = self.unescape(text[pos + 1 : end - 1], line)
                pos = end
            else:
                start = pos
                while pos < n and text[pos] not in "{},|\t":
                    if text[pos] == '"':
                        end = _quoted_end(text, pos)
                        pos = end if end >= 0 else n
                    else:
                        pos += 1
                name = text[start:pos].strip(" ")
                if not name:
                    raise self.error("Empty field name in field list", line)
            while pos < n and text[pos] == " ":
                pos += 1
            nested = None
            if text.startswith("{", pos):
                if text[pos - 1] == " ":
                    raise self.error(
                        "Whitespace between a field name and its nested field group",
                        line,
                    )
                nested, pos = self.field_list(text, pos, delimiter, line)
                while pos < n and text[pos] == " ":
                    pos += 1
            if name in seen and self.strict:
                raise self.error(f"Duplicate field name {name!r}", line)
            seen.add(name)
            fields.append((name, nested))
            if pos >= n:
                raise self.error("Unmatched '{' in field list", line)
            c = text[pos]
            pos += 1
            if c == "}":
                return tuple(fields), pos
            if c != delimiter:
                if c in DELIMITERS:
                    raise self.error(
                        "Field list delimiter does not match the bracket segment", line
                    )
                raise self.error("Malformed field list", line)

    # -- document (§5) ------------------------------------------------------

    def document(self) -> Any:
        first = self.peek()
        if first is None:
            return self.finish({})  # empty document (§5)
        if first.depth > 0:
            raise self.over_indented(first)  # an indented first line (§5, §8)
        if first.content == "[]":
            self.take()
            self.end_of_root()
            return []
        kind = self.classify(first.content, first)
        if isinstance(kind, _Header) and kind.key is None:
            self.take()
            value = self.header_value(kind, first, 1)
            self.end_of_root()
            return value
        if isinstance(kind, _Scalar) and len(self.lines) == 1:
            self.take()
            return self.primitive(first.content, first)
        return self.finish(self.object_body(0, {}, -1))

    def end_of_root(self) -> None:
        """A root array or keyed object spans the whole document (§5)."""
        line = self.peek()
        if line is not None:
            raise self.error("Unexpected content after the root value", line)

    # -- objects (§8) -------------------------------------------------------

    def object_body(
        self, depth: int, obj: dict[str, Any], parent: int
    ) -> dict[str, Any]:
        """Parse the fields at ``depth`` of an object opened at ``parent`` (§8)."""
        while (line := self.peek()) is not None and line.depth > parent:
            if line.depth != depth:
                raise self.over_indented(line)
            self.take()
            self.field(line, obj, depth)
        return obj

    def over_indented(self, line: _Line) -> ToonDecodeError:
        """A line deeper than its scope that no line opened (§8, §14.2)."""
        return self.error("Unexpected indentation", line)

    def field(self, line: _Line, obj: dict[str, Any], depth: int) -> None:
        kind = self.classify(line.content, line)
        if isinstance(kind, _Header):
            if kind.key is None:
                raise self.error(
                    "A header without a key is only valid at the root", line
                )
            self.assign(obj, kind.key, self.header_value(kind, line, depth + 1), line)
            return
        if isinstance(kind, _Scalar):
            raise self.error("Expected 'key: value'", line)
        self.assign(obj, kind.key, self.field_value(kind.rest, line, depth), line)

    def field_value(self, rest: str, line: _Line, depth: int) -> Any:
        """Decode what follows ``key:`` for a field standing at ``depth``."""
        if rest:
            return [] if rest == "[]" else self.primitive(rest, line)
        child = self.peek()
        if child is None or child.depth <= depth:
            return self.finish({})
        if self.strict and child.depth != depth + 1:
            raise self.error("Indentation jumps more than one level", child)
        return self.finish(self.object_body(child.depth, {}, depth))

    # -- arrays and keyed objects (§9, §10) ---------------------------------

    def header_value(self, header: _Header, line: _Line, depth: int) -> Any:
        """Decode the value a header opens; ``depth`` is its content depth."""
        if header.keyed:
            return self.entries(header, line, self.scope_depth(depth), depth - 1)
        if header.fields is not None:
            return self.rows(header, line, self.scope_depth(depth), depth - 1)
        if header.rest:
            values = self.values(header.rest, header.delimiter, line)
            self.check_count(len(values), header, line)
            return values
        return self.items(header, line, self.scope_depth(depth), depth - 1)

    def check_count(self, count: int, header: _Header, line: _Line) -> None:
        if self.strict and count != header.length:
            raise self.error(f"Declared length {header.length} but found {count}", line)

    def check_width(self, cells: list[Any], fields: Fields, line: _Line) -> None:
        width = _leaf_count(fields)
        if len(cells) != width:
            raise self.error(f"Expected {width} values but found {len(cells)}", line)

    def items(self, header: _Header, line: _Line, depth: int, parent: int) -> list[Any]:
        """Parse the list items of an array in list form (§9.2, §9.4)."""
        items: list[Any] = []
        started = False
        try:
            while (item := self.peek()) and item.depth > parent:
                if item.depth != depth:
                    raise self.over_indented(item)
                if not _is_list_item(item.content):
                    break
                self.take()
                if not started:
                    self.spans += 1
                    started = True
                items.append(self.item(item, depth))
        finally:
            self.spans -= started
        self.check_count(len(items), header, line)
        return items

    def item(self, line: _Line, depth: int) -> Any:
        """Decode one list item at ``depth`` (§9.4, §10)."""
        rest = line.content[2:].strip(" ")
        if not rest:
            return self.finish({})
        if rest == "[]":
            return []
        kind = self.classify(rest, line)
        if isinstance(kind, _Scalar):
            return self.primitive(rest, line)
        if isinstance(kind, _Header) and kind.key is None:
            if kind.fields is not None:
                raise self.error(
                    "A header with a field list cannot be a list item", line
                )
            return self.header_value(kind, line, depth + 1)
        # An object whose first field sits on the hyphen line at depth + 1.
        obj: dict[str, Any] = {}
        if isinstance(kind, _Header):
            assert kind.key is not None
            obj[kind.key] = self.header_value(kind, line, depth + 2)
        else:
            obj[kind.key] = self.field_value(kind.rest, line, depth + 1)
        return self.finish(self.object_body(depth + 1, obj, depth))

    def rows(self, header: _Header, line: _Line, depth: int, parent: int) -> list[Any]:
        """Parse the rows of a tabular array (§9.3)."""
        assert header.fields is not None
        delimiter = header.delimiter
        rows: list[Any] = []
        started = False
        try:
            while (row := self.peek()) and row.depth > parent:
                if row.depth != depth:
                    raise self.over_indented(row)
                colon = _find_unquoted(row.content, ":")
                if colon >= 0:
                    split = _find_unquoted(row.content, delimiter)
                    if split < 0 or colon < split:
                        break  # a key-value line ends the rows
                self.take()
                if not started:
                    self.spans += 1
                    started = True
                cells = self.values(row.content, delimiter, row)
                self.check_width(cells, header.fields, row)
                rows.append(self.materialize(header.fields, iter(cells)))
        finally:
            self.spans -= started
        self.check_count(len(rows), header, line)
        return rows

    def entries(self, header: _Header, line: _Line, depth: int, parent: int) -> Any:
        """Parse the entry rows of a keyed tabular object (§9.5)."""
        assert header.fields is not None
        obj: dict[str, Any] = {}
        count = 0
        try:
            while (entry := self.peek()) and entry.depth > parent:
                if entry.depth != depth:
                    raise self.over_indented(entry)
                self.take()
                if not count:
                    self.spans += 1
                count += 1
                colon = _find_unquoted(entry.content, ":")
                if colon < 0:
                    raise self.error("Expected 'key: values' entry row", entry)
                key = self.key(entry.content[:colon], entry)
                cells = self.values(
                    entry.content[colon + 1 :].strip(" "), header.delimiter, entry
                )
                self.check_width(cells, header.fields, entry)
                self.assign(
                    obj, key, self.materialize(header.fields, iter(cells)), entry
                )
        finally:
            self.spans -= bool(count)
        self.check_count(count, header, line)
        return self.finish(obj)

    def materialize(self, fields: Fields, cells: Iterator[Any]) -> Any:
        """Build one object from row cells, walking the field list depth-first."""
        obj: dict[str, Any] = {}
        for name, nested in fields:
            obj[name] = (
                next(cells) if nested is None else self.materialize(nested, cells)
            )
        return self.finish(obj)
