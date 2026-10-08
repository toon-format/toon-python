# AGENTS.md

Rules for anyone changing this repository, human or coding agent. Read this
before editing; keep it current when a rule changes.

## What this project is

`toon-format` (import name `toon_format`) is the official Python
implementation of [TOON](https://github.com/toon-format/spec), the
Token-Oriented Object Notation. It is pure Python with no runtime dependencies
and mirrors the `json` module: `dumps`, `dump`, `loads`, `load`, and
`ToonDecodeError`, with `encode` and `decode` as aliases of `dumps` and
`loads`, the names the other TOON implementations use.

**Target specification: TOON 4.4**, exposed as `toon_format.__toon_spec__`.
The conformance fixtures in `tests/fixtures/` are copied from the spec
repository and never edited by hand. The specification is the authority: when
this code, its tests, or another implementation disagree with
[SPEC.md](https://github.com/toon-format/spec/blob/main/SPEC.md), the
specification wins.

## Environment

The project is managed with [uv](https://docs.astral.sh/uv/).

```bash
uv sync                    # create .venv with the dev dependencies
uv run pytest              # full test suite
uv run pytest -k keyed     # a subset
uv run prek install        # install the Git hooks
```

[prek](https://github.com/j178/prek) reads `.pre-commit-config.yaml`: before
each commit it runs `ruff check --fix`, `ruff format`, `mypy`, and
`mkdocs build --strict`. `uv run prek run --all-files` runs these hooks on the
whole repository, and `uv run prek run --all-files --hook-stage manual` runs
every check below, tests included.

## Checks before proposing a change

All of these must pass; CI runs the same commands on Python 3.10 to 3.14.

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest --cov --cov-fail-under=95
uv run --group docs mkdocs build --strict
```

Set `HYPOTHESIS_PROFILE=ci` to run the property tests with more examples, as CI does.

## Code rules

- **Language.** Code, comments, docstrings, commit messages, and documentation
  are written in American English.
- **Python 3.10+.** Use modern syntax (`X | Y`, built-in generics, `from
  __future__ import annotations`). Every module starts with a docstring.
- **Typing.** `mypy --strict` must pass. Avoid `Any` in new signatures unless
  the value is genuinely arbitrary (user data, hook results).
- **No runtime dependencies.** Integrations import their library lazily or live
  in an optional module (`toon_format.pydantic`), declared as an extra.
- **Documentation.** User-facing behavior is documented in `docs/`; the API
  reference is generated from docstrings, which use the Google style. Preview
  with `uv run --group docs mkdocs serve`. `README.md` stays short and links to
  the documentation.
- **Public API.** Everything public is re-exported from `toon_format/__init__.py` and
  listed in `__all__`. Everything else is private (`_module.py`, `_name`). Options
  are keyword-only. Changing the public API requires updating `docs/`,
  `CHANGELOG.md`, and its tests.
- **Cite the specification.** Comments and docstrings reference the section
  they implement, for example `(§9.5)`. Keep that habit: it is how reviewers
  check behavior.
- **Errors.** Encoding raises `TypeError` for values or keys that cannot be
  represented and `ValueError` for invalid options, cycles, unpaired
  surrogates, or excessive nesting, like `json.dumps`. Decoding raises only
  `ToonDecodeError` for bad input, with `.line` and `.source` set. Never
  replace an unrepresentable value with `null` silently.
- **Style.** Lines are at most 88 characters (the reason is in
  `CONTRIBUTING.md`); `ruff format` decides the layout. Small functions,
  early returns, no dead code, no commented-out code, no speculative options.
  Match the surrounding code.

### Encoder invariants

- The form of a value follows from its shape and position, never from a
  preference (§1.4): inline for primitive arrays, tabular for uniform objects,
  keyed tabular for an object with at least two uniform entries in field or
  root position, list form otherwise.
- A keyless array that is itself a list item never uses a field list (§9.4).
- A list-item object is rendered as fields one level deeper whose first line
  moves onto the hyphen line; this single rule produces the §10 layout for
  every first field, tabular or not.
- Every header declares the document delimiter (§11.1).
- Output has no trailing spaces, no trailing newline, and no comment lines.
- Normalization runs before rendering and yields only `dict`, `list`, `str`,
  `int`, `float` (finite), `Decimal` (finite), `bool`, and `None`.

### Decoder invariants

- Comment lines and blank lines are handled while splitting lines, before any
  structural decision (§5.1, §12). Line numbers in errors always refer to the
  original document.
- Line classification follows §5.2. A malformed header is an error in both
  modes (§6).
- Whitespace is space and tab only (§1.2): never decide syntax with
  `str.isspace()`, an argument-less `strip()`, or `\s`.
- `strict=False` applies exactly the five recoveries of §14.4: counts are
  advisory, duplicate keys and repeated field names resolve last-write-wins
  (first position kept), indentation depth is tabs plus floored spaces, blank
  lines in header spans are ignored, and a jumped first line sets its scope's
  depth. Every other §14 condition is an error in both modes.
- A declared `[N]` never ends or truncates a scope; it is only compared with
  what the scope contains.
- Numbers follow the §4 grammar, never Python's `int()`/`float()` grammar,
  which accepts `1_000`, `+5`, and `inf`.

### Documented choices

The specification requires implementations to document some choices. They
are listed under "Specification choices" in `docs/data-types.md`; change that
section together with the code.

## Tests

- pytest only; parametrize instead of looping; assert on complete output, not
  substrings.
- Every official fixture runs through `dumps`/`dump` and `loads`/`load`. A
  fixture failure is a bug in this package.
- Other tests cover what the fixtures cannot express: host types, hooks,
  errors, non-strict leniency, and regressions from the issue tracker (cite
  the issue number). Hypothesis checks `loads(dumps(x)) == x`.
- Every bug fix comes with a test that fails without it.

## Specification updates

1. Run `uv run scripts/update_fixtures.py vX.Y.Z` and read the spec changelog.
2. Implement the changes, citing the new sections.
3. Update `__toon_spec__`, the README badge, `docs/data-types.md`, this file,
   and `CHANGELOG.md`.

## Commits

- Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`,
  `ci:`, `chore:`); add `!` for breaking changes.
- Every user-visible change gets a line under *Unreleased* in `CHANGELOG.md`.
- Releases follow `CONTRIBUTING.md`.
