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
- The `toon` module with a `json`-style interface: `dumps`, `dump`, `loads`, `load`.
- `default` and `sort_keys` options for encoding; `parse_float`, `parse_int`,
  `object_hook`, and `object_pairs_hook` for decoding.
- Encoding of dataclasses, attrs classes, enums, UUIDs, sets, `Decimal` (lossless), and Pydantic models.
- Decoding from `bytes` and binary files.
- `ToonDecodeError.line`, `.source`, and `.msg`.
- `toon.Delimiter` and `toon.__toon_spec__`.
- CLI subcommands `toon encode`, `toon decode`, `toon check` (validates
  several files and reports `file:line: message`), and `toon stats` (token
  counts of JSON and of TOON with each delimiter, with `tiktoken`, exact for
  OpenAI models only), and `python -m toon`. `toon FILE` keeps the 0.9
  interface.
- Documentation site built with MkDocs for Read the Docs.
- Differential tests against the independent [toons](https://github.com/alesanfra/toons)
  implementation and property-based round-trip tests.

### Changed

- The distribution is now `toon-python` and the import name `toon`. The
  `toon-format` distribution remains as its former name: it depends on
  `toon-python` and carries the deprecated `toon_format` module.
- Unsupported values raise `TypeError` instead of becoming `null`.
- Python 3.10 or later is required.

### Removed

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
