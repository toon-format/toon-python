# Contributing to toon-python

Thank you for helping with the official Python implementation of TOON.

1. Install [uv](https://docs.astral.sh/uv/) and run `uv sync`. Alternatively,
   open the repository in the [dev container](https://containers.dev/)
   (`.devcontainer/devcontainer.json`, also used by GitHub Codespaces), which
   comes with uv and every dependency installed.
2. Read [AGENTS.md](AGENTS.md): it describes the layout, the code rules, and
   the checks every change must pass.
3. For behavior changes, start from the [specification](https://github.com/toon-format/spec/blob/main/SPEC.md)
   and cite the section you implement. Questions about the format itself
   belong in the [spec repository](https://github.com/toon-format/spec).
4. Add tests, update `CHANGELOG.md`, and open a pull request with a
   Conventional Commits title (`fix: ...`, `feat: ...`).

```bash
uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest
```

## Code style

`ruff format` formats the code and `ruff check` lints it; CI runs both.

Lines are limited to **88 characters**, the default of ruff and Black. It is
the de facto standard of the Python ecosystem: FastAPI, Flask, Django, HTTPX,
Requests, pytest, and pandas all use it. PEP 8's 79 characters wrap ordinary
code too often, and a longer limit would diverge from the projects most
contributors already know. The value is set explicitly in `pyproject.toml` so
that nobody has to know the default.
