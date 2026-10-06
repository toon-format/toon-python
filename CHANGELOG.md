# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed

- Support for [TOON specification 4.2](https://github.com/toon-format/spec/blob/v4.2.1/SPEC.md):
  all official fixtures of spec `v4.2.1` pass, and `toon_format.__toon_spec__`
  is `"4.2"`. A string starting with U+FEFF is quoted only as a root
  primitive.
- Decoding settles the edge cases that 4.1 left open: quoted strings accept raw
  control characters in strict mode, a leading hyphen marks a list item only at
  item depth, a line whose only colons sit in the bracket segment or its field
  list is a key-value line, a quote span inside a field name hides braces and
  delimiters, whitespace before a nested field group is a header error, a
  tab-only line is a tab-indentation error in strict mode instead of a blank
  line, and an indented first line is over-indented.
- With `strict=False`, a jumped first line sets the depth of its scope,
  over-indented lines inside arrays are skipped instead of ending them, and a
  scalar line after a root array is an error.

## [1.0.0]

A complete rewrite. See [docs/migration.md](docs/migration.md) for upgrading
from 0.9.

### Added

- Full support for [TOON specification 4.1](https://github.com/toon-format/spec/blob/v4.1.2/SPEC.md):
  keyed tabular objects, nested field groups, comment lines, canonical empty
  arrays, and every strict-mode check. All official fixtures of spec `v4.1.2` pass.
- A `json`-style interface: `dumps`, `dump`, `loads`, `load`, with keyword-only
  options. `encode` and `decode` are aliases of `dumps` and `loads`.
- `default` and `sort_keys` options for encoding; `parse_float`, `parse_int`,
  `object_hook`, and `object_pairs_hook` for decoding.
- Encoding of dataclasses, attrs classes, enums, UUIDs, sets, `Decimal` (lossless), and Pydantic models.
- Decoding from `bytes` and binary files.
- `ToonDecodeError.line`, `.source`, and `.msg`.
- `toon_format.Delimiter` and `toon_format.__toon_spec__`.
- Documentation site built with MkDocs for Read the Docs.
- Property-based round-trip tests.

### Changed

- `encode` and `decode` take options as keyword arguments instead of a
  dictionary.
- Unsupported values raise `TypeError` instead of becoming `null`.
- Python 3.10 or later is required.

### Removed

- The options types `EncodeOptions`, `DecodeOptions`, and `DelimiterKey`.
- The token helpers `count_tokens`, `estimate_savings`, and `compare_formats`.
- The `toon` command and `python -m toon_format`; use
  [`@toon-format/cli`](https://www.npmjs.com/package/@toon-format/cli).
- Length markers (`[#N]`), removed from the specification.

### Fixed

- Nested objects inside list items (#33), nested length mismatches (#47), the
  empty root array (#61), arrays of arrays (#62), empty objects as the first
  field of a list item (#63), empty-string keys (#64), quoting of non-ASCII
  keys (#65), negative array lengths, and CRLF input.

## [0.9.0-beta.1] - 2025-11-08

First public beta, implementing TOON specification 1.3.

[Unreleased]: https://github.com/toon-format/toon-python/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/toon-format/toon-python/releases/tag/v1.0.0
[0.9.0-beta.1]: https://github.com/toon-format/toon-python/releases/tag/v0.9.0-beta.1
