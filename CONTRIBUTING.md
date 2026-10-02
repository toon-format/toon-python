# Contributing to toon-python

Thank you for helping with the official Python implementation of TOON.

1. Install [uv](https://docs.astral.sh/uv/) and run `uv sync`, then
   `uv run prek install` to lint, format, type-check, and build the
   documentation before each commit. Alternatively, open the repository in
   the [dev container](https://containers.dev/)
   (`.devcontainer/devcontainer.json`, also used by GitHub Codespaces), which
   comes with uv, every dependency, and the Git hooks installed.
2. Read [AGENTS.md](AGENTS.md): it describes the code rules and the checks
   every change must pass.
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

## Releases

Publishing happens only through the `Publish` workflow
(`.github/workflows/publish.yml`), with PyPI trusted publishing. PyPI binds
the publisher to that file name and to the `pypi` and `testpypi`
environments: do not rename them.

1. `uv version --bump minor` (or `patch`, `major`, or an explicit version),
   and move the *Unreleased* entries of `CHANGELOG.md` under the new version.
2. Merge that change through a pull request.
3. Optional: run the `Publish` workflow by hand to upload to TestPyPI.
4. Create a GitHub release tagged `vX.Y.Z`. The workflow checks that the tag
   matches the version, runs the tests, builds, and uploads to PyPI.

The documentation is meant to live at <https://toon-python.readthedocs.io>,
built by Read the Docs from `.readthedocs.yaml`. That project does not exist
yet: import the repository on readthedocs.org with the slug `toon-python`, then
point the "Documentation" section of `README.md` and the `Documentation` URL in
`pyproject.toml` to it, and add a Read the Docs badge next to the others.
