"""The ``toon`` command."""

from __future__ import annotations

import io
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


def test_encode_from_stdin(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run(monkeypatch, capsys, stdin=USERS_JSON) == (0, USERS_TOON + "\n", "")


def test_decode_from_stdin(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out, _ = run(monkeypatch, capsys, "--json-indent", "0", stdin=USERS_TOON)
    assert (code, out) == (0, USERS_JSON + "\n")


def test_detects_direction_from_extension(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "users.json"
    source.write_text(USERS_JSON, encoding="utf-8")
    target = tmp_path / "users.toon"
    assert run(monkeypatch, capsys, str(source), "-o", str(target)) == (0, "", "")
    assert target.read_text(encoding="utf-8") == USERS_TOON  # no trailing newline (§12)

    back = tmp_path / "back.json"
    assert run(monkeypatch, capsys, str(target), "-o", str(back)) == (0, "", "")
    assert back.read_text(encoding="utf-8").startswith('{\n  "users": [')


def test_options(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out, _ = run(
        monkeypatch,
        capsys,
        "-e",
        "--delimiter",
        "tab",
        "--indent-size",
        "4",
        stdin='{"a": {"b": [1, 2]}}',
    )
    assert (code, out) == (0, "a:\n    b[2\t]: 1\t2\n")
    code, out, _ = run(
        monkeypatch, capsys, "-d", "--no-strict", "--json-indent", "0", stdin="a[3]: 1"
    )
    assert (code, out) == (0, '{"a": [1]}\n')


def test_out_of_range_number_is_not_written_as_json(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    result = run(monkeypatch, capsys, "-d", "--no-strict", stdin="n: 1e400")
    assert result == (1, "", "toon: a number is out of the JSON range\n")


class _WordEncoding:
    def encode(self, text: str) -> list[str]:
        return text.split()


def test_stats(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from toon import _tokens

    monkeypatch.setattr(_tokens, "_encoding", lambda name: _WordEncoding())
    code, out, err = run(
        monkeypatch, capsys, "-e", "--stats", stdin='{"a": [1, 2], "b": "x y"}'
    )
    assert (code, out) == (0, "a[2]: 1,2\nb: x y\n")
    assert err == (
        "Tokens with tiktoken o200k_base (exact for OpenAI models only)\n"
        "Format              Tokens  Characters  TOON vs\n"
        "JSON (compact)           2          21  +150.0%\n"
        "JSON (indent 2)         10          43   -50.0%\n"
        "TOON                     5          16\n"
    )


def test_stats_needs_tiktoken(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from toon import _tokens

    _tokens._encoding.cache_clear()
    monkeypatch.setitem(sys.modules, "tiktoken", None)
    code, out, err = run(monkeypatch, capsys, "-e", "--stats", stdin='{"a": 1}')
    assert (code, out) == (1, "")
    assert err == (
        'toon: tiktoken is required for token counting: pip install "toon-format[tokens]"\n'
    )


def test_check(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run(monkeypatch, capsys, "--check", stdin=USERS_TOON) == (0, "", "")
    code, out, err = run(monkeypatch, capsys, "--check", "-d", stdin="items[3]: a,b")
    assert (code, out) == (1, "")
    assert err == "toon: invalid TOON: line 1: Declared length 3 but found 2\n"


@pytest.mark.parametrize(
    ("args", "stdin", "message"),
    [
        (["-e"], "{oops", "toon: invalid JSON"),
        (["-e"], '{"s": "\\ud800"}', "unpaired surrogate"),
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


def test_usage_errors(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    for args in (
        ["-e", "-d"],
        ["--check", "-o", "x"],
        ["--delimiter", ";"],
        ["--indent-size", "0"],
    ):
        with pytest.raises(SystemExit) as info:
            run(monkeypatch, capsys, *args)
        assert info.value.code == 2


def test_length_marker_is_ignored(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out, err = run(monkeypatch, capsys, "--length-marker", stdin="[1, 2]")
    assert (code, out) == (0, "[2]: 1,2\n")
    assert "ignored" in err


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


@pytest.mark.parametrize("module", ["toon", "toon_format"])
def test_python_m(module: str) -> None:
    result = subprocess.run(
        [sys.executable, "-W", "ignore", "-m", module, "-e"],
        input="[1, 2]",
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout == "[2]: 1,2\n"
