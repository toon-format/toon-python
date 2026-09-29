"""The ``toon`` command."""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

from toon import __version__
from toon.cli import main

USERS_JSON = '{"users": [{"id": 1, "name": "Ada"}, {"id": 2, "name": "Bob"}]}'
USERS_TOON = "users[2]{id,name}:\n  1,Ada\n  2,Bob"


def run(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    *args: str,
    stdin: str = "",
) -> tuple[int, str, str]:
    monkeypatch.setattr(sys, "stdin", io.StringIO(stdin))
    code = main(list(args))
    out, err = capsys.readouterr()
    return code, out, err


@pytest.mark.parametrize(
    ("args", "stdin", "expected"),
    [
        (["encode"], USERS_JSON, USERS_TOON + "\n"),
        (
            ["encode", "--delimiter", "tab", "--indent", "4"],
            '{"a": {"b": [1, 2]}}',
            "a:\n    b[2\t]: 1\t2\n",
        ),
        (["decode", "--compact"], USERS_TOON, USERS_JSON + "\n"),
        (["decode"], "a: 1", '{\n  "a": 1\n}\n'),
        (["decode", "--compact", "--no-strict"], "a[3]: 1", '{"a": [1]}\n'),
        (["decode", "--compact", "--indent", "4"], "a:\n    b: 1", '{"a": {"b": 1}}\n'),
    ],
)
def test_commands(
    args: list[str],
    stdin: str,
    expected: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert run(monkeypatch, capsys, *args, stdin=stdin) == (0, expected, "")


def test_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "users.json"
    source.write_text(USERS_JSON, encoding="utf-8")
    target = tmp_path / "users.toon"
    assert run(monkeypatch, capsys, "encode", str(source), "-o", str(target)) == (
        0,
        "",
        "",
    )
    assert target.read_text(encoding="utf-8") == USERS_TOON  # no trailing newline (§12)

    back = tmp_path / "back.json"
    code = run(monkeypatch, capsys, "decode", str(target), "-o", str(back), "--compact")
    assert code == (0, "", "")
    assert back.read_text(encoding="utf-8") == USERS_JSON + "\n"


@pytest.mark.parametrize(
    ("args", "stdin", "expected"),
    [
        ([], USERS_JSON, USERS_TOON + "\n"),
        (["-"], USERS_TOON, json.dumps(json.loads(USERS_JSON), indent=2) + "\n"),
        (["-e", "--delimiter", "|"], "[1, 2]", "[2|]: 1|2\n"),
        (
            ["-d", "--indent", "4"],
            "a:\n    b: 1",
            '{\n    "a": {\n        "b": 1\n    }\n}\n',
        ),
        (["-d", "--no-strict", "--indent-size", "1"], "a: 1", '{\n "a": 1\n}\n'),
    ],
)
def test_convert_without_command(
    args: list[str],
    stdin: str,
    expected: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``toon FILE [options]`` keeps the interface of 0.9."""
    assert run(monkeypatch, capsys, *args, stdin=stdin) == (0, expected, "")


def test_convert_detects_direction_from_extension(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "users.json"
    source.write_text(USERS_JSON, encoding="utf-8")
    target = tmp_path / "users.toon"
    assert run(monkeypatch, capsys, str(source), "-o", str(target)) == (0, "", "")
    assert target.read_text(encoding="utf-8") == USERS_TOON

    back = tmp_path / "back.json"
    assert run(monkeypatch, capsys, str(target), "-o", str(back)) == (0, "", "")
    assert back.read_text(encoding="utf-8") == (
        json.dumps(json.loads(USERS_JSON), indent=2) + "\n"
    )


def test_out_of_range_number_is_not_written_as_json(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    result = run(monkeypatch, capsys, "decode", "--no-strict", stdin="n: 1e400")
    assert result == (1, "", "toon: a number is out of the JSON range\n")


def test_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    valid = tmp_path / "valid.toon"
    valid.write_text(USERS_TOON, encoding="utf-8")
    invalid = tmp_path / "invalid.toon"
    invalid.write_text("a: 1\nitems[3]: a,b", encoding="utf-8")
    assert run(monkeypatch, capsys, "check", str(valid)) == (0, "", "")
    code, out, err = run(
        monkeypatch, capsys, "check", str(invalid), "missing.toon", str(valid)
    )
    assert (code, out) == (1, "")
    assert err == (
        f"{invalid}:2: Declared length 3 but found 2\n"
        "toon: cannot read missing.toon: No such file or directory\n"
    )


def test_check_stdin(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run(monkeypatch, capsys, "check", stdin=USERS_TOON) == (0, "", "")
    result = run(monkeypatch, capsys, "check", stdin="a[3]: 1")
    assert result == (1, "", "<stdin>:1: Declared length 3 but found 1\n")
    assert run(monkeypatch, capsys, "check", "--no-strict", stdin="a[3]: 1") == (
        0,
        "",
        "",
    )


class _WordEncoding:
    def encode(self, text: str) -> list[str]:
        return text.split()


STATS = (
    "Tokens with tiktoken o200k_base (exact for OpenAI models only)\n"
    "Format              Tokens  Characters  vs compact JSON\n"
    "JSON (compact)           2          21\n"
    "JSON (indent 2)         10          43          +400.0%\n"
    "TOON (comma)             5          16          +150.0%\n"
    "TOON (tab)               7          17          +250.0%\n"
    "TOON (pipe)              5          17          +150.0%\n"
)


@pytest.mark.parametrize("stdin", ['{"a": [1, 2], "b": "x y"}', "a[2]: 1,2\nb: x y"])
def test_stats(
    stdin: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from toon import _tokens

    monkeypatch.setattr(_tokens, "_encoding", lambda name: _WordEncoding())
    assert run(monkeypatch, capsys, "stats", stdin=stdin) == (0, STATS, "")


def test_stats_needs_tiktoken(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from toon import _tokens

    _tokens._encoding.cache_clear()
    monkeypatch.setitem(sys.modules, "tiktoken", None)
    assert run(monkeypatch, capsys, "stats", stdin='{"a": 1}') == (
        1,
        "",
        "toon: tiktoken is required for token counting: "
        'pip install "toon-python[tokens]"\n',
    )


@pytest.mark.parametrize(
    ("args", "stdin", "message"),
    [
        (["encode"], "{oops", "toon: invalid JSON"),
        (["encode"], '{"s": "\\ud800"}', "unpaired surrogate"),
        (["decode"], "a[3]: 1", "toon: invalid TOON: line 1:"),
        (["stats"], "a[3]: 1", "toon: invalid TOON: line 1:"),
        (["decode", "missing.toon"], "", "toon: cannot read missing.toon"),
        (["missing.toon"], "", "toon: cannot read missing.toon"),
    ],
)
def test_errors(
    args: list[str],
    stdin: str,
    message: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = run(monkeypatch, capsys, *args, stdin=stdin)
    assert (code, out) == (1, "")
    assert message in err


@pytest.mark.parametrize(
    "args",
    [
        ["-e", "-d"],
        ["--delimiter", ";"],
        ["--indent-size", "0"],
        ["encode", "--indent", "0"],
        ["decode", "--delimiter", "tab"],
        ["stats", "--check"],
        ["--check"],
        ["--stats"],
    ],
)
def test_usage_errors(
    args: list[str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as info:
        run(monkeypatch, capsys, *args)
    assert info.value.code == 2


class _Terminal(io.StringIO):
    def isatty(self) -> bool:
        return True


def test_no_arguments_in_a_terminal_prints_help(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdin", _Terminal())
    assert main([]) == 2
    out, err = capsys.readouterr()
    assert out == ""
    assert err.startswith("usage: toon [-h] [-V] COMMAND ...")


def test_length_marker_is_ignored(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run(monkeypatch, capsys, "--length-marker", stdin="[1, 2]") == (
        0,
        "[2]: 1,2\n",
        "toon: --length-marker is no longer part of TOON and is ignored\n",
    )


def test_version(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit):
        run(monkeypatch, capsys, "--version")
    assert capsys.readouterr().out == f"toon {__version__} (TOON specification 4.1)\n"


def test_files_are_utf8_with_lf(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "in.json"
    source.write_bytes('{"a": ["é", "ü"]}'.encode())
    target = tmp_path / "out.toon"
    assert run(monkeypatch, capsys, str(source), "-o", str(target)) == (0, "", "")
    assert target.read_bytes() == "a[2]: é,ü".encode()
    source.write_bytes(b"\xff")
    code, _, err = run(monkeypatch, capsys, str(source))
    assert (code, err) == (1, f"toon: {source} is not valid UTF-8\n")


def test_unwritable_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "missing" / "out.toon"
    code, _, err = run(monkeypatch, capsys, "-o", str(target), stdin="[1]")
    assert code == 1
    assert err.startswith(f"toon: cannot write {target}")


def test_python_m() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "toon", "encode"],
        input="[1, 2]",
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout == "[2]: 1,2\n"
