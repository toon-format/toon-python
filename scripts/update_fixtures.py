# /// script
# requires-python = ">=3.10"
# ///
"""Replace tests/fixtures with the conformance fixtures of a TOON specification release.

Usage: uv run scripts/update_fixtures.py v4.1.2
"""

from __future__ import annotations

import io
import shutil
import sys
import tarfile
import urllib.request
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent.parent / "tests" / "fixtures"
ARCHIVE = "https://github.com/toon-format/spec/archive/refs/tags/{tag}.tar.gz"


def main(tag: str) -> None:
    with urllib.request.urlopen(ARCHIVE.format(tag=tag)) as response:
        data = response.read()
    for category in ("encode", "decode"):
        shutil.rmtree(FIXTURES / category, ignore_errors=True)
    count = 0
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        for member in archive.getmembers():
            parts = Path(member.name).parts
            if member.isfile() and parts[1:4] in (
                ("tests", "fixtures", "encode"),
                ("tests", "fixtures", "decode"),
            ):
                source = archive.extractfile(member)
                assert source is not None
                target = FIXTURES.joinpath(*parts[3:])
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read())
                count += 1
    readme = FIXTURES / "README.md"
    text = readme.read_text(encoding="utf-8")
    start = text.index("at tag `") + len("at tag `")
    readme.write_text(
        text[:start] + tag + text[text.index("`", start) :], encoding="utf-8"
    )
    print(f"Copied {count} fixture files from {tag}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
