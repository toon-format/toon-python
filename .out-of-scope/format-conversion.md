# Conversion to Other Formats

This package converts between Python values and TOON, and nothing else. It does not read or write CSV, YAML, or XML, and does not batch-convert files.

## Why this is out of scope

TOON carries the JSON data model (§2), so any other format reaches it through a parser that already yields dicts and lists – `json`, `csv`, or a mature YAML or XML library. A converter here would duplicate those parsers and turn every edge case of their formats into a bug report against this package. As Johann put it on the CSV pull request: "this is completely out of scope for the TOON Python package. There are numerous battle-tested CSV parsers available" ([#39](https://github.com/toon-format/toon-python/pull/39#issuecomment-3539108955)).

The `toon` command follows the same line and converts between JSON and TOON only.

## Prior requests

- [#25](https://github.com/toon-format/toon-python/issues/25) / [#35](https://github.com/toon-format/toon-python/pull/35) – "batch processing": conversion between JSON, YAML, XML, CSV, and TOON
- [#38](https://github.com/toon-format/toon-python/discussions/38) – "TOON to CSV python lib": merging `tooncsv` into this package
- [#39](https://github.com/toon-format/toon-python/pull/39) – "Add CSV Parsing & Writing Support to toon_format"
