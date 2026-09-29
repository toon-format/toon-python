# AGENTS.md

Rules for anyone changing this repository, human or coding agent. Read this
before editing; keep it current when a rule changes.

## What this project is

`toon-python` (import name `toon`) is the official Python implementation of
[TOON](https://github.com/toon-format/spec), the Token-Oriented Object Notation.
It is pure Python with no runtime dependencies and mirrors the `json` module:
`dumps`, `dump`, `loads`, `load`, and `ToonDecodeError`.

**Target specification: TOON 4.1**, exposed as `toon.__toon_spec__`. The
conformance fixtures in `tests/fixtures/` are copied from spec tag `v4.1.1`.
The specification is the authority: when this code, its tests, or another
implementation disagree with [SPEC.md](https://github.com/toon-format/spec/blob/main/SPEC.md),
the specification wins.

## Layout

| Path | Contents |
| --- | --- |
| `src/toon/__init__.py` | Public names only; no logic |
| `src/toon/_api.py` | `dumps`/`dump`/`loads`/`load`, option validation, `Delimiter` |
| `src/toon/_encoder.py` | Host-type normalization (§3) and rendering (§8–§10) |
| `src/toon/_decoder.py` | Line splitting (§5.1, §12) and the recursive-descent parser |
| `src/toon/_text.py` | Rules shared by both directions: quoting, escaping, number grammars |
| `src/toon/_errors.py` | `ToonDecodeError` |
| `src/toon/_tokens.py` | Offline token counts with `tiktoken` for `toon stats` and the 0.9 helpers |
| `src/toon/cli.py` | The `toon` command |
| `src/toon/pydantic.py` | Optional Pydantic integration |
| `tests/fixtures/` | Official spec fixtures; never edited by hand |
| `tests/strategies.py` | Hypothesis strategies for JSON-model values |
| `scripts/update_fixtures.py` | Re-vendors the fixtures from a spec tag |
| `packaging/toon-format/` | The `toon-format` distribution, the former name: depends on `toon-python` and carries the deprecated 0.9 API (`toon_format`, thin wrappers over `toon`), its tests, and the `toon` command |
| `scripts/benchmark.py` | Times encoding and decoding, optionally against a git revision |
| `docs/`, `mkdocs.yml` | User documentation, built with MkDocs for Read the Docs (`.readthedocs.yaml`) |

## Environment

The project is managed with [uv](https://docs.astral.sh/uv/).

```bash
uv sync                    # create .venv with the dev dependencies
uv run pytest              # full test suite
uv run pytest -k keyed     # a subset
```

## Checks before proposing a change

All of these must pass; CI runs the same commands on Python 3.10 to 3.14.

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest --cov --cov-fail-under=95
(cd packaging/toon-format && uv run --package toon-format pytest --cov --cov-fail-under=95)
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
  in an optional module (`toon.pydantic`), declared as an extra.
- **Documentation.** User-facing behavior is documented in `docs/`; the API
  reference is generated from docstrings, which use the Google style. Preview
  with `uv run --group docs mkdocs serve`. `README.md` stays short and links to
  the documentation.
- **Public API.** Everything public is re-exported from `toon/__init__.py` and
  listed in `__all__`. Everything else is private (`_module.py`, `_name`). Options
  are keyword-only. Changing the public API requires updating `docs/`,
  `CHANGELOG.md`, and `tests/test_api.py`.
- **Cite the specification.** Comments and docstrings reference the section
  they implement, for example `(§9.5)`. Keep that habit: it is how reviewers
  check behavior.
- **Errors.** Encoding raises `TypeError` for values or keys that cannot be
  represented and `ValueError` for invalid options, cycles, unpaired
  surrogates, or excessive nesting, like `json.dumps`. Decoding raises only
  `ToonDecodeError` for bad input, created through `_Parser.error` so that
  `.line` and `.source` are set. Never replace an unrepresentable value with
  `null` silently.
- **Style.** Lines are at most 88 characters (the reason is in
  `CONTRIBUTING.md`); `ruff format` decides the layout. Small functions,
  early returns, no dead code, no commented-out code, no speculative options.
  Match the surrounding code.

### Encoder invariants

- The form of a value follows from its shape and position, never from a
  preference (§1.4): inline for primitive arrays, tabular when `_shape`
  succeeds, keyed tabular for an object with at least two uniform entries in
  field or root position, list form otherwise.
- A keyless array that is itself a list item never uses a field list (§9.4).
- A list-item object is rendered as fields at `depth + 1` whose first line
  moves onto the hyphen line; this single rule produces the §10 layout for
  every first field, tabular or not.
- Every header declares the document delimiter (§11.1).
- Output has no trailing spaces, no trailing newline, and no comment lines.
- Normalization runs before rendering and yields only `dict`, `list`, `str`,
  `int`, `float` (finite), `Decimal` (finite), `bool`, and `None`.

### Decoder invariants

- Comment lines are removed and blank lines folded into `_Line.blank_before`
  in `_split_lines`, before any structural decision (§5.1, §12). Line numbers
  in errors always refer to the original document.
- `_Parser.classify` implements the line classes of §5.2. A malformed header
  raises `_Malformed`; strict mode turns it into an error, non-strict mode
  falls back to a key-value line with a literal key (§6).
- `strict=False` relaxes only what §14 lists as strict-only: counts and
  widths, blank lines in header spans, indentation, over-indented lines,
  duplicate keys (last write wins, first position kept), malformed headers,
  and trailing content after a root array. Errors marked "any mode" in §14 stay
  errors.
- A declared `[N]` never ends or truncates a scope; it is only compared with
  what the scope contains.
- Numbers follow the §4 grammar in `_text.is_number_token`, never Python's
  `int()`/`float()` grammar, which accepts `1_000`, `+5`, and `inf`.

### Documented choices

The specification requires implementations to document some choices. They
are listed under "Specification choices" in `docs/data-types.md`; change that
section together with the code.

## Tests

- pytest only; parametrize instead of looping; assert on complete output, not
  substrings.
- `test_spec_fixtures.py` runs every official fixture through `dumps`/`dump`
  and `loads`/`load`. A fixture failure is a bug in this package.
- `test_encode.py` and `test_decode.py` cover behavior the fixtures cannot
  express: host types, hooks, errors, non-strict leniency, and regressions
  from the issue tracker (cite the issue number).
- `test_roundtrip.py` checks `loads(dumps(x)) == x` and output invariants with
  Hypothesis.
- `test_toons_compat.py` is a differential test against
  [toons](https://github.com/alesanfra/toons), an independent Rust
  implementation of the same specification version. Both encoders must
  produce the same text, except for the float spellings §2 leaves open (toon
  uses exponents outside [1e-6, 1e21) and exact digits for integral floats
  from 2⁵³) and for strings starting with U+FEFF, which toon quotes because a
  bare one at the root is removed as a byte-order mark (§12); both decoders
  must agree on valid documents and on every decode fixture. On malformed input the two knowingly differ; `toon` follows the
  specification there, never toons:
  - a single line such as `[` or `foo[2]` is a root string (§5, §5.2: without
    a colon it is not a header);
  - inside an array in list form, a line starting with `- ` anywhere but at
    the array's item depth is an error in both modes (§5.2, §10); outside such
    an array the hyphen is ordinary text (`- a: 1` is the key `"- a"`);
  - quoted strings with literal control characters other than tab are
    rejected in strict mode (§7.1 `unescaped-char`);
  - field lists missing a delimiter (`{a{x}b}`) are malformed (§6 `fields-seg`).

  When the two disagree on anything else, find out which one is wrong before
  changing either.
- Every bug fix comes with a test that fails without it.

## Specification updates

1. Run `uv run scripts/update_fixtures.py vX.Y.Z` and read the spec changelog.
2. Implement the changes, citing the new sections.
3. Update `__toon_spec__`, the README badge, `docs/data-types.md`, this file,
   and `CHANGELOG.md`.
4. Bump `toons` in the dev dependencies once it supports the same version.

## Commits and releases

- Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`,
  `ci:`, `chore:`); add `!` for breaking changes.
- Every user-visible change gets a line under *Unreleased* in `CHANGELOG.md`.
- Publishing happens only through the `Publish` workflow
  (`.github/workflows/publish.yml`), with PyPI trusted publishing. PyPI binds
  the publisher to that file name and to the `pypi` and `testpypi`
  environments: do not rename them. The same jobs publish `toon-python`
  and then `toon-format`; both PyPI projects need the trusted publisher.

To release:

1. `uv version --bump minor` (or `patch`, `major`, or an explicit version),
   and move the *Unreleased* entries of `CHANGELOG.md` under the new version.
   Run `uv version --package toon-format` with the same version and update the
   three `toon-python==` pins in `packaging/toon-format/pyproject.toml`; the
   workflow checks them.
2. Merge that change through a pull request.
3. Optional: run the `Publish` workflow by hand to upload to TestPyPI.
4. Create a GitHub release tagged `vX.Y.Z`. The workflow checks that the tag
   matches the version, runs the tests, builds, and uploads to PyPI.

The documentation is meant to live at <https://toon-python.readthedocs.io>,
built by Read the Docs from `.readthedocs.yaml`. That project does not exist
yet: import the repository on readthedocs.org with the slug `toon-python`, then
remove the "not published yet" note from `README.md`.
