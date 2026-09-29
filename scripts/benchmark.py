"""Time encoding and decoding, optionally against another git revision.

Usage:
    uv run scripts/benchmark.py              # the working tree only
    uv run scripts/benchmark.py main         # the working tree against main
    uv run scripts/benchmark.py v0.9.0-beta.1

The revision is checked out in a temporary git worktree and imported from its
``src`` directory: ``toon.dumps``/``toon.loads`` when it has the ``toon``
module, the 0.9 ``toon_format.encode``/``toon_format.decode`` otherwise. Each
figure is the best of five runs. The datasets avoid forms that 0.9 cannot
write, such as keyed tabular objects, so that both sides encode the same text.
"""

from __future__ import annotations

import importlib
import json
import os
import random
import subprocess
import sys
import tempfile
import timeit
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
WORDS = ["alpha", "beta", "gamma", "hello world", "x:y", "42", "true", "é ü"]


def _datasets() -> dict[str, tuple[Any, int]]:
    """Return each dataset with the number of calls per timing run."""
    rng = random.Random(42)

    def user(i: int) -> dict[str, Any]:
        return {
            "id": i,
            "name": f"user{i}",
            "email": f"u{i}@example.com",
            "active": i % 2 == 0,
            "score": round(rng.random() * 100, 3),
            "role": rng.choice(WORDS),
        }

    def node(depth: int) -> dict[str, Any]:
        if depth == 0:
            return {"k": rng.choice(WORDS), "v": rng.randint(0, 999), "f": rng.random()}
        children: dict[str, Any] = {f"child{j}": node(depth - 1) for j in range(3)}
        return children | {"tags": ["a", "b", "c"]}

    def mixed(i: int) -> dict[str, Any]:
        item: dict[str, Any] = {"id": i, "kind": rng.choice(["a", "b"])}
        if i % 3 == 0:
            item["meta"] = {"x": i, "y": [1, 2, 3]}
        elif i % 3 == 1:
            item["items"] = [{"n": j, "s": "s"} for j in range(3)]
        return item

    numbers = {f"a{i}": [rng.randint(0, 10**6) for _ in range(50)] for i in range(200)}
    small = {"name": "Ada", "age": 36, "tags": ["math", "code"], "ok": True}
    return {
        "tabular, 1000 rows": ({"users": [user(i) for i in range(1000)]}, 20),
        "nested, depth 6": (node(6), 20),
        "mixed list, 1000 items": ({"items": [mixed(i) for i in range(1000)]}, 20),
        "200 number arrays": (numbers, 20),
        "small object": (small, 10000),
    }


def _best(call: Callable[[], object], number: int) -> float:
    return min(timeit.repeat(call, number=number, repeat=5)) / number


def _measure(src: Path) -> dict[str, dict[str, float]]:
    """Time the implementation in ``src`` inside this process."""
    if (src / "toon").is_dir():
        module = importlib.import_module("toon")
        dumps, loads = module.dumps, module.loads
    else:
        module = importlib.import_module("toon_format")
        dumps, loads = module.encode, module.decode
    # The installed package must not shadow the revision under test.
    assert Path(module.__file__ or "").is_relative_to(src), module.__file__
    results = {}
    for name, (data, number) in _datasets().items():
        text = dumps(data)
        assert loads(text) == data, name
        results[name] = {
            "encode": _best(lambda: dumps(data), number),  # noqa: B023
            "decode": _best(lambda: loads(text), number),  # noqa: B023
        }
    return results


def _run(src: Path) -> dict[str, dict[str, float]]:
    """Time the implementation in ``src`` in a fresh interpreter."""
    env = {**os.environ, "PYTHONPATH": str(src)}
    command = [sys.executable, __file__, "--measure", str(src)]
    output = subprocess.run(command, env=env, check=True, capture_output=True)
    result: dict[str, dict[str, float]] = json.loads(output.stdout)
    return result


def _milliseconds(seconds: float) -> str:
    return f"{seconds * 1000:.3f} ms"


def main(revision: str | None) -> None:
    current = _run(ROOT / "src")
    if revision is None:
        print(f"{'':24} {'encode':>12} {'decode':>12}")
        for name, times in current.items():
            encode, decode = (
                _milliseconds(times["encode"]),
                _milliseconds(times["decode"]),
            )
            print(f"{name:24} {encode:>12} {decode:>12}")
        return
    with tempfile.TemporaryDirectory() as directory:
        tree = Path(directory) / "tree"
        git = ["git", "-C", str(ROOT), "worktree"]
        add = [*git, "add", "--quiet", "--detach", str(tree), revision]
        subprocess.run(add, check=True)
        try:
            other = _run(tree / "src")
        finally:
            subprocess.run([*git, "remove", "--force", str(tree)], check=True)
    print(f"{'':31} {revision:>12} {'working tree':>12} {'speedup':>8}")
    for name, times in current.items():
        for operation in ("encode", "decode"):
            before, after = other[name][operation], times[operation]
            print(
                f"{name:24} {operation:6} {_milliseconds(before):>12}"
                f" {_milliseconds(after):>12} {before / after:7.2f}x"
            )


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--measure":
        print(json.dumps(_measure(Path(sys.argv[2]))))
    elif len(sys.argv) <= 2:
        main(sys.argv[1] if len(sys.argv) == 2 else None)
    else:
        sys.exit(__doc__)
