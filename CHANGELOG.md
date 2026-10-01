# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.0.0]

A complete rewrite. See [docs/migration.md](docs/migration.md) for upgrading
from 0.9.

### Added

- Full support for [TOON specification 4.1](https://github.com/toon-format/spec/blob/v4.1.1/SPEC.md):
  keyed tabular objects, nested field groups, comment lines, canonical empty
  arrays, and every strict-mode check. All official fixtures of spec `v4.1.1` pass.
- A `json`-style interface: `dumps`, `dump`, `loads`, `load`, with keyword-only
  options. `encode` and `decode` are aliases of `dumps` and `loads`.
- `default` and `sort_keys` options for encoding; `parse_float`, `parse_int`,
  `object_hook`, and `object_pairs_hook` for decoding.
- Encoding of dataclasses, attrs classes, enums, UUIDs, sets, `Decimal` (lossless), and Pydantic models.
- Decoding from `bytes` and binary files.
- `ToonDecodeError.line`, `.source`, and `.msg`.
- `toon_format.Delimiter` and `toon_format.__toon_spec__`.
- The `toon-python` distribution, an alias with no code that installs
  `toon-format`.
- Documentation site built with MkDocs for Read the Docs.
- Differential tests against [toons](https://github.com/alesanfra/toons), a
  Rust implementation of the same specification, and property-based
  round-trip tests.

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
